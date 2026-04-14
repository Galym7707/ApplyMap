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

IMPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "strongest_angle": {
            "type": "string",
            "description": "One concise sentence explaining the strongest overall Common App positioning angle.",
        },
        "items": {
            "type": "array",
            "maxItems": MAX_IMPORTED_ITEMS,
            "items": {
                "type": "object",
                "properties": {
                    "source_index": {"type": "integer", "minimum": 1},
                    "type": {"type": "string", "enum": ["activity", "honor"]},
                    "title": {"type": "string"},
                    "organization_name": {"type": ["string", "null"]},
                    "role_title": {"type": ["string", "null"]},
                    "description_raw": {"type": ["string", "null"]},
                    "category": {"type": ["string", "null"]},
                    "hours_per_week": {"type": ["number", "null"], "minimum": 0, "maximum": 168},
                    "weeks_per_year": {"type": ["integer", "null"], "minimum": 0, "maximum": 52},
                    "impact_scope": {
                        "type": ["string", "null"],
                        "enum": [
                            "school",
                            "local",
                            "regional",
                            "national",
                            "international",
                            "family",
                            "personal",
                            None,
                        ],
                    },
                    "leadership_level": {
                        "type": ["string", "null"],
                        "enum": ["none", "member", "lead", "founder", "captain", None],
                    },
                    "truth_risk_flag": {"type": "boolean"},
                    "major_relevance_score": {"type": "number", "minimum": 0, "maximum": 10},
                    "selectivity_score": {"type": "number", "minimum": 0, "maximum": 10},
                    "continuity_score": {"type": "number", "minimum": 0, "maximum": 10},
                    "distinctiveness_score": {"type": "number", "minimum": 0, "maximum": 10},
                    "selection_reason": {"type": "string"},
                    "common_app_text": {"type": "string"},
                    "recommended_rank": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
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
                    "recommended_rank",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["strongest_angle", "items"],
    "additionalProperties": False,
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


def _enforce_common_app_limit(value: str, word_limit: int, achievement_type: str) -> str:
    words = _compact_whitespace(value).split()
    if word_limit > 0 and len(words) > word_limit:
        value = " ".join(words[:word_limit])
    if achievement_type == AchievementType.activity.value:
        value = _truncate_characters(value, 150)
    return _compact_whitespace(value)


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
            "recommended_rank": None,
        }
        item["common_app_text"] = _fallback_common_app_text(item, word_limit)
        items.append(item)

    strongest_angle = (
        "Present the profile as a focused, evidence-backed student story with the strongest sustained work first."
    )
    return {"strongest_angle": strongest_angle, "items": items}


def _import_prompt(raw_text: str, user: Optional[Any], word_limit: int) -> str:
    payload = {
        "student_profile": _profile_context(user),
        "word_limit": word_limit,
        "raw_source_text": raw_text,
    }
    return (
        "You are ApplyMap Chancellor, helping an international student convert a messy mixed-achievement note file "
        "into a clean Common App-ready shortlist.\n\n"
        "Tasks:\n"
        "1. Extract distinct student achievements from the raw text. Merge obvious duplicates into one strongest version.\n"
        "2. Classify each item as either 'activity' or 'honor'.\n"
        "3. Fill structured fields conservatively. If a field is missing, use null instead of inventing facts.\n"
        "4. Score each item from 0 to 10 on major_relevance_score, selectivity_score, continuity_score, and distinctiveness_score.\n"
        "5. Recommend the strongest top 10 activities and top 5 honors for a Common App-style application. Use recommended_rank "
        "for selected items and null for the rest.\n"
        f"6. Write one concise Common App-ready wording per item under {word_limit} words. For activities, keep it under 150 characters too.\n"
        "7. strongest_angle must explain the single best overall application angle in one sentence.\n\n"
        "Important constraints:\n"
        "- Do not invent achievements, outcomes, metrics, organizations, dates, leadership roles, or awards.\n"
        "- If the source sounds uncertain or inflated, set truth_risk_flag to true.\n"
        "- Prefer concrete, specific language over hype.\n"
        "- Preserve Kazakhstan/NIS/IB/A-Level context when present.\n"
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
            "recommended_rank": raw_item.get("recommended_rank"),
        }
        if not normalized["common_app_text"]:
            normalized["common_app_text"] = _fallback_common_app_text(normalized, word_limit)
        normalized_items.append(normalized)

    return {
        "strongest_angle": _compact_whitespace(str(result.get("strongest_angle") or "")),
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
        for rank, item in enumerate(sorted(activities, key=_local_score, reverse=True)[:10], start=1):
            item["recommended_rank"] = rank
        ranked_activities = sorted(activities, key=lambda item: item.get("recommended_rank") or 99)

    if not any(item.get("recommended_rank") for item in ranked_honors):
        for rank, item in enumerate(sorted(honors, key=_local_score, reverse=True)[:5], start=1):
            item["recommended_rank"] = rank
        ranked_honors = sorted(honors, key=lambda item: item.get("recommended_rank") or 99)

    normalized["strongest_angle"] = normalized["strongest_angle"] or (
        "Lead with the most selective, sustained, and distinctive work, then support it with the strongest honors."
    )
    normalized["top_activities"] = [
        item for item in ranked_activities if item.get("recommended_rank") and item["recommended_rank"] <= 10
    ][:10]
    normalized["top_honors"] = [
        item for item in ranked_honors if item.get("recommended_rank") and item["recommended_rank"] <= 5
    ][:5]
    return normalized
