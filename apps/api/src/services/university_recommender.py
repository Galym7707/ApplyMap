import json
from typing import Any

import httpx

from ..config import settings
from ..models.achievement import Achievement


RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "recommendations": {
            "type": "array",
            "maxItems": 20,
            "items": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "category": {"type": "string", "enum": ["dream", "target", "safe"]},
                    "rationale": {"type": "string"},
                    "fit_notes": {"type": "string"},
                },
                "required": ["slug", "category", "rationale"],
            },
        },
    },
    "required": ["recommendations"],
}


def _achievement_payload(achievement: Achievement) -> dict[str, Any]:
    scores = [
        achievement.major_relevance_score,
        achievement.selectivity_score,
        achievement.continuity_score,
        achievement.distinctiveness_score,
    ]
    numeric_scores = [score for score in scores if isinstance(score, (int, float))]
    return {
        "id": str(achievement.id),
        "type": achievement.type.value,
        "title": achievement.title,
        "organization_name": achievement.organization_name,
        "role_title": achievement.role_title,
        "description_raw": achievement.description_raw,
        "category": achievement.category,
        "impact_scope": getattr(achievement.impact_scope, "value", achievement.impact_scope),
        "leadership_level": getattr(achievement.leadership_level, "value", achievement.leadership_level),
        "hours_per_week": achievement.hours_per_week,
        "weeks_per_year": achievement.weeks_per_year,
        "chancellor_score_average": round(sum(numeric_scores) / len(numeric_scores), 1) if numeric_scores else None,
    }


def _prompt(
    *,
    selected_honors: list[Achievement],
    selected_activities: list[Achievement],
    preferences: dict[str, Any],
    universities: list[dict[str, Any]],
) -> str:
    payload = {
        "student_preferences": preferences,
        "selected_top_honors": [_achievement_payload(item) for item in selected_honors],
        "selected_top_activities": [_achievement_payload(item) for item in selected_activities],
        "allowed_common_app_universities": [
            {
                "slug": item["slug"],
                "name": item["name"],
                "country": item["country"],
                "major_strengths": item.get("major_strengths"),
                "aid_type": item.get("aid_type"),
                "aid_strength": item.get("aid_strength"),
                "selectivity_score": item.get("selectivity_score"),
                "education_years_required": item.get("education_years_required"),
                "school_years_note": item.get("school_years_note"),
                "aid_notes": item.get("aid_notes"),
            }
            for item in universities
        ],
    }
    return (
        "You are SourceLock Chancellor. Recommend up to 20 Common App universities using only the selected "
        "top 5 honors, selected top 10 activities, and saved student preferences in the input JSON. "
        "Do not use unselected achievements. Do not recommend universities outside allowed_common_app_universities.\n\n"
        "Categorize results as dream, target, or safe. For a high-need international applicant, safe means "
        "relative safety within this funded/Common App shortlist, not guaranteed admission or aid. Prefer about "
        "4 dream, 10 target, and 6 safe when enough universities are available.\n\n"
        "Consider intended major, preferred countries/regions, school years, teaching language, full-ride need, "
        "aid route quality, and selectivity. Return JSON only.\n\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False, default=str)}"
    )


def _extract_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    content = candidates[0].get("content") if candidates else {}
    parts = content.get("parts") or []
    return str(parts[0].get("text", "")) if parts else ""


def _gemini_recommendations(
    *,
    selected_honors: list[Achievement],
    selected_activities: list[Achievement],
    preferences: dict[str, Any],
    universities: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        return None

    model = (settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request_payload = {
        "contents": [{"parts": [{"text": _prompt(
            selected_honors=selected_honors,
            selected_activities=selected_activities,
            preferences=preferences,
            universities=universities,
        )}]}],
        "generationConfig": {
            "temperature": 0.15,
            "responseMimeType": "application/json",
            "responseJsonSchema": RECOMMENDATION_SCHEMA,
        },
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                url,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=request_payload,
            )
            response.raise_for_status()
        payload = json.loads(_extract_text(response.json()))
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None

    allowed_by_slug = {item["slug"]: item for item in universities}
    results = []
    for rec in payload.get("recommendations", []):
        slug = rec.get("slug")
        if slug not in allowed_by_slug:
            continue
        university = allowed_by_slug[slug]
        category = rec.get("category") if rec.get("category") in {"dream", "target", "safe"} else "target"
        results.append(_merge_recommendation(university, category, rec.get("rationale") or "", rec.get("fit_notes")))
        if len(results) == 20:
            break
    return results or None


def _merge_recommendation(university: dict[str, Any], category: str, rationale: str, fit_notes: str | None) -> dict[str, Any]:
    return {
        "university_id": university["id"],
        "slug": university["slug"],
        "name": university["name"],
        "country": university["country"],
        "category": category,
        "rationale": rationale,
        "fit_notes": fit_notes,
        "aid_notes": university.get("aid_notes"),
        "funding_source_url": university.get("funding_source_url"),
    }


def _score_university(university: dict[str, Any], preferences: dict[str, Any], achievement_text: str) -> float:
    score = float(university.get("aid_strength") or 0)
    major = str(preferences.get("intended_major") or preferences.get("major") or "").lower()
    preferred_countries = [str(item).lower() for item in preferences.get("preferred_countries", []) if item]
    preferred_regions = [str(item).lower() for item in preferences.get("preferred_regions", []) if item]
    teaching_language = str(preferences.get("teaching_language") or "").lower()
    school_years = preferences.get("school_years")

    strengths = " ".join(university.get("major_strengths") or []).lower()
    if major and any(term in strengths for term in major.replace("/", " ").split() if len(term) > 2):
        score += 18
    if preferred_countries and university["country"].lower() in preferred_countries:
        score += 10
    if preferred_regions and str(university.get("region") or "").lower() in preferred_regions:
        score += 8
    if teaching_language and teaching_language in [language.lower() for language in university.get("teaching_languages") or []]:
        score += 5
    if preferences.get("needs_full_ride") and university.get("full_ride_possible"):
        score += 12
    if school_years and university.get("education_years_required") and int(school_years) < int(university["education_years_required"]):
        score -= 40
    if "research" in achievement_text and university.get("weight_preset") == "research_heavy":
        score += 6
    return score


def _fallback_recommendations(
    *,
    selected_honors: list[Achievement],
    selected_activities: list[Achievement],
    preferences: dict[str, Any],
    universities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    achievement_text = " ".join(
        f"{item.title} {item.description_raw or ''} {item.category or ''}"
        for item in [*selected_honors, *selected_activities]
    ).lower()
    ranked = sorted(
        universities,
        key=lambda item: (
            _score_university(item, preferences, achievement_text),
            -(item.get("selectivity_score") or 0),
        ),
        reverse=True,
    )[:20]

    results = []
    for index, university in enumerate(ranked):
        if index < 4:
            category = "dream"
        elif index < 14:
            category = "target"
        else:
            category = "safe"
        rationale = "Heuristic fallback based on major fit, funding route, school-year compatibility, and selected achievements."
        results.append(_merge_recommendation(university, category, rationale, university.get("eligibility_notes")))
    return results


def recommend_common_app_universities(
    *,
    selected_honors: list[Achievement],
    selected_activities: list[Achievement],
    preferences: dict[str, Any],
    universities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    gemini_results = _gemini_recommendations(
        selected_honors=selected_honors,
        selected_activities=selected_activities,
        preferences=preferences,
        universities=universities,
    )
    return gemini_results or _fallback_recommendations(
        selected_honors=selected_honors,
        selected_activities=selected_activities,
        preferences=preferences,
        universities=universities,
    )
