import json
import os
import re
from typing import Any, Optional

import httpx

from ..config import settings
from ..models.achievement import AchievementType, ImpactScope, LeadershipLevel

MAX_IMPORT_BYTES = 200_000
MAX_IMPORT_CHARS = 16_000
DEFAULT_WORD_LIMIT = 22
MAX_IMPORTED_ITEMS = 30
MAX_TOP_ACTIVITIES = 10
MAX_TOP_HONORS = 5
COMMON_APP_ACTIVITY_POSITION_LIMIT = 50
COMMON_APP_ACTIVITY_ORGANIZATION_LIMIT = 100
COMMON_APP_ACTIVITY_DESCRIPTION_LIMIT = 150
COMMON_APP_HONOR_DESCRIPTION_LIMIT = 100

IMPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "strongest_angle": {"type": "string"},
        "needs_student_clarification": {"type": "boolean"},
        "clarifying_questions": {"type": "array", "items": {"type": "string"}},
        "additional_information_recommended": {"type": "boolean"},
        "additional_information_reason": {"type": "string"},
        "additional_information_draft": {"type": "string"},
        "formatting_notes": {"type": "array", "items": {"type": "string"}},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source_index": {"type": "integer"},
                    "type": {"type": "string", "enum": ["activity", "honor"]},
                    "title": {"type": "string"},
                    "organization_name": {"type": ["string", "null"]},
                    "role_title": {"type": ["string", "null"]},
                    "description_raw": {"type": ["string", "null"]},
                    "category": {"type": ["string", "null"]},
                    "hours_per_week": {"type": ["number", "null"]},
                    "weeks_per_year": {"type": ["integer", "null"]},
                    "impact_scope": {"type": ["string", "null"]},
                    "leadership_level": {"type": ["string", "null"]},
                    "truth_risk_flag": {"type": "boolean"},
                    "major_relevance_score": {"type": "number"},
                    "selectivity_score": {"type": "number"},
                    "continuity_score": {"type": "number"},
                    "distinctiveness_score": {"type": "number"},
                    "selection_reason": {"type": "string"},
                    "common_app_text": {"type": "string"},
                    "common_app_position": {"type": ["string", "null"]},
                    "common_app_organization": {"type": ["string", "null"]},
                    "common_app_activity_description": {"type": ["string", "null"]},
                    "common_app_honor_description": {"type": ["string", "null"]},
                    "verification_queries": {"type": "array", "items": {"type": "string"}},
                    "verification_notes": {"type": "array", "items": {"type": "string"}},
                    "missing_or_unclear_facts": {"type": "array", "items": {"type": "string"}},
                    "recommended_rank": {"type": ["integer", "null"]},
                },
                "required": [
                    "source_index",
                    "type",
                    "title",
                    "truth_risk_flag",
                    "major_relevance_score",
                    "selectivity_score",
                    "continuity_score",
                    "distinctiveness_score",
                    "selection_reason",
                    "common_app_text",
                    "common_app_position",
                    "common_app_organization",
                    "common_app_activity_description",
                    "common_app_honor_description",
                    "verification_queries",
                    "verification_notes",
                    "missing_or_unclear_facts",
                    "recommended_rank",
                ],
            },
        },
    },
    "required": [
        "strongest_angle",
        "needs_student_clarification",
        "clarifying_questions",
        "additional_information_recommended",
        "additional_information_reason",
        "additional_information_draft",
        "formatting_notes",
        "items",
    ],
}

HONOR_KEYWORDS = (
    "award",
    "winner",
    "won",
    "prize",
    "medal",
    "honor",
    "honour",
    "olympiad",
    "scholarship",
    "finalist",
    "laureate",
    "distinction",
    "champion",
)


def _profile_context(user: Optional[Any]) -> dict[str, Any]:
    profile = getattr(user, "profile", None)
    if profile is None:
        return {
            "country": getattr(user, "country", None),
        }

    return {
        "country": getattr(user, "country", None),
        "graduation_year": getattr(profile, "graduation_year", None),
        "curriculum": getattr(profile, "curriculum", None),
        "intended_major": getattr(profile, "intended_major", None),
        "sat_score": getattr(profile, "sat_score", None),
        "act_score": getattr(profile, "act_score", None),
        "ielts_score": getattr(profile, "ielts_score", None),
        "toefl_score": getattr(profile, "toefl_score", None),
        "application_preferences_json": getattr(profile, "application_preferences_json", None),
    }


