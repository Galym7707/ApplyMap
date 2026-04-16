import json
from typing import Any
from urllib.parse import urlparse

import httpx

from ..config import settings
from .chancellor_analysis import ADMISSIONS_FRAMEWORK
from .counselor_knowledge import CHANCELLOR_COUNSELOR_FRAMEWORK


ADVISOR_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "exams_to_prioritize": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "exam": {"type": "string"},
                    "why": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["exam", "why", "priority"],
            },
        },
        "profile_actions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "low_value_activities": {
            "type": "array",
            "items": {"type": "string"},
        },
        "research_or_summer_programs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "why_it_helps": {"type": "string"},
                    "source_url": {"type": "string"},
                },
                "required": ["name", "why_it_helps"],
            },
        },
        "source_notes": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "summary",
        "exams_to_prioritize",
        "profile_actions",
        "low_value_activities",
        "research_or_summer_programs",
        "source_notes",
    ],
}


class SearchNotConfiguredError(RuntimeError):
    pass


def _google_search(query: str, *, num: int = 5) -> list[dict[str, str]]:
    api_key = settings.GOOGLE_SEARCH_API_KEY.strip()
    engine_id = settings.GOOGLE_SEARCH_ENGINE_ID.strip()
    if not api_key or not engine_id:
        raise SearchNotConfiguredError("Google Custom Search is not configured")

    with httpx.Client(timeout=12.0) as client:
        response = client.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": api_key,
                "cx": engine_id,
                "q": query,
                "num": num,
                "safe": "active",
                "hl": "en",
            },
        )
        response.raise_for_status()

    items = response.json().get("items") or []
    return [
        {
            "title": str(item.get("title") or ""),
            "url": str(item.get("link") or ""),
            "snippet": str(item.get("snippet") or ""),
        }
        for item in items
        if item.get("link")
    ]


def _source_tier(url: str, university_name: str) -> str:
    host = urlparse(url).netloc.lower()
    name_tokens = [token for token in university_name.lower().replace("-", " ").split() if len(token) > 3]
    has_name_token = any(token in host for token in name_tokens)
    if has_name_token and (".edu" in host or ".ac." in host or host.endswith(".edu")):
        return "official"
    if has_name_token:
        return "likely_official"
    if ".edu" in host or ".ac." in host:
        return "education_domain"
    return "third_party"


def search_university_sources(university_name: str, intended_major: str | None = None) -> list[dict[str, str]]:
    major = intended_major or "undergraduate"
    queries = [
        f"{university_name} official undergraduate admissions international students requirements",
        f"{university_name} official scholarships financial aid international students",
        f"{university_name} official English taught programs {major}",
        f"{university_name} official research summer programs high school students {major}",
    ]

    seen: set[str] = set()
    results: list[dict[str, str]] = []
    for query in queries:
        for item in _google_search(query, num=5):
            url = item["url"]
            if url in seen:
                continue
            seen.add(url)
            results.append(
                {
                    **item,
                    "query": query,
                    "source_tier": _source_tier(url, university_name),
                }
            )
            if len(results) >= 12:
                return results
    return results


def _profile_payload(user: Any) -> dict[str, Any]:
    profile = getattr(user, "profile", None)
    return {
        "country": getattr(user, "country", None),
        "graduation_year": getattr(profile, "graduation_year", None),
        "curriculum": getattr(profile, "curriculum", None),
        "intended_major": getattr(profile, "intended_major", None),
        "sat_score": getattr(profile, "sat_score", None),
        "sat_math": getattr(profile, "sat_math", None),
        "sat_ebrw": getattr(profile, "sat_ebrw", None),
        "act_score": getattr(profile, "act_score", None),
        "ielts_score": getattr(profile, "ielts_score", None),
        "toefl_score": getattr(profile, "toefl_score", None),
        "duolingo_score": getattr(profile, "duolingo_score", None),
        "a_level_subjects": getattr(profile, "a_level_subjects", None),
        "ib_predicted_score": getattr(profile, "ib_predicted_score", None),
        "unt_score": getattr(profile, "unt_score", None),
        "nis_grade12_certificate_gpa": getattr(profile, "nis_grade12_certificate_gpa", None),
    }


def _achievement_payload(achievements: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "type": getattr(item.type, "value", item.type),
            "title": item.title,
            "organization_name": item.organization_name,
            "role_title": item.role_title,
            "description_raw": item.description_raw,
            "category": item.category,
            "impact_scope": getattr(item.impact_scope, "value", item.impact_scope),
            "leadership_level": getattr(item.leadership_level, "value", item.leadership_level),
            "major_relevance_score": item.major_relevance_score,
            "selectivity_score": item.selectivity_score,
            "continuity_score": item.continuity_score,
            "distinctiveness_score": item.distinctiveness_score,
        }
        for item in achievements
    ]


def _prompt(
    *,
    university_name: str,
    user: Any,
    achievements: list[Any],
    search_results: list[dict[str, str]],
) -> str:
    payload = {
        "target_university": university_name,
        "student_profile": _profile_payload(user),
        "student_achievements": _achievement_payload(achievements),
        "google_search_results": search_results,
    }
    return (
        "You are ApplyMap Chancellor. Give a concise, factual action plan for one target university. "
        "Use only the student profile, achievements, and the supplied Google Custom Search results. "
        "Do not invent admission requirements, scores, deadlines, program names, or scholarships. "
        "If a fact is not supported by a source result, write that it cannot be confirmed from the current sources.\n\n"
        "Kazakhstan context: interpret UNT/ENT, NIS Grade 12 Certificate, NIS school context, IB, A-levels, "
        "and 11 vs 12 years of schooling as important fit factors. MESK in Russian/Kazakh user language maps "
        "to NIS Grade 12 Certificate in English.\n\n"
        f"{ADMISSIONS_FRAMEWORK}\n\n"
        f"{CHANCELLOR_COUNSELOR_FRAMEWORK}\n\n"
        "Be direct. Avoid motivational filler. Identify exams that could materially improve the application, "
        "activities that are low-value for this target, and research or summer programs only when they appear "
        "in the supplied source results. If google_search_results is empty, say current university facts cannot "
        "be confirmed and give only general next steps that do not depend on current requirements. Return JSON only.\n\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False, default=str)}"
    )


def _extract_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    content = candidates[0].get("content") if candidates else {}
    parts = content.get("parts") or []
    return str(parts[0].get("text", "")) if parts else ""


def generate_university_action_plan(
    *,
    university_name: str,
    user: Any,
    achievements: list[Any],
    search_results: list[dict[str, str]],
) -> dict[str, Any]:
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        return {
            "summary": "Gemini is not configured, so ApplyMap cannot generate a source-backed action plan yet.",
            "exams_to_prioritize": [],
            "profile_actions": [],
            "low_value_activities": [],
            "research_or_summer_programs": [],
            "source_notes": ["Set GEMINI_API_KEY to enable the Chancellor action plan."],
        }

    model = (settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request_payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": _prompt(
                            university_name=university_name,
                            user=user,
                            achievements=achievements,
                            search_results=search_results,
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "responseJsonSchema": ADVISOR_SCHEMA,
        },
    }

    try:
        with httpx.Client(timeout=25.0) as client:
            response = client.post(
                url,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=request_payload,
            )
            response.raise_for_status()
        return json.loads(_extract_text(response.json()))
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {
            "summary": "The Chancellor could not generate a reliable JSON plan from the current sources.",
            "exams_to_prioritize": [],
            "profile_actions": [],
            "low_value_activities": [],
            "research_or_summer_programs": [],
            "source_notes": ["Retry with a more specific university name or after checking API configuration."],
        }
