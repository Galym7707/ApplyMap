"""
Rewrite service for generating style variants of achievement descriptions.
Uses Gemini when available, then falls back to conservative local formatting.
"""
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models.achievement import Achievement, AchievementType
from ..models.report import OptimizationReport, RewriteVariant
from .counselor_knowledge import CHANCELLOR_COUNSELOR_FRAMEWORK


COMMON_APP_ACTIVITY_DESC_LIMIT = 150
COMMON_APP_HONOR_DESC_LIMIT = 100
KAIST_DESC_LIMIT = 200
KOREA_DEFAULT_DESC_LIMIT = 300

STYLE_ORDER: list[tuple[str, bool, str]] = [
    (
        "factual",
        False,
        "Clean English wording that preserves the verified facts without hype.",
    ),
    (
        "impact_first",
        True,
        "Leads with the strongest outcome, scope, or selectivity before explaining the role.",
    ),
    (
        "understated",
        False,
        "Concise, restrained version that keeps the student's voice factual.",
    ),
]

REWRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "variants": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "style_mode": {
                        "type": "string",
                        "enum": ["factual", "impact_first", "understated"],
                    },
                    "text": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": ["style_mode", "text", "explanation"],
            },
        },
    },
    "required": ["variants"],
}


def _compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _truncate_to_limit(text: str, limit: int) -> str:
    """Hard truncate text to a character limit, breaking at a word boundary when possible."""
    text = _compact_whitespace(text)
    if len(text) <= limit:
        return text
    truncated = text[:limit]
    last_space = truncated.rfind(" ")
    if last_space > limit - 24:
        truncated = truncated[:last_space]
    return truncated.rstrip(",.;: ")


def _has_cyrillic(value: str) -> bool:
    return bool(re.search(r"[\u0400-\u04FF]", value or ""))


