import json
from typing import Any, Optional

import httpx

from ..config import settings
from .counselor_knowledge import CHANCELLOR_COUNSELOR_FRAMEWORK


SCORE_KEYS = (
    "major_relevance_score",
    "selectivity_score",
    "continuity_score",
    "distinctiveness_score",
)

SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "major_relevance_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 10,
            "description": "Alignment between the achievement and the student's intended major or academic direction.",
        },
        "selectivity_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 10,
            "description": "Competitiveness, award level, and selection difficulty behind the achievement.",
        },
        "continuity_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 10,
            "description": "Sustained commitment based on duration, hours, and ongoing responsibility.",
        },
        "distinctiveness_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 10,
            "description": "How uncommon, self-directed, leadership-heavy, impact-heavy, or spike-relevant the achievement is.",
        },
    },
    "required": list(SCORE_KEYS),
    "additionalProperties": False,
}

ADMISSIONS_FRAMEWORK = """
Use this admissions strategy framework:
- Depth beats breadth. A few world-class or deeply developed achievements should score higher than many generic activities.
- Favor a strong, authentic spike: a sustained area where the student shows uncommon initiative, impact, rigor, or visibility.
- Impact and leadership matter most when they are specific: built, published, founded, led, scaled, won, selected, presented, or served a defined audience.
- Authenticity matters. Do not reward over-polished, vague, buzzword-heavy, or all-perfect claims without concrete evidence.
- Major strategy matters. If the intended major is crowded for the student's context, reward achievements that make the profile more distinctive or cross-disciplinary.
- Home-country context matters for international students. Global impact is stronger when it is also tied back to a real local or national context.
- Be conservative when evidence is missing. Never invent facts.
""".strip()


def _value(source: Any, field: str) -> Any:
    if isinstance(source, dict):
        return source.get(field)
    return getattr(source, field, None)


def _enum_value(value: Any) -> str:
    if value is None:
        return ""
    return getattr(value, "value", str(value))


def _text(source: Any) -> str:
    parts = [
        _value(source, "title"),
        _value(source, "organization_name"),
        _value(source, "role_title"),
        _value(source, "description_raw"),
        _value(source, "category"),
    ]
    return " ".join(str(part) for part in parts if part).lower()


def _profile_major(user: Optional[Any]) -> str:
    profile = getattr(user, "profile", None)
    intended_major = getattr(profile, "intended_major", None)
    return str(intended_major).lower() if intended_major else ""


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _clamp(value: float) -> float:
    return round(max(0.0, min(10.0, value)), 1)


def _profile_context(user: Optional[Any]) -> dict[str, Any]:
    profile = getattr(user, "profile", None)
    if profile is None:
        return {}

    return {
        "country": getattr(user, "country", None),
        "graduation_year": getattr(profile, "graduation_year", None),
        "curriculum": getattr(profile, "curriculum", None),
        "intended_major": getattr(profile, "intended_major", None),
        "sat_score": getattr(profile, "sat_score", None),
        "act_score": getattr(profile, "act_score", None),
        "ielts_score": getattr(profile, "ielts_score", None),
        "toefl_score": getattr(profile, "toefl_score", None),
    }


def _achievement_context(source: Any) -> dict[str, Any]:
    return {
        "type": _enum_value(_value(source, "type")),
        "title": _value(source, "title"),
        "organization_name": _value(source, "organization_name"),
        "role_title": _value(source, "role_title"),
        "description_raw": _value(source, "description_raw"),
        "category": _value(source, "category"),
        "hours_per_week": _value(source, "hours_per_week"),
        "weeks_per_year": _value(source, "weeks_per_year"),
        "impact_scope": _enum_value(_value(source, "impact_scope")),
        "leadership_level": _enum_value(_value(source, "leadership_level")),
    }


def _gemini_prompt(source: Any, user: Optional[Any]) -> str:
    payload = {
        "student_profile": _profile_context(user),
        "achievement": _achievement_context(source),
    }
    return (
        "You are ApplyMap Chancellor, an admissions evaluation assistant for international applicants. "
        "Score one student achievement. Use the framework below, but only use facts present in the input.\n\n"
        "Kazakhstan context: preserve NIS selection context, NIS Grade 12 Certificate/MESK wording, UNT/ENT, IB, "
        "and A-levels when they appear, but do not imply that final UNT/ENT or final NIS Grade 12 Certificate results "
        "are available at the start of Grade 12 or required for U.S. initial applications unless an official target "
        "source says so. NIS applicants may have selective STEM-focused, trilingual, Cambridge-aligned academic "
        "backgrounds. MESK in Russian/Kazakh user language maps to NIS Grade 12 Certificate in English output.\n\n"
        f"{ADMISSIONS_FRAMEWORK}\n\n"
        f"{CHANCELLOR_COUNSELOR_FRAMEWORK}\n\n"
        "Score each field from 0 to 10, using one decimal place when useful:\n"
        "- major_relevance_score: fit with intended major, academic direction, and profile strategy.\n"
        "- selectivity_score: competitiveness, award level, and selection difficulty.\n"
        "- continuity_score: sustained commitment based on time, duration, and responsibility.\n"
        "- distinctiveness_score: uncommon spike, initiative, leadership, originality, visibility, or impact.\n\n"
        "Be conservative when evidence is missing. Return JSON only.\n\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False, default=str)}"
    )