def _compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _count_words(value: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", value))


def _truncate_characters(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    truncated = value[:limit]
    last_space = truncated.rfind(" ")
    if last_space > max(0, limit - 24):
        truncated = truncated[:last_space]
    return truncated.rstrip(",.;: ")


def _clean_string_list(value: Any, *, max_items: int = 6, max_chars: int = 260) -> list[str]:
    if not isinstance(value, list):
        return []

    strings: list[str] = []
    for item in value:
        text = _compact_whitespace(str(item or ""))
        if text:
            strings.append(_truncate_characters(text, max_chars))
        if len(strings) >= max_items:
            break
    return strings


def _enforce_common_app_limit(value: str, word_limit: int, achievement_type: str) -> str:
    words = _compact_whitespace(value).split()
    if word_limit > 0 and len(words) > word_limit:
        value = " ".join(words[:word_limit])
    if achievement_type == AchievementType.activity.value:
        value = _truncate_characters(value, COMMON_APP_ACTIVITY_DESCRIPTION_LIMIT)
    if achievement_type == AchievementType.honor.value:
        value = _truncate_characters(value, COMMON_APP_HONOR_DESCRIPTION_LIMIT)
    return _compact_whitespace(value)


def _activity_position(item: dict[str, Any]) -> str:
    value = _compact_whitespace(str(item.get("common_app_position") or item.get("role_title") or item.get("title") or ""))
    return _truncate_characters(value, COMMON_APP_ACTIVITY_POSITION_LIMIT)


def _activity_organization(item: dict[str, Any]) -> str:
    value = _compact_whitespace(str(item.get("common_app_organization") or item.get("organization_name") or ""))
    return _truncate_characters(value, COMMON_APP_ACTIVITY_ORGANIZATION_LIMIT)


def _activity_description(item: dict[str, Any], word_limit: int) -> str:
    value = _compact_whitespace(
        str(item.get("common_app_activity_description") or item.get("common_app_text") or item.get("description_raw") or "")
    )
    if not value:
        value = _fallback_common_app_text(item, word_limit)
    return _enforce_common_app_limit(value, word_limit, AchievementType.activity.value)


def _honor_description(item: dict[str, Any], word_limit: int) -> str:
    value = _compact_whitespace(
        str(item.get("common_app_honor_description") or item.get("common_app_text") or item.get("title") or "")
    )
    return _enforce_common_app_limit(value, word_limit, AchievementType.honor.value)


def _coerce_enum(enum_cls: Any, value: Any) -> Any:
    if value in (None, "", "null"):
        return None
    try:
        return enum_cls(value)
    except ValueError:
        return None


def _clamp_score(value: Any) -> float:
    try:
        return round(max(0.0, min(10.0, float(value))), 1)
    except (TypeError, ValueError):
        return 5.0


def decode_import_file(file_name: str, raw_bytes: bytes) -> str:
    if len(raw_bytes) > MAX_IMPORT_BYTES:
        raise ValueError("File is too large for MVP bulk import. Keep it under 200 KB.")

    extension = os.path.splitext(file_name or "")[1].lower()
    if extension and extension not in {".txt", ".md", ".csv", ".json"}:
        raise ValueError("MVP import currently supports .txt, .md, .csv, and .json files.")

    for encoding in ("utf-8", "utf-8-sig", "utf-16", "cp1251", "latin-1"):
        try:
            text = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Could not read the uploaded file as text.")

    text = _compact_whitespace(text).strip()
    if not text:
        raise ValueError("The uploaded file is empty.")
    return text[:MAX_IMPORT_CHARS]


def _fallback_title(line: str) -> str:
    line = _compact_whitespace(line)
    chunks = re.split(r"[.;:-]", line, maxsplit=1)
    title = chunks[0].strip() if chunks else line
    return title[:120] or "Untitled achievement"


def _fallback_type(line: str) -> AchievementType:
    normalized = line.lower()
    if any(keyword in normalized for keyword in HONOR_KEYWORDS):
        return AchievementType.honor
    return AchievementType.activity


def _fallback_common_app_text(item: dict[str, Any], word_limit: int) -> str:
    parts = [
        item.get("role_title"),
        item.get("organization_name"),
        item.get("description_raw"),
    ]
    value = _compact_whitespace(". ".join(part for part in parts if part))
    if not value:
        value = item["title"]
    return _enforce_common_app_limit(value, word_limit, item["type"])


def _fallback_parse(raw_text: str, user: Optional[Any], word_limit: int) -> dict[str, Any]:
    from .chancellor_analysis import estimate_chancellor_scores

    lines = [
        _compact_whitespace(line)
        for line in re.split(r"(?:\r?\n)+|(?:\s*[-*•]\s+)", raw_text)
        if _compact_whitespace(line)
    ]

    items: list[dict[str, Any]] = []
    for index, line in enumerate(lines[:MAX_IMPORTED_ITEMS], start=1):
        item_type = _fallback_type(line)
        base_item = {
            "source_index": index,
            "type": item_type.value,
            "title": _fallback_title(line),
            "organization_name": None,
            "role_title": None,
            "description_raw": line,
            "category": None,
            "hours_per_week": None,
            "weeks_per_year": None,
            "impact_scope": None,
            "leadership_level": None,
            "truth_risk_flag": False,
            "selection_reason": "Selected by heuristic fallback because AI extraction was unavailable.",
        }
        scores = estimate_chancellor_scores(base_item, user)
        item = {
            **base_item,
            **scores,
            "common_app_text": "",
            "common_app_position": None,
            "common_app_organization": None,
            "common_app_activity_description": None,
            "common_app_honor_description": None,
            "verification_queries": [],
            "verification_notes": [],
            "missing_or_unclear_facts": ["AI extraction was unavailable; verify the wording against the original evidence."],
            "recommended_rank": None,
        }
        item["common_app_text"] = _fallback_common_app_text(item, word_limit)
        items.append(item)

    strongest_angle = (
        "Present the profile as a focused, evidence-backed student story with the strongest sustained work first."
    )
    return {
        "strongest_angle": strongest_angle,
        "needs_student_clarification": True,
        "clarifying_questions": [
            "Please confirm titles, dates, roles, and measurable outcomes before using the generated Common App wording."
        ],
        "additional_information_recommended": False,
        "additional_information_reason": "",
        "additional_information_draft": "",
        "formatting_notes": ["Gemini extraction was unavailable, so ApplyMap used a conservative local fallback."],
        "items": items,
    }


def _import_prompt(raw_text: str, user: Optional[Any], word_limit: int) -> str:
    payload = {
        "student_profile": _profile_context(user),
        "word_limit": word_limit,
        "common_app_limits": {
            "activities_max_items": MAX_TOP_ACTIVITIES,
            "activity_position_leadership_description_chars": COMMON_APP_ACTIVITY_POSITION_LIMIT,
            "activity_organization_name_chars": COMMON_APP_ACTIVITY_ORGANIZATION_LIMIT,
            "activity_description_chars": COMMON_APP_ACTIVITY_DESCRIPTION_LIMIT,
            "honors_max_items": MAX_TOP_HONORS,
            "honor_title_description_chars": COMMON_APP_HONOR_DESCRIPTION_LIMIT,
        },
        "raw_source_text": raw_text,
    }
    return (
        "You are ApplyMap Chancellor, helping an international student convert a messy mixed-achievement note file "
        "into a clean, factual Common App-ready shortlist.\n\n"
        "Tasks:\n"
        "1. Extract distinct student achievements from the raw text. Merge obvious duplicates into one strongest version.\n"
        "2. Classify each item as either 'activity' or 'honor'.\n"
        "3. Fill structured fields conservatively. If a field is missing, use null instead of inventing facts.\n"
        "4. Score each item from 0 to 10 on major_relevance_score, selectivity_score, continuity_score, and distinctiveness_score.\n"
        "5. Recommend the strongest top 10 activities and top 5 academic honors for a Common App-style application. Use recommended_rank "
        "for selected items and null for the rest.\n"
        "6. For activities, fill separate Common App fields: common_app_position <= 50 characters, "
        "common_app_organization <= 100 characters, and common_app_activity_description <= 150 characters. "
        "Use the activity description for accomplishments and measurable impact, not role repetition.\n"
        "7. For honors, fill common_app_honor_description as one title/description block <= 100 characters.\n"
        "8. strongest_angle must explain the single best overall application angle in one sentence.\n"
        "9. If there are inconsistencies in years, roles, award level, school grade, hours, or metrics, set "
        "needs_student_clarification=true and write short clarifying_questions before the student should trust final wording.\n"
        "10. Recommend Additional Information only when it is genuinely needed to clarify important context that cannot fit "
        "in the activity/honor fields, unusual school/curriculum context, or multiple related awards. If recommended, write a "
        "ready-to-paste concise additional_information_draft; otherwise leave it blank.\n\n"
        "Important constraints:\n"
        "- Do not invent achievements, outcomes, metrics, organizations, dates, leadership roles, or awards.\n"
        "- If the source sounds uncertain or inflated, set truth_risk_flag to true.\n"
        "- Prefer concrete, specific language over hype.\n"
        "- Preserve Kazakhstan/NIS/IB/A-Level context when present.\n"
        "- In English output, MESK/МЭСК means NIS Grade 12 Certificate.\n"
        "- Apply the College Essay Guy-style approach: active verbs, measurable impact, no filler, no repeated role wording, "
        "selectivity where supported, and abbreviations only when they improve clarity.\n"
        "- If the student omits participant counts, selection rates, dates, or exact award level, add those to "
        "missing_or_unclear_facts and propose verification_queries. Do not fabricate counts.\n"
        "- The shortlist should reward spike, depth, selectivity, continuity, and distinctive impact.\n"
        "- A weak selected item is worse than leaving a slot empty. Only rank items that are truly shortlist-worthy.\n\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False, default=str)}"
    )


def _extract_gemini_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    content = candidates[0].get("content") if candidates else {}
    parts = content.get("parts") or []
    return str(parts[0].get("text", "")) if parts else ""


def _gemini_parse(raw_text: str, user: Optional[Any], word_limit: int) -> Optional[dict[str, Any]]:
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        return None

    model = (settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": _import_prompt(raw_text, user, word_limit)}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "responseJsonSchema": IMPORT_SCHEMA,
        },
    }

    try:
        with httpx.Client(timeout=25.0) as client:
            response = client.post(
                url,
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
        response_text = _extract_gemini_text(response.json())
        parsed = json.loads(response_text)
        if not isinstance(parsed, dict) or not isinstance(parsed.get("items"), list):
            return None
        return parsed
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def _local_score(item: dict[str, Any]) -> float:
    return (
        float(item.get("major_relevance_score") or 0)
        + float(item.get("selectivity_score") or 0)
        + float(item.get("continuity_score") or 0)
        + float(item.get("distinctiveness_score") or 0)
    )


class SearchNotConfiguredError(RuntimeError):
    pass


def _google_search(query: str, *, num: int = 3) -> list[dict[str, str]]:
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

    results = response.json().get("items") or []
    return [
        {
            "title": _compact_whitespace(str(item.get("title") or "")),
            "url": str(item.get("link") or ""),
            "snippet": _compact_whitespace(str(item.get("snippet") or "")),
        }
        for item in results
        if item.get("link")
    ]


def _default_verification_query(item: dict[str, Any], user: Optional[Any]) -> str:
    country = _compact_whitespace(str(getattr(user, "country", "") or ""))
    parts = [
        f'"{item.get("title")}"' if item.get("title") else "",
        f'"{item.get("organization_name")}"' if item.get("organization_name") else "",
        country if country else "",
        "participants results award official",
    ]
    return _compact_whitespace(" ".join(part for part in parts if part))


def _format_search_note(result: dict[str, str]) -> str:
    title = _truncate_characters(result.get("title") or "Search result", 80)
    snippet = _truncate_characters(result.get("snippet") or "No snippet available", 150)
    url = result.get("url") or ""
    return _truncate_characters(f"Source candidate: {title} - {snippet} ({url})", 300)


def _attach_google_verification(items: list[dict[str, Any]], user: Optional[Any]) -> list[str]:
    if not settings.GOOGLE_SEARCH_API_KEY.strip() or not settings.GOOGLE_SEARCH_ENGINE_ID.strip():
        return [
            "Google Search is not configured. Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID to verify achievements online."
        ]

    notes: list[str] = []
    for item in items:
        query = (item.get("verification_queries") or [_default_verification_query(item, user)])[0]
        if not query:
            item.setdefault("missing_or_unclear_facts", []).append("No searchable title or organization was available.")
            continue
        try:
            search_results = _google_search(query, num=3)
        except (SearchNotConfiguredError, httpx.HTTPError):
            item.setdefault("missing_or_unclear_facts", []).append(
                "Google verification failed for this item; ask the student for an official link or evidence."
            )
            continue

        if not search_results:
            item.setdefault("missing_or_unclear_facts", []).append(
                "No Google result found for this item; ask the student for an official source or certificate."
            )
            continue

        item.setdefault("verification_notes", []).extend(_format_search_note(result) for result in search_results[:3])
        notes.append(f"Checked Google for: {query}")

    return notes


def _normalize_items(result: dict[str, Any], word_limit: int) -> dict[str, Any]:
    normalized_items: list[dict[str, Any]] = []

    for index, raw_item in enumerate(result.get("items") or [], start=1):
        title = _compact_whitespace(str(raw_item.get("title") or ""))
        if not title:
            continue

        item_type = _coerce_enum(AchievementType, raw_item.get("type")) or AchievementType.activity
        normalized = {
            "source_index": int(raw_item.get("source_index") or index),
            "type": item_type.value,
            "title": title[:500],
            "organization_name": _compact_whitespace(str(raw_item.get("organization_name") or "")) or None,
            "role_title": _compact_whitespace(str(raw_item.get("role_title") or "")) or None,
            "description_raw": _compact_whitespace(str(raw_item.get("description_raw") or "")) or None,
            "category": _compact_whitespace(str(raw_item.get("category") or "")) or None,
            "hours_per_week": raw_item.get("hours_per_week"),
            "weeks_per_year": raw_item.get("weeks_per_year"),
            "impact_scope": (_coerce_enum(ImpactScope, raw_item.get("impact_scope")) or None),
            "leadership_level": (_coerce_enum(LeadershipLevel, raw_item.get("leadership_level")) or None),
            "truth_risk_flag": bool(raw_item.get("truth_risk_flag")),
            "major_relevance_score": _clamp_score(raw_item.get("major_relevance_score")),
            "selectivity_score": _clamp_score(raw_item.get("selectivity_score")),
            "continuity_score": _clamp_score(raw_item.get("continuity_score")),
            "distinctiveness_score": _clamp_score(raw_item.get("distinctiveness_score")),
            "selection_reason": _compact_whitespace(str(raw_item.get("selection_reason") or "")),
            "common_app_text": _enforce_common_app_limit(
                str(raw_item.get("common_app_text") or ""),
                word_limit,
                item_type.value,
            ),
            "common_app_position": _compact_whitespace(str(raw_item.get("common_app_position") or "")) or None,
            "common_app_organization": _compact_whitespace(str(raw_item.get("common_app_organization") or "")) or None,
            "common_app_activity_description": _compact_whitespace(
                str(raw_item.get("common_app_activity_description") or "")
            )
            or None,
            "common_app_honor_description": _compact_whitespace(str(raw_item.get("common_app_honor_description") or ""))
            or None,
            "verification_queries": _clean_string_list(raw_item.get("verification_queries"), max_items=3, max_chars=160),
            "verification_notes": _clean_string_list(raw_item.get("verification_notes"), max_items=5, max_chars=300),
            "missing_or_unclear_facts": _clean_string_list(
                raw_item.get("missing_or_unclear_facts"), max_items=6, max_chars=180
            ),
            "recommended_rank": raw_item.get("recommended_rank"),
        }
        if not normalized["common_app_text"]:
            normalized["common_app_text"] = _fallback_common_app_text(normalized, word_limit)
        if item_type == AchievementType.activity:
            normalized["common_app_position"] = _activity_position(normalized)
            normalized["common_app_organization"] = _activity_organization(normalized) or None
            normalized["common_app_activity_description"] = _activity_description(normalized, word_limit)
            normalized["common_app_text"] = normalized["common_app_activity_description"]
            normalized["common_app_honor_description"] = None
        else:
            normalized["common_app_honor_description"] = _honor_description(normalized, word_limit)
            normalized["common_app_text"] = normalized["common_app_honor_description"]
            normalized["common_app_position"] = None
            normalized["common_app_organization"] = None
            normalized["common_app_activity_description"] = None
        normalized_items.append(normalized)

    return {
        "strongest_angle": _compact_whitespace(str(result.get("strongest_angle") or "")),
        "needs_student_clarification": bool(result.get("needs_student_clarification")),
        "clarifying_questions": _clean_string_list(result.get("clarifying_questions"), max_items=8, max_chars=220),
        "additional_information_recommended": bool(result.get("additional_information_recommended")),
        "additional_information_reason": _compact_whitespace(str(result.get("additional_information_reason") or "")),
        "additional_information_draft": _compact_whitespace(str(result.get("additional_information_draft") or "")),
        "formatting_notes": _clean_string_list(result.get("formatting_notes"), max_items=8, max_chars=220),
        "items": normalized_items,
    }


def parse_achievement_import(raw_text: str, user: Optional[Any], word_limit: int) -> dict[str, Any]:
    parsed = _gemini_parse(raw_text, user, word_limit) or _fallback_parse(raw_text, user, word_limit)
    normalized = _normalize_items(parsed, word_limit)
    items = normalized["items"]

    activities = [item for item in items if item["type"] == AchievementType.activity.value]
    honors = [item for item in items if item["type"] == AchievementType.honor.value]

    ranked_activities = sorted(
        activities,
        key=lambda item: (
            item.get("recommended_rank") is None,
            item.get("recommended_rank") or 99,
            -_local_score(item),
        ),
    )
    ranked_honors = sorted(
        honors,
        key=lambda item: (
            item.get("recommended_rank") is None,
            item.get("recommended_rank") or 99,
            -_local_score(item),
        ),
    )

    if not any(item.get("recommended_rank") for item in ranked_activities):
        for rank, item in enumerate(sorted(activities, key=_local_score, reverse=True)[:MAX_TOP_ACTIVITIES], start=1):
            item["recommended_rank"] = rank
        ranked_activities = sorted(activities, key=lambda item: item.get("recommended_rank") or 99)

    if not any(item.get("recommended_rank") for item in ranked_honors):
        for rank, item in enumerate(sorted(honors, key=_local_score, reverse=True)[:MAX_TOP_HONORS], start=1):
            item["recommended_rank"] = rank
        ranked_honors = sorted(honors, key=lambda item: item.get("recommended_rank") or 99)

    normalized["strongest_angle"] = normalized["strongest_angle"] or (
        "Lead with the most selective, sustained, and distinctive work, then support it with the strongest honors."
    )
    normalized["top_activities"] = [
        item
        for item in ranked_activities
        if item.get("recommended_rank") and item["recommended_rank"] <= MAX_TOP_ACTIVITIES
    ][:MAX_TOP_ACTIVITIES]
    normalized["top_honors"] = [
        item for item in ranked_honors if item.get("recommended_rank") and item["recommended_rank"] <= MAX_TOP_HONORS
    ][:MAX_TOP_HONORS]
    verification_notes = _attach_google_verification(
        [*normalized["top_activities"], *normalized["top_honors"]],
        user,
    )
    normalized["formatting_notes"].extend(verification_notes)
    return normalized