def _ascii_punctuation(value: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return value


def _normalize_award_level(value: str) -> str:
    value = re.sub(r"\bRepublican\b", "National", value, flags=re.IGNORECASE)
    value = re.sub(r"\bRespublikalyk\b", "National", value, flags=re.IGNORECASE)
    value = re.sub(r"\bRespublikanskiy\b", "National", value, flags=re.IGNORECASE)
    return value


def _capitalize_first(value: str) -> str:
    if not value:
        return value
    for index, char in enumerate(value):
        if char.isalpha():
            return value[:index] + char.upper() + value[index + 1 :]
    return value


def _extract_year_phrases(value: str) -> list[str]:
    years: list[str] = []
    for match in re.finditer(r"\b20\d{2}(?:\s*[-\u2013\u2014]\s*(?:20)?\d{2})?\b", value or ""):
        year = _ascii_punctuation(match.group(0))
        year = re.sub(r"\s*-\s*", "-", year)
        if year not in years:
            years.append(year)
    return years[:2]


def _preserve_required_year(text: str, required_years: list[str], limit: int) -> str:
    if not text or not required_years:
        return text
    if any(year in text for year in required_years):
        return text

    suffix = f", {required_years[0]}"
    if text.endswith("."):
        suffix = f" {required_years[0]}."
        base = text[:-1]
    else:
        base = text
    if len(base) + len(suffix) <= limit:
        return f"{base}{suffix}"

    base = _truncate_to_limit(base, max(1, limit - len(suffix)))
    return f"{base}{suffix}"


def _clean_generated_text(text: str, *, limit: int, required_years: list[str]) -> str:
    text = _ascii_punctuation(_compact_whitespace(text)).strip(" \"'")
    text = _normalize_award_level(text)
    text = _capitalize_first(text)
    if _has_cyrillic(text):
        return ""
    text = _preserve_required_year(text, required_years, limit)
    return _truncate_to_limit(text, limit)


def _achievement_type(achievement: Achievement) -> str:
    value = getattr(achievement.type, "value", achievement.type)
    return str(value or AchievementType.activity.value)


def _target_format(report: OptimizationReport, achievement: Achievement) -> dict[str, Any]:
    university = getattr(report, "university", None)
    name = str(getattr(university, "name", "") or "")
    country = str(getattr(university, "country", "") or "")
    application_system = str(getattr(university, "application_system", "") or "")
    haystack = f"{name} {country} {application_system}".lower()

    if "korea" in haystack or any(token in haystack for token in ["kaist", "unist", "postech", "yonsei"]):
        if "kaist" in haystack:
            return {
                "label": "KAIST Apply",
                "limit": KAIST_DESC_LIMIT,
                "limit_unit": "English bytes/chars",
                "is_common_app": False,
                "instruction": "Use KAIST-style concise English. Prioritize year, placement/selectivity, role, and quantified output.",
            }
        return {
            "label": "Korean university application",
            "limit": KOREA_DEFAULT_DESC_LIMIT,
            "limit_unit": "English bytes/chars",
            "is_common_app": False,
            "instruction": "Do not assume Common App. Use concise Study in Korea or university-portal-ready English.",
        }

    if _achievement_type(achievement) == AchievementType.honor.value:
        return {
            "label": "Common App honors",
            "limit": COMMON_APP_HONOR_DESC_LIMIT,
            "limit_unit": "characters",
            "is_common_app": True,
            "instruction": "Write one Common App honor title/description block.",
        }

    return {
        "label": "Common App activities",
        "limit": COMMON_APP_ACTIVITY_DESC_LIMIT,
        "limit_unit": "characters",
        "is_common_app": True,
        "instruction": "Write a Common App activity description. Do not repeat the position field.",
    }


def _extract_key_facts(achievement: Achievement) -> Dict[str, Any]:
    """Extract factual elements from the achievement for use in rewrites."""
    facts: Dict[str, Any] = {
        "type": _achievement_type(achievement),
        "title": achievement.title,
        "organization_name": achievement.organization_name,
        "role_title": achievement.role_title,
        "description_raw": achievement.description_raw,
        "category": achievement.category,
        "start_date": achievement.start_date.isoformat() if achievement.start_date else None,
        "end_date": achievement.end_date.isoformat() if achievement.end_date else None,
        "hours_per_week": achievement.hours_per_week,
        "weeks_per_year": achievement.weeks_per_year,
        "impact_scope": getattr(achievement.impact_scope, "value", achievement.impact_scope),
        "leadership_level": getattr(achievement.leadership_level, "value", achievement.leadership_level),
    }
    return {key: value for key, value in facts.items() if value not in (None, "")}


def _source_text(facts: dict[str, Any]) -> str:
    return " ".join(str(value) for value in facts.values() if value not in (None, ""))


def _fallback_text(achievement: Achievement, facts: dict[str, Any], limit: int, required_years: list[str]) -> str:
    parts = [
        str(facts.get("role_title") or ""),
        f"at {facts['organization_name']}" if facts.get("organization_name") else "",
        str(facts.get("description_raw") or facts.get("title") or ""),
    ]
    text = _clean_generated_text(" ".join(part for part in parts if part), limit=limit, required_years=required_years)
    if text:
        return text
    return _truncate_to_limit(
        "English rewrite unavailable; verify exact facts before submission.",
        limit,
    )


def _rewrite_prompt(
    *,
    achievement: Achievement,
    facts: dict[str, Any],
    target_format: dict[str, Any],
    required_years: list[str],
) -> str:
    payload = {
        "achievement_facts": facts,
        "target_format": target_format,
        "required_years_from_source": required_years,
    }
    return (
        "You are ApplyMap Chancellor. Rewrite one achievement into copy-paste-ready application text.\n\n"
        f"{CHANCELLOR_COUNSELOR_FRAMEWORK}\n\n"
        "Rules:\n"
        "- Return exactly three variants: factual, impact_first, and understated.\n"
        "- Output only polished English text. Translate Russian, Kazakh, or mixed-language input into English.\n"
        "- Fix capitalization, grammar, and informal phrasing.\n"
        "- Preserve years, date ranges, grade level, number of people served, event names, placements, and supported metrics.\n"
        "- Never replace a concrete source detail with a guessed or more impressive detail. If the source says gift cards, "
        "lessons, mentoring, or another specific activity, translate that detail directly; do not invent tournaments, "
        "research, publications, awards, or program names.\n"
        "- Translate Kazakhstan award level words like Republican/Respublikalyk/Respublikanskiy as National unless an official "
        "English title clearly uses Republican.\n"
        "- Do not invent facts, participant counts, selection rates, titles, or outcomes.\n"
        "- Use ASCII punctuation. Do not output Cyrillic text.\n"
        f"- Target format: {target_format['label']}; limit: {target_format['limit']} {target_format['limit_unit']}.\n"
        f"- {target_format['instruction']}\n"
        "- For Korean universities, do not call the output Common App wording unless the application system is Common App.\n"
        "- Keep the meaning even when compressing. If the source says the student mentored five 8th graders as an 11th grader "
        "in 2024-2025 and organized events, keep those facts in concise English.\n"
        "- Each text must be no longer than the target limit.\n"
        "- Explanations should be one short sentence and should not mention internal materials.\n\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False, default=str)}"
    )


def _extract_gemini_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    content = candidates[0].get("content") if candidates else {}
    parts = content.get("parts") or []
    return str(parts[0].get("text", "")) if parts else ""


def _gemini_rewrite_variants(
    achievement: Achievement,
    facts: dict[str, Any],
    target_format: dict[str, Any],
    required_years: list[str],
) -> Optional[dict[str, tuple[str, str]]]:
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        return None

    model = (settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": _rewrite_prompt(
                            achievement=achievement,
                            facts=facts,
                            target_format=target_format,
                            required_years=required_years,
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
            "responseJsonSchema": REWRITE_SCHEMA,
        },
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            response = client.post(
                url,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
        parsed = json.loads(_extract_gemini_text(response.json()))
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None

    variants: dict[str, tuple[str, str]] = {}
    for raw_variant in parsed.get("variants") or []:
        style_mode = str(raw_variant.get("style_mode") or "")
        if style_mode not in {style for style, _, _ in STYLE_ORDER}:
            continue
        text = _clean_generated_text(
            str(raw_variant.get("text") or ""),
            limit=int(target_format["limit"]),
            required_years=required_years,
        )
        if not text:
            continue
        explanation = _compact_whitespace(str(raw_variant.get("explanation") or "Generated from verified student facts."))
        variants[style_mode] = (text, explanation)

    return variants or None


def generate_rewrite_variants(
    db: Session,
    achievement: Achievement,
    report: OptimizationReport,
) -> List[RewriteVariant]:
    """
    Generate 3 style variants for an achievement.
    Returns RewriteVariant objects (not yet committed to DB).
    """
    facts = _extract_key_facts(achievement)
    target_format = _target_format(report, achievement)
    required_years = _extract_year_phrases(_source_text(facts))
    generated = _gemini_rewrite_variants(achievement, facts, target_format, required_years) or {}

    fallback = _fallback_text(achievement, facts, int(target_format["limit"]), required_years)
    variants = []
    for style_mode, is_recommended, default_explanation in STYLE_ORDER:
        text, explanation = generated.get(style_mode, (fallback, default_explanation))
        variant = RewriteVariant(
            achievement_id=achievement.id,
            report_id=report.id,
            style_mode=style_mode,
            text=text,
            character_count=len(text),
            is_recommended=is_recommended,
            explanation=explanation,
        )
        variants.append(variant)

    return variants