def _extract_gemini_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    content = candidates[0].get("content") if candidates else {}
    parts = content.get("parts") or []
    return str(parts[0].get("text", "")) if parts else ""


def _scores_from_mapping(value: Any) -> Optional[dict[str, float]]:
    if not isinstance(value, dict):
        return None

    scores: dict[str, float] = {}
    for key in SCORE_KEYS:
        raw = value.get(key)
        if raw is None or isinstance(raw, bool):
            return None
        try:
            scores[key] = _clamp(float(raw))
        except (TypeError, ValueError):
            return None
    return scores


def _gemini_scores(source: Any, user: Optional[Any]) -> Optional[dict[str, float]]:
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        return None

    model = (settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request_payload = {
        "contents": [{"parts": [{"text": _gemini_prompt(source, user)}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "responseJsonSchema": SCORE_SCHEMA,
        },
    }

    try:
        with httpx.Client(timeout=12.0) as client:
            response = client.post(
                url,
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json=request_payload,
            )
            response.raise_for_status()
        response_text = _extract_gemini_text(response.json())
        return _scores_from_mapping(json.loads(response_text))
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def _heuristic_scores(source: Any, user: Optional[Any] = None) -> dict[str, float]:
    text = _text(source)
    scope = _enum_value(_value(source, "impact_scope"))
    leadership = _enum_value(_value(source, "leadership_level"))
    hours = _value(source, "hours_per_week") or 0
    weeks = _value(source, "weeks_per_year") or 0
    intended_major = _profile_major(user)

    major_score = 5.0
    if intended_major:
        major_terms = [
            term
            for term in intended_major.replace("/", " ").replace(",", " ").split()
            if len(term) > 2
        ]
        major_score = 7.0 if any(term in text for term in major_terms) else 4.5
    elif _contains_any(
        text,
        [
            "research",
            "science",
            "math",
            "physics",
            "chemistry",
            "biology",
            "robot",
            "programming",
            "engineering",
            "economics",
        ],
    ):
        major_score = 6.0
    if _contains_any(text, ["coursework", "project", "lab", "olympiad", "competition", "internship"]):
        major_score += 1.0

    scope_base = {
        "international": 8.0,
        "national": 7.0,
        "regional": 5.5,
        "local": 4.5,
        "school": 3.5,
        "family": 3.0,
        "personal": 2.5,
    }
    selectivity_score = scope_base.get(scope, 4.5)
    if _contains_any(
        text,
        ["selected", "selective", "winner", "finalist", "medal", "olympiad", "scholarship", "first place", "top "],
    ):
        selectivity_score += 1.5
    if _contains_any(text, ["imo", "ipho", "ibo", "nasa", "global", "international"]):
        selectivity_score += 1.0

    annual_hours = float(hours) * float(weeks)
    if annual_hours >= 250:
        continuity_score = 8.0
    elif annual_hours >= 120:
        continuity_score = 6.5
    elif annual_hours >= 40:
        continuity_score = 5.0
    elif weeks or hours:
        continuity_score = 3.5
    else:
        continuity_score = 4.0
    if _contains_any(text, ["year", "years", "since", "ongoing", "weekly", "semester"]):
        continuity_score += 1.0

    distinctiveness_score = 4.5
    if leadership in {"lead", "captain", "founder"}:
        distinctiveness_score += 1.5
    if scope in {"national", "international"}:
        distinctiveness_score += 1.0
    if _contains_any(
        text,
        ["founded", "created", "built", "published", "patent", "research", "startup", "world champion", "first place"],
    ):
        distinctiveness_score += 1.5
    if _contains_any(text, ["press", "media", "tedx", "conference", "downloads", "users"]):
        distinctiveness_score += 1.0
    if _contains_any(text, ["helped", "member", "participated"]) and len(text) < 120:
        distinctiveness_score -= 0.5

    return {
        "major_relevance_score": _clamp(major_score),
        "selectivity_score": _clamp(selectivity_score),
        "continuity_score": _clamp(continuity_score),
        "distinctiveness_score": _clamp(distinctiveness_score),
    }


def estimate_chancellor_scores(source: Any, user: Optional[Any] = None) -> dict[str, float]:
    return _gemini_scores(source, user) or _heuristic_scores(source, user)
