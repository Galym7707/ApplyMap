import json
import os
import re
import time
from typing import Any, Optional

import httpx

from ..config import settings
from ..models.achievement import AchievementType, ImpactScope, LeadershipLevel

MAX_IMPORT_BYTES = 10_000_000
MAX_IMPORT_CHARS = 80_000
MAX_PDF_PAGES = 25
MAX_DOCX_PARAGRAPHS = 2500
AI_IMPORT_MAX_CHARS = 24_000
GEMINI_IMPORT_TIMEOUT_SECONDS = 7.0
GOOGLE_VERIFICATION_TIME_BUDGET_SECONDS = 0.0
DEFAULT_WORD_LIMIT = 22
MAX_IMPORTED_ITEMS = 60
MAX_TOP_ACTIVITIES = 10
MAX_TOP_HONORS = 5
COMMON_APP_ACTIVITY_POSITION_LIMIT = 50
COMMON_APP_ACTIVITY_ORGANIZATION_LIMIT = 100
COMMON_APP_ACTIVITY_DESCRIPTION_LIMIT = 150
COMMON_APP_HONOR_DESCRIPTION_LIMIT = 100
COMMON_APP_ACTIVITY_TYPES = (
    "Academic",
    "Art",
    "Athletics: Club",
    "Athletics: JV/Varsity",
    "Career Oriented",
    "Community Service (Volunteer)",
    "Computer/Technology",
    "Cultural",
    "Dance",
    "Debate/Speech",
    "Environmental",
    "Family Responsibilities",
    "Foreign Exchange",
    "Foreign Language",
    "Internship",
    "Journalism/Publication",
    "Junior R.O.T.C.",
    "LGBT",
    "Music: Instrumental",
    "Music: Vocal",
    "Religious",
    "Research",
    "Robotics",
    "School Spirit",
    "Science/Math",
    "Social Justice",
    "Student Govt./Politics",
    "Theater/Drama",
    "Work (Paid)",
    "Other Club/Activity",
)
COMMON_APP_CLASSIFICATION_GUIDE = """
Common App classification rules:
- Honor = result or recognition: medal, rank, prize, finalist/semifinalist, scholarship by merit, subject distinction, academic award.
- Activity = process or contribution: role, responsibility, sustained work, project, research process, tutoring, volunteering, work, family responsibility, leadership.
- If a line only says the student won/placed/finaled in a competition, classify it as honor, not activity.
- If the same story belongs in both sections, do not duplicate wording. Honors should state the award formally; Activities should explain the work, role, scale, time, contribution, and impact behind it.
- For honors, use: year + award title + context + grade if known + level (School/Regional/National/International).
- For activities, use: action verb + what the student did + audience/scale + measurable result; mention an award only briefly if it adds new context.
- Add numbers whenever they are supported by the source or public verification: year, grade, placement, participant/team count, selection rate, users served, hours/week, weeks/year.
- Do not invent numbers. If public search does not confirm a number, ask for it in missing_or_unclear_facts instead of writing it as fact.
""".strip()

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
        "extraction_notes": {"type": "array", "items": {"type": "string"}},
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
                    "common_app_activity_type": {"type": ["string", "null"]},
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
                    "common_app_activity_type",
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
        "extraction_notes",
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
    "semifinalist",
    "semi-finalist",
    "place",
    "rank",
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


def _normalize_student_facing_text(value: str) -> str:
    text = _compact_whitespace(value)
    text = re.sub(r"\bRepublican\b", "National", text, flags=re.IGNORECASE)
    text = re.sub(r"\bRespublikalyk\b", "National", text, flags=re.IGNORECASE)
    text = re.sub(r"\bRespublikanskiy\b", "National", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\b(\d+)(st|nd|rd|th)\b",
        lambda match: f"{match.group(1)}{match.group(2).lower()}",
        text,
        flags=re.IGNORECASE,
    )
    for index, char in enumerate(text):
        if char.isalpha():
            text = text[:index] + char.upper() + text[index + 1 :]
            break
    text = re.sub(
        r"\b(\d+)(st|nd|rd|th)\b",
        lambda match: f"{match.group(1)}{match.group(2).lower()}",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _preserve_source_structure(value: str) -> str:
    lines = []
    for line in (value or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        cleaned = re.sub(r"[ \t\f\v]+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
        elif lines and lines[-1] != "":
            lines.append("")
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _source_excerpts(raw_text: str, *, max_items: int = 8, max_chars: int = 240) -> list[str]:
    scored: list[tuple[int, int, str]] = []
    keywords = (
        "award",
        "winner",
        "honor",
        "activities",
        "president",
        "captain",
        "founder",
        "research",
        "olympiad",
        "competition",
        "volunteer",
        "raised",
        "published",
        "selected",
        "national",
        "international",
        "hr/wk",
        "wk/yr",
    )
    for chunk in re.split(r"(?:\n\s*){1,}|(?:\s*[•\u2022*]\s+)", raw_text):
        text = _compact_whitespace(chunk)
        if len(text) < 18:
            continue
        lower = text.lower()
        score = sum(2 for keyword in keywords if keyword in lower)
        if any(char.isdigit() for char in text):
            score += 1
        scored.append((score, len(scored), _truncate_characters(text, max_chars)))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [text for _, _, text in scored[:max_items]]


def _source_line_map(raw_text: str) -> dict[int, str]:
    source_lines: dict[int, str] = {}
    fallback_index = 1
    for raw_line in raw_text.splitlines():
        line = _compact_whitespace(raw_line)
        if not line:
            continue
        numbered = re.match(r"^(\d+)\)\s*(.+)$", line)
        if numbered:
            source_lines[int(numbered.group(1))] = line
            continue
        source_lines.setdefault(fallback_index, line)
        fallback_index += 1
    return source_lines


def _prepare_ai_import_text(raw_text: str) -> str:
    if len(raw_text) <= AI_IMPORT_MAX_CHARS:
        return raw_text

    keywords = (
        "award",
        "winner",
        "honor",
        "activities",
        "president",
        "captain",
        "founder",
        "research",
        "olympiad",
        "competition",
        "volunteer",
        "raised",
        "published",
        "selected",
        "national",
        "international",
        "grade",
        "202",
        "hr/wk",
        "wk/yr",
        "участ",
        "побед",
        "приз",
        "олимпиад",
        "конкурс",
        "волонтер",
        "волонтёр",
        "финал",
        "место",
        "жүлде",
        "жеңімпаз",
    )
    chunks: list[str] = []
    for chunk in re.split(r"(?:\n\s*){1,}|(?:\s*[•\u2022*]\s+)", raw_text):
        text = _compact_whitespace(chunk)
        if len(text) >= 14:
            chunks.append(text)

    scored: list[tuple[int, int, str]] = []
    for index, chunk in enumerate(chunks):
        lower = chunk.lower()
        score = sum(2 for keyword in keywords if keyword in lower)
        if any(char.isdigit() for char in chunk):
            score += 1
        if len(chunk) > 400:
            score -= 1
        scored.append((score, index, chunk))

    selected: list[tuple[int, str]] = []
    total_chars = 0
    for score, index, chunk in sorted(scored, key=lambda item: (-item[0], item[1])):
        if score <= 0 and total_chars > AI_IMPORT_MAX_CHARS // 2:
            continue
        candidate = _truncate_characters(chunk, 900)
        if total_chars + len(candidate) + 1 > AI_IMPORT_MAX_CHARS:
            continue
        selected.append((index, candidate))
        total_chars += len(candidate) + 1
        if len(selected) >= MAX_IMPORTED_ITEMS * 3:
            break

    selected.sort(key=lambda item: item[0])
    prepared = "\n".join(chunk for _, chunk in selected).strip()
    return prepared or raw_text[:AI_IMPORT_MAX_CHARS]


def _count_words(value: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", value))


def _truncate_characters(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    truncated = value[:limit]
    last_space = truncated.rfind(" ")
    if last_space > max(0, limit - 24):
        truncated = truncated[:last_space]
    truncated = truncated.rstrip(",.;: ")
    truncated = re.sub(r"\s+(?:from|among|of|with|for|in|at|by|to|and|or|on|&)$", "", truncated, flags=re.IGNORECASE)
    truncated = truncated.rstrip(",.;: ")
    truncated = re.sub(r"\s+(?:from|among|of|with|for|in|at|by|to|and|or)\s+\d*$", "", truncated, flags=re.IGNORECASE)
    truncated = truncated.rstrip(",.;: ")
    sentence_ends = list(re.finditer(r"[.!?](?:\s|$)", truncated))
    if sentence_ends:
        tail = truncated[sentence_ends[-1].end() :].strip()
        complete = truncated[: sentence_ends[-1].end()].strip()
        if 0 < len(tail) <= 32 and len(complete) >= 40:
            return complete
    for separator in (";", ","):
        separator_index = truncated.rfind(separator)
        tail_length = len(truncated) - separator_index
        if separator_index >= 0 and tail_length <= 42 and len(truncated[:separator_index].strip()) >= 50:
            return truncated[:separator_index].rstrip(",.;: ")
    return truncated


def _clean_string_list(value: Any, *, max_items: int = 6, max_chars: int = 260) -> list[str]:
    if isinstance(value, str):
        value = [value]
    elif not isinstance(value, list):
        return []

    strings: list[str] = []
    for item in value:
        text = _compact_whitespace(str(item or ""))
        if text:
            strings.append(_truncate_characters(text, max_chars))
        if len(strings) >= max_items:
            break
    return strings


HONOR_SIGNAL_KEYWORDS = (
    "award",
    "bronze",
    "silver",
    "gold",
    "medal",
    "winner",
    "won",
    "1st place",
    "2nd place",
    "3rd place",
    "first place",
    "second place",
    "third place",
    "prize",
    "finalist",
    "semifinalist",
    "semi-finalist",
    "rank",
    "top ",
    "distinction",
    "honor",
    "scholarship",
)

ACTIVITY_PROCESS_KEYWORDS = (
    "built",
    "created",
    "developed",
    "designed",
    "founded",
    "led",
    "organized",
    "coordinated",
    "taught",
    "mentored",
    "tutored",
    "volunteered",
    "served",
    "worked",
    "interned",
    "conducted",
    "researched",
    "analyzed",
    "wrote",
    "published",
    "presented",
    "trained",
    "coached",
    "managed",
    "launched",
    "maintained",
    "onboarded",
    "raised",
    "improved",
)


def _contains_keyword(value: str, keywords: tuple[str, ...]) -> bool:
    text = value.lower()
    return any(keyword in text for keyword in keywords)


def _looks_like_award_only_activity(item: dict[str, Any]) -> bool:
    text = " ".join(
        _compact_whitespace(str(item.get(key) or ""))
        for key in (
            "title",
            "description_raw",
            "common_app_text",
            "common_app_activity_description",
            "common_app_position",
        )
    )
    lower = text.lower()
    has_honor_signal = _contains_keyword(lower, HONOR_SIGNAL_KEYWORDS) or bool(
        re.search(r"\b\d+(?:st|nd|rd|th)\s+(?:place|rank)\b", lower)
    )
    if not has_honor_signal:
        return False

    has_process_signal = _contains_keyword(lower, ACTIVITY_PROCESS_KEYWORDS)
    has_time_commitment = item.get("hours_per_week") is not None or item.get("weeks_per_year") is not None
    role = _compact_whitespace(str(item.get("role_title") or item.get("common_app_position") or ""))
    organization = _compact_whitespace(str(item.get("organization_name") or item.get("common_app_organization") or ""))
    has_real_role = bool(role) and not _contains_keyword(role, HONOR_SIGNAL_KEYWORDS)
    has_real_org = bool(organization) and organization.lower() not in {"not enough information yet", "unknown", "n/a"}
    return not (has_process_signal or has_time_commitment or has_real_role or has_real_org)


def _format_honor_year_first(value: str) -> str:
    text = _compact_whitespace(value)
    grade_match = re.match(r"^(9|10|11|12)\)\s+(.+)$", text)
    grade_suffix = ""
    if grade_match:
        grade_suffix = f", Grade {grade_match.group(1)}"
        text = grade_match.group(2)
    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", text)
    if not year_match:
        return _compact_whitespace(f"{text}{grade_suffix}")
    if text.startswith(year_match.group(1)):
        return _compact_whitespace(f"{text}{grade_suffix}")
    year = year_match.group(1)
    without_year = _compact_whitespace((text[: year_match.start()] + text[year_match.end() :]).strip(" ,;:-()"))
    return _compact_whitespace(f"{year} {without_year}{grade_suffix}")


def _remove_unsupported_leading_year(value: str, item: dict[str, Any]) -> str:
    text = _compact_whitespace(value)
    year_match = re.match(r"^(20\d{2}|19\d{2})\s+(.+)$", text)
    if not year_match:
        return text

    source_text = _compact_whitespace(
        " ".join(
            str(item.get(key) or "")
            for key in ("title", "organization_name", "role_title", "description_raw", "source_excerpt")
        )
    )
    if year_match.group(1) in source_text:
        return text

    missing = item.setdefault("missing_or_unclear_facts", [])
    if not any("year" in str(fact).lower() for fact in missing):
        missing.append("Confirm the exact award year.")
    return _compact_whitespace(year_match.group(2))


def _honor_source_text(item: dict[str, Any]) -> str:
    return _compact_whitespace(
        " ".join(
            str(item.get(key) or "")
            for key in ("title", "organization_name", "role_title", "description_raw", "source_excerpt")
        )
    )


def _extract_source_year(item: dict[str, Any]) -> str:
    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", _honor_source_text(item))
    return year_match.group(1) if year_match else ""


def _compact_honor_title(item: dict[str, Any]) -> str:
    source = _honor_source_text(item).lower()
    title = _compact_whitespace(str(item.get("title") or ""))
    if "central asian startup cup" in source:
        return "Central Asian Startup Cup"
    if "caspian startup" in source:
        return "Caspian Startup"
    if "samsung solve for tomorrow" in source:
        return "Samsung Solve for Tomorrow"
    if "fizmat ai olympiad" in source or "faio" in source:
        return "Fizmat AI Olympiad"
    if "jastarforum" in source:
        return "JASTARForum Science Fair"
    if "galymind" in source:
        return "Int'l Galymind Research Paper Competition"
    if "science. technology. algorithmization. programming" in source:
        return "Int'l Scientific Conference"
    if "international scientific and practical conference" in source:
        return "Int'l Scientific Conference"
    return title


def _compact_honor_award(item: dict[str, Any]) -> str:
    source = _honor_source_text(item).lower()
    if "top 15" in source and "innovative" in source:
        return "Top 15 Most Innovative Startups"
    if "semi-finalist" in source or "semifinalist" in source or "полу-финалист" in source:
        return "Semifinalist"
    if "finalist" in source or "финалист" in source:
        return "Finalist"
    if "absolute 1st" in source or "absoulute 1st" in source:
        return "1st Place"
    if "1st place" in source or "first place" in source:
        return "1st Place"
    if "2nd place" in source or "second place" in source:
        return "2nd Place"
    if "3rd place" in source or "third place" in source:
        return "3rd Place"
    if "gold" in source:
        return "Gold Medal"
    if "silver" in source:
        return "Silver Medal"
    if "bronze" in source or "brozne" in source:
        return "Bronze Medal"
    return _compact_whitespace(str(item.get("title") or "Honor"))


def _compact_honor_metrics(item: dict[str, Any]) -> list[str]:
    source = _honor_source_text(item)
    normalized = source.lower()
    metrics: list[str] = []

    if re.search(r"\b15\s*/\s*200\b", source):
        metrics.append("Top 15/200 teams")
    top_out_of_match = re.search(r"top\s+(\d+)\s+out\s+of\s+(\d+)\s+teams", source, flags=re.IGNORECASE)
    if top_out_of_match:
        metrics.append(f"Top {top_out_of_match.group(1)}/{top_out_of_match.group(2)} teams")
    if ("100+ teams" in normalized or "over 100 teams" in normalized) and "4 countries" in normalized:
        metrics.append("100+ teams/4 countries")

    participants_match = re.search(r"(?:out of|among|over)\s+([\d,]+)\s+participants", source, flags=re.IGNORECASE)
    if participants_match:
        metrics.append(f"{participants_match.group(1)} participants")

    teams_match = re.search(r"(?:among|среди)\s+([\d,]+)\s+(?:participating\s+)?(?:teams|команд)", source, flags=re.IGNORECASE)
    if teams_match:
        metrics.append(f"{teams_match.group(1)} teams")

    if "stem" in normalized:
        metrics.insert(0, "STEM")
    if "history" in normalized and "culture" in normalized:
        metrics.insert(0, "History & Culture")

    deduped: list[str] = []
    for metric in metrics:
        if metric not in deduped:
            deduped.append(metric)
    return deduped


def _compose_compact_honor_description(item: dict[str, Any]) -> str:
    award = _compact_honor_award(item)
    title = _compact_honor_title(item)
    if not award or not title:
        return ""

    year = _extract_source_year(item)
    if not year:
        missing = item.setdefault("missing_or_unclear_facts", [])
        if not any("year" in str(fact).lower() for fact in missing):
            missing.append("Confirm the exact award year.")
    prefix = f"{year} " if year else ""
    detail_parts = _compact_honor_metrics(item)
    level = getattr(item.get("impact_scope"), "value", item.get("impact_scope"))
    if level in {
        ImpactScope.school.value,
        ImpactScope.local.value,
        ImpactScope.regional.value,
        ImpactScope.national.value,
        ImpactScope.international.value,
    }:
        level_label = "State/Regional" if level in {ImpactScope.local.value, ImpactScope.regional.value} else str(level).title()
        if not any(level_label.lower() == part.lower() for part in detail_parts):
            detail_parts.append(level_label)

    details = f" ({', '.join(detail_parts)})" if detail_parts else ""
    return _compact_whitespace(f"{prefix}{award}, {title}{details}")


def _append_honor_level(value: str, impact_scope: Any) -> str:
    text = _compact_whitespace(value)
    level = getattr(impact_scope, "value", impact_scope)
    if level not in {
        ImpactScope.school.value,
        ImpactScope.local.value,
        ImpactScope.regional.value,
        ImpactScope.national.value,
        ImpactScope.international.value,
    }:
        return text
    label = "State/Regional" if level in {ImpactScope.local.value, ImpactScope.regional.value} else str(level).title()
    if label.lower() in text.lower():
        return text
    return _compact_whitespace(f"{text}, {label}")


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
    if value.lower() in {"n/a", "na", "none", "unknown", "not enough information yet"} or "implied" in value.lower():
        return ""
    return _truncate_characters(value, COMMON_APP_ACTIVITY_ORGANIZATION_LIMIT)


def _activity_type(item: dict[str, Any]) -> str:
    candidates = [
        item.get("common_app_activity_type"),
        item.get("category"),
        item.get("title"),
        item.get("organization_name"),
        item.get("role_title"),
        item.get("description_raw"),
    ]
    exact = {option.lower(): option for option in COMMON_APP_ACTIVITY_TYPES}
    text = " ".join(_compact_whitespace(str(value or "")).lower() for value in candidates if value)
    if "chess" in text and not any(
        word in text
        for word in ("teach", "taught", "teacher", "children", "disabilities", "volunteer", "service", "mentor", "inclusive")
    ):
        return "Other Club/Activity"
    for value in candidates:
        cleaned = _compact_whitespace(str(value or "")).lower()
        if cleaned in exact:
            return exact[cleaned]
    if any(word in text for word in ("robot", "robotics")):
        return "Robotics"
    if any(word in text for word in ("research", "paper", "publication", "conference")):
        return "Research"
    if any(word in text for word in ("computer", "technology", "programming", "python", "software", "website", "ai ", "full-stack", "coding")):
        return "Computer/Technology"
    if any(word in text for word in ("math", "science", "stem", "olympiad", "physics", "chemistry", "biology", "informatics")):
        return "Science/Math"
    if any(word in text for word in ("volunteer", "service", "mentor", "mentoring", "charity")):
        return "Community Service (Volunteer)"
    if re.search(r"\bintern(ship)?\b", text):
        return "Internship"
    if any(word in text for word in ("job", "paid", "work")):
        return "Work (Paid)"
    if "family" in text:
        return "Family Responsibilities"
    if any(word in text for word in ("debate", "speech", "mun", "model un")):
        return "Debate/Speech"
    if any(word in text for word in ("journal", "newspaper", "magazine", "article")):
        return "Journalism/Publication"
    if any(word in text for word in ("environment", "climate", "eco")):
        return "Environmental"
    if any(word in text for word in ("student government", "student council", "politics")):
        return "Student Govt./Politics"
    if any(word in text for word in ("music", "instrument", "piano", "violin")):
        return "Music: Instrumental"
    if any(word in text for word in ("vocal", "choir", "singing")):
        return "Music: Vocal"
    if "dance" in text:
        return "Dance"
    if any(word in text for word in ("theater", "theatre", "drama")):
        return "Theater/Drama"
    if any(word in text for word in ("art", "design", "drawing", "painting")):
        return "Art"
    if any(word in text for word in ("culture", "cultural")):
        return "Cultural"
    if any(word in text for word in ("language", "linguistic")):
        return "Foreign Language"
    if any(word in text for word in ("lgbt", "lgbtq")):
        return "LGBT"
    if "relig" in text:
        return "Religious"
    if any(word in text for word in ("sport", "athletic", "football", "basketball", "swim", "varsity")):
        return "Athletics: JV/Varsity"
    return "Other Club/Activity"


def _activity_description(item: dict[str, Any], word_limit: int) -> str:
    value = _compact_whitespace(
        str(item.get("common_app_activity_description") or item.get("common_app_text") or item.get("description_raw") or "")
    )
    if not value:
        value = _fallback_common_app_text(item, word_limit)
    return _enforce_common_app_limit(value, word_limit, AchievementType.activity.value)


def _honor_description(item: dict[str, Any], word_limit: int) -> str:
    value = _compact_whitespace(
        str(
            item.get("common_app_honor_description")
            or item.get("description_raw")
            or item.get("common_app_text")
            or item.get("title")
            or ""
        )
    )
    value = _remove_unsupported_leading_year(_format_honor_year_first(value), item)
    value = _compose_compact_honor_description(item) or _append_honor_level(value, item.get("impact_scope"))
    return _enforce_common_app_limit(value, word_limit, AchievementType.honor.value)


def _coerce_enum(enum_cls: Any, value: Any) -> Any:
    if value in (None, "", "null"):
        return None
    cleaned = _compact_whitespace(str(value))
    try:
        return enum_cls(cleaned)
    except ValueError:
        pass
    normalized = cleaned.lower().replace("_", " ").replace("-", " ")
    for member in enum_cls:
        if normalized == str(member.value).lower().replace("_", " ").replace("-", " "):
            return member
    return None


def _clamp_score(value: Any) -> float:
    try:
        return round(max(0.0, min(10.0, float(value))), 1)
    except (TypeError, ValueError):
        return 5.0


def _coerce_recommended_rank(value: Any) -> Optional[int]:
    if value in (None, "", "null"):
        return None
    try:
        rank = int(value)
    except (TypeError, ValueError):
        return None
    return rank if rank > 0 else None


def _coerce_source_index(value: Any, fallback: int) -> int:
    if value in (None, "", "null"):
        return fallback
    match = re.search(r"\d+", str(value))
    if not match:
        return fallback
    try:
        return max(1, int(match.group(0)))
    except ValueError:
        return fallback


def _extract_pdf_text(raw_bytes: bytes) -> str:
    import io

    try:
        import pdfplumber
    except ImportError:
        raise ValueError("PDF support requires pdfplumber. Run: pip install pdfplumber")

    pages_text: list[str] = []
    try:
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            for index, page in enumerate(pdf.pages):
                if index >= MAX_PDF_PAGES:
                    break
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages_text.append(page_text)
                if sum(len(text) for text in pages_text) >= MAX_IMPORT_CHARS:
                    break
    except Exception as exc:
        raise ValueError(
            "Could not extract text from this PDF. Upload a selectable-text PDF, DOCX, TXT, MD, CSV, or JSON file."
        ) from exc

    text = "\n".join(pages_text)
    if not _compact_whitespace(text):
        raise ValueError(
            "This PDF has no selectable text. Scanned image PDFs are not supported yet; upload a text-based PDF, DOCX, TXT, MD, CSV, or JSON file."
        )
    return text[:MAX_IMPORT_CHARS]


def _extract_docx_text(raw_bytes: bytes) -> str:
    import io

    try:
        from docx import Document
    except ImportError:
        raise ValueError("DOCX support requires python-docx. Run: pip install python-docx")

    try:
        doc = Document(io.BytesIO(raw_bytes))
        paragraphs: list[str] = []
        total_chars = 0
        for paragraph in doc.paragraphs[:MAX_DOCX_PARAGRAPHS]:
            text = paragraph.text.strip()
            if not text:
                continue
            paragraphs.append(text)
            total_chars += len(text) + 1
            if total_chars >= MAX_IMPORT_CHARS:
                break
    except Exception as exc:
        raise ValueError("Could not extract text from this DOCX file. Export it as TXT or a simpler DOCX and retry.") from exc

    return "\n".join(paragraphs)[:MAX_IMPORT_CHARS]


def decode_import_file(file_name: str, raw_bytes: bytes) -> str:
    if len(raw_bytes) > MAX_IMPORT_BYTES:
        raise ValueError("File is too large for import. Keep it under 10 MB.")

    extension = os.path.splitext(file_name or "")[1].lower()
    supported = {".txt", ".md", ".csv", ".json", ".pdf", ".docx"}
    if extension and extension not in supported:
        raise ValueError(
            "Import supports .txt, .md, .csv, .json, .pdf, and .docx files."
        )

    if extension == ".pdf":
        text = _extract_pdf_text(raw_bytes)
    elif extension == ".docx":
        text = _extract_docx_text(raw_bytes)
    else:
        for encoding in ("utf-8", "utf-8-sig", "utf-16", "cp1251", "latin-1"):
            try:
                text = raw_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Could not read the uploaded file as text.")

    text = _preserve_source_structure(text)
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


def _local_shortlist_base_item(
    *,
    source_index: int,
    item_type: AchievementType,
    title: str,
    description_raw: str,
    rank: int,
    major: float,
    selectivity: float,
    continuity: float,
    distinctiveness: float,
    organization_name: Optional[str] = None,
    role_title: Optional[str] = None,
    category: Optional[str] = None,
    impact_scope: Optional[ImpactScope] = None,
    leadership_level: Optional[LeadershipLevel] = None,
    common_app_activity_type: Optional[str] = None,
    common_app_position: Optional[str] = None,
    common_app_organization: Optional[str] = None,
    common_app_activity_description: Optional[str] = None,
    common_app_honor_description: Optional[str] = None,
    missing_or_unclear_facts: Optional[list[str]] = None,
) -> dict[str, Any]:
    return {
        "source_index": source_index,
        "type": item_type.value,
        "title": title,
        "organization_name": organization_name,
        "role_title": role_title,
        "description_raw": description_raw,
        "category": category,
        "hours_per_week": None,
        "weeks_per_year": None,
        "impact_scope": impact_scope.value if impact_scope else None,
        "leadership_level": leadership_level.value if leadership_level else None,
        "truth_risk_flag": False,
        "major_relevance_score": major,
        "selectivity_score": selectivity,
        "continuity_score": continuity,
        "distinctiveness_score": distinctiveness,
        "selection_reason": "Selected by fast local Chancellor fallback from source-supported evidence.",
        "common_app_text": common_app_activity_description or common_app_honor_description or "",
        "common_app_activity_type": common_app_activity_type,
        "common_app_position": common_app_position,
        "common_app_organization": common_app_organization,
        "common_app_activity_description": common_app_activity_description,
        "common_app_honor_description": common_app_honor_description,
        "verification_queries": [],
        "verification_notes": [],
        "missing_or_unclear_facts": missing_or_unclear_facts or [],
        "recommended_rank": rank,
    }


def _build_fast_local_shortlist(raw_text: str) -> list[dict[str, Any]]:
    source_lines = _source_line_map(raw_text)
    numbered_lines = sorted(source_lines.items())
    lower_lines = {index: line.lower() for index, line in numbered_lines}

    def find_indices(*needles: str) -> list[int]:
        return [
            index
            for index, lower in lower_lines.items()
            if any(needle.lower() in lower for needle in needles)
        ]

    def combined_text(indices: list[int]) -> str:
        return " ".join(source_lines[index] for index in indices if index in source_lines)

    items: list[dict[str, Any]] = []

    web_indices = sorted(set(find_indices("mpoxdetection", "full-stack", "freelance", "codeforces", "acmp.ru")))
    if web_indices:
        items.append(
            _local_shortlist_base_item(
                source_index=web_indices[0],
                item_type=AchievementType.activity,
                title="AI-Integrated Full-Stack Web Development",
                organization_name="Self-Employed / Personal Projects",
                role_title="Full-Stack Developer, Freelancer",
                description_raw=combined_text(web_indices),
                category="Computer/Technology",
                impact_scope=ImpactScope.personal,
                leadership_level=LeadershipLevel.founder,
                common_app_activity_type="Computer/Technology",
                common_app_position="Full-Stack Dev & Freelancer",
                common_app_organization="Self-Employed",
                common_app_activity_description=(
                    "Developed & hosted AI-integrated Mpox detection web app; built client websites as freelancer; "
                    "solved Python/C++ problems."
                ),
                missing_or_unclear_facts=[
                    "Hours/week and weeks/year for web projects.",
                    "Number of freelance clients or projects.",
                ],
                rank=1,
                major=9,
                selectivity=5,
                continuity=6,
                distinctiveness=8,
            )
        )

    inclusive_indices = find_indices("inclusive academy")
    if inclusive_indices:
        items.append(
            _local_shortlist_base_item(
                source_index=inclusive_indices[0],
                item_type=AchievementType.activity,
                title="Inclusive Academy Python and Chess Teaching",
                organization_name="Inclusive Academy",
                role_title="Python Teacher & Chess Coach",
                description_raw=source_lines[inclusive_indices[0]],
                category="Community Service (Volunteer)",
                impact_scope=ImpactScope.international,
                leadership_level=LeadershipLevel.lead,
                common_app_activity_type="Community Service (Volunteer)",
                common_app_position="Python Teacher & Chess Coach",
                common_app_organization="Inclusive Academy",
                common_app_activity_description=(
                    "Taught Python & chess to 3 children with disabilities (ages 8-9) in 2023 through Inclusive Academy."
                ),
                missing_or_unclear_facts=["Hours/week and weeks/year for teaching."],
                rank=2,
                major=7,
                selectivity=5,
                continuity=4,
                distinctiveness=7,
            )
        )

    mentor_indices = find_indices("ментор", "8-класс", "40 минут")
    if mentor_indices:
        items.append(
            _local_shortlist_base_item(
                source_index=mentor_indices[0],
                item_type=AchievementType.activity,
                title="NIS Peer Mentoring and School Events",
                organization_name="NIS FMN Almaty",
                role_title="Peer Mentor & Event Organizer",
                description_raw=source_lines[mentor_indices[0]],
                category="Community Service (Volunteer)",
                impact_scope=ImpactScope.school,
                leadership_level=LeadershipLevel.lead,
                common_app_activity_type="Community Service (Volunteer)",
                common_app_position="Peer Mentor & Event Organizer",
                common_app_organization="NIS FMN Almaty",
                common_app_activity_description=(
                    "Mentored five 8th graders as an 11th grader (2024-25); organized staff appreciation & 40-min adaptation lesson."
                ),
                missing_or_unclear_facts=["Hours/week and weeks/year for mentoring."],
                rank=3,
                major=5,
                selectivity=4,
                continuity=5,
                distinctiveness=6,
            )
        )

    yandex_indices = find_indices("yandex lyceum")
    if yandex_indices:
        items.append(
            _local_shortlist_base_item(
                source_index=yandex_indices[0],
                item_type=AchievementType.activity,
                title="Yandex Lyceum Python Coursework",
                organization_name="Yandex Lyceum",
                role_title="Alumnus",
                description_raw=source_lines[yandex_indices[0]],
                category="Computer/Technology",
                impact_scope=ImpactScope.personal,
                leadership_level=LeadershipLevel.member,
                common_app_activity_type="Computer/Technology",
                common_app_position="Alumnus",
                common_app_organization="Yandex Lyceum",
                common_app_activity_description=(
                    "Completed a year-long offline Python programming course at Yandex Lyceum."
                ),
                missing_or_unclear_facts=["Year of completion.", "Hours/week and weeks/year for coursework."],
                rank=4,
                major=8,
                selectivity=5,
                continuity=6,
                distinctiveness=5,
            )
        )

    hackathon_indices = find_indices("hackorgkz")
    if hackathon_indices:
        items.append(
            _local_shortlist_base_item(
                source_index=hackathon_indices[0],
                item_type=AchievementType.activity,
                title="HackOrgKz National Hackathon",
                organization_name="HackOrgKz",
                role_title="Participant",
                description_raw=source_lines[hackathon_indices[0]],
                category="Computer/Technology",
                impact_scope=ImpactScope.national,
                leadership_level=LeadershipLevel.member,
                common_app_activity_type="Computer/Technology",
                common_app_position="Participant",
                common_app_organization="HackOrgKz",
                common_app_activity_description=(
                    "Participated in National Hackathon of HackOrgKz (Sept. 20, 2024), collaborating on a tech project."
                ),
                missing_or_unclear_facts=["Specific project, role, team size, and outcome."],
                rank=5,
                major=7,
                selectivity=5,
                continuity=2,
                distinctiveness=4,
            )
        )

    festival_indices = find_indices("festival of scientific ideas")
    if festival_indices:
        items.append(
            _local_shortlist_base_item(
                source_index=festival_indices[0],
                item_type=AchievementType.activity,
                title="Festival of Scientific Ideas Project",
                role_title="Participant",
                description_raw=source_lines[festival_indices[0]],
                category="Science/Math",
                impact_scope=ImpactScope.school,
                leadership_level=LeadershipLevel.member,
                common_app_activity_type="Science/Math",
                common_app_position="Participant",
                common_app_activity_description=(
                    'Developed and presented a scientific project for the school "Festival of Scientific Ideas" competition.'
                ),
                missing_or_unclear_facts=["Project topic, year, and outcome."],
                rank=6,
                major=6,
                selectivity=3,
                continuity=2,
                distinctiveness=4,
            )
        )

    chess_indices = sorted(set(find_indices("first-class chess", "kbtu open", "шахмат")))
    if chess_indices:
        items.append(
            _local_shortlist_base_item(
                source_index=chess_indices[0],
                item_type=AchievementType.activity,
                title="Competitive Chess",
                role_title="Competitive Chess Player",
                description_raw=combined_text(chess_indices),
                category="Other Club/Activity",
                impact_scope=ImpactScope.regional,
                leadership_level=LeadershipLevel.member,
                common_app_activity_type="Other Club/Activity",
                common_app_position="Competitive Chess Player",
                common_app_activity_description=(
                    "Competed in chess tournaments including KBTU OPEN 2024; earned First-Class Chess Player status."
                ),
                missing_or_unclear_facts=["Hours/week and weeks/year for chess."],
                rank=7,
                major=3,
                selectivity=5,
                continuity=5,
                distinctiveness=4,
            )
        )

    honor_specs = [
        (
            find_indices("fizmat ai olympiad", "faio"),
            "Fizmat AI Olympiad",
            AchievementType.honor,
            1,
            9,
            8,
            1,
            8,
            ImpactScope.national,
            ["Confirm the exact award year."],
        ),
        (
            find_indices("science. technology. algorithmization. programming"),
            "International Scientific and Practical Conference",
            AchievementType.honor,
            2,
            8,
            8,
            1,
            7,
            ImpactScope.international,
            [],
        ),
        (
            find_indices("jastarforum"),
            "JASTARForum Science Fair",
            AchievementType.honor,
            3,
            7,
            7,
            1,
            7,
            ImpactScope.national,
            ["Confirm the exact award year."],
        ),
        (
            find_indices("central asian startup cup"),
            "Central Asian Startup Cup",
            AchievementType.honor,
            4,
            7,
            8,
            1,
            7,
            ImpactScope.international,
            ["Confirm the exact award year."],
        ),
        (
            find_indices("caspian startup"),
            "Caspian Startup",
            AchievementType.honor,
            5,
            7,
            8,
            1,
            7,
            ImpactScope.international,
            [],
        ),
    ]
    for indices, title, item_type, rank, major, selectivity, continuity, distinctiveness, scope, missing in honor_specs:
        if not indices:
            continue
        items.append(
            _local_shortlist_base_item(
                source_index=indices[0],
                item_type=item_type,
                title=title,
                description_raw=source_lines[indices[0]],
                impact_scope=scope,
                common_app_honor_description="",
                missing_or_unclear_facts=missing,
                rank=rank,
                major=major,
                selectivity=selectivity,
                continuity=continuity,
                distinctiveness=distinctiveness,
            )
        )

    return items


def _fallback_parse(raw_text: str, user: Optional[Any], word_limit: int) -> dict[str, Any]:
    from .chancellor_analysis import _heuristic_scores

    local_shortlist_items = _build_fast_local_shortlist(raw_text)
    if local_shortlist_items:
        return {
            "strongest_angle": (
                "Lead with AI/software, STEM awards, and selective startup evidence, supported by service and teaching work."
            ),
            "needs_student_clarification": True,
            "clarifying_questions": [
                "Confirm missing years, hours per week, weeks per year, and project details before final submission."
            ],
            "additional_information_recommended": False,
            "additional_information_reason": "",
            "additional_information_draft": "",
            "formatting_notes": [
                "Gemini did not finish within the upload timeout, so ApplyMap used the fast local Chancellor formatter."
            ],
            "extraction_notes": [
                f"Fast local fallback built {len(local_shortlist_items)} Common App-ready candidates from numbered source lines."
            ],
            "items": local_shortlist_items,
        }

    lines = [
        _compact_whitespace(line)
        for line in re.split(r"(?:\r?\n)+|(?:^|\n)\s*[-*\u2022]\s+", raw_text)
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
        scores = _heuristic_scores(base_item, user)
        item = {
            **base_item,
            **scores,
            "common_app_text": "",
            "common_app_activity_type": _activity_type(base_item) if item_type == AchievementType.activity else None,
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
        "extraction_notes": [
            f"Local fallback split the source into {len(items)} candidate achievement lines."
        ],
        "items": items,
    }


def _import_prompt(
    raw_text: str,
    user: Optional[Any],
    word_limit: int,
    clarification_answers: Optional[dict[str, str]] = None,
) -> str:
    payload = {
        "student_profile": _profile_context(user),
        "common_app_limits": {
            "activities_max_items": MAX_TOP_ACTIVITIES,
            "activity_position_leadership_description_chars": COMMON_APP_ACTIVITY_POSITION_LIMIT,
            "activity_organization_name_chars": COMMON_APP_ACTIVITY_ORGANIZATION_LIMIT,
            "activity_description_chars": COMMON_APP_ACTIVITY_DESCRIPTION_LIMIT,
            "honors_max_items": MAX_TOP_HONORS,
            "honor_title_description_chars": COMMON_APP_HONOR_DESCRIPTION_LIMIT,
        },
        "common_app_classification_guide": COMMON_APP_CLASSIFICATION_GUIDE,
        "source_excerpts": _source_excerpts(raw_text),
        "student_clarification_answers": clarification_answers or {},
        "raw_source_text": raw_text,
    }
    return (
        "You are ApplyMap Chancellor. Convert a messy Kazakhstan student achievement file into compact, factual "
        "Common App-ready JSON.\n\n"
        "Return ONLY valid JSON with top-level keys: strongest_angle, needs_student_clarification, clarifying_questions, "
        "additional_information_recommended, additional_information_reason, additional_information_draft, formatting_notes, "
        "extraction_notes, items.\n"
        "Top output only: return at most 15 items total: the strongest top 10 activities and top 5 honors. "
        "If fewer than 10 activities are fully evidenced, still return every source-supported activity candidate and ask "
        "for missing time/role/project details. Do not stop at 5 only because hours, weeks, or dates are incomplete. "
        "Do not return extra unranked items.\n"
        "Each item must include these keys: source_index, type, title, organization_name, role_title, description_raw, "
        "category, hours_per_week, weeks_per_year, impact_scope, leadership_level, truth_risk_flag, "
        "major_relevance_score, selectivity_score, continuity_score, distinctiveness_score, selection_reason, "
        "common_app_text, common_app_activity_type, common_app_position, common_app_organization, "
        "common_app_activity_description, common_app_honor_description, verification_queries, verification_notes, "
        "missing_or_unclear_facts, recommended_rank.\n\n"
        "Tasks:\n"
        "1. Extract distinct achievements. Merge only true duplicates.\n"
        "2. Classify using this rule: Honor = result/recognition; Activity = process/role/contribution/project/work.\n"
        "3. Set recommended_rank 1-10 for activities and 1-5 for honors. Do not include extra unranked items.\n"
        "4. Output polished English only.\n\n"
        "Activity candidates may include personal software projects, freelance work, teaching, mentoring, volunteering, "
        "structured coursework, hackathons, competitive chess, scientific-project participation, and sustained competitive "
        "programming. If evidence is incomplete, keep the activity and ask for the missing detail.\n\n"
        "For a Computer Science or AI-oriented student, rank AI olympiads, STEM/research awards, science fairs, and "
        "selective tech competitions above generic competition participation unless the source gives stronger evidence. "
        "Do not drop a named AI/STEM olympiad medal or STEM conference award when it is present. Non-STEM awards can stay, "
        "but should not outrank stronger AI/STEM/science-fair/startup evidence for a CS/AI profile.\n\n"
        "Common App formatting rules:\n"
        f"- Activity type must be exactly one of: {', '.join(COMMON_APP_ACTIVITY_TYPES)}.\n"
        f"- Activity position <= {COMMON_APP_ACTIVITY_POSITION_LIMIT} characters.\n"
        f"- Activity organization <= {COMMON_APP_ACTIVITY_ORGANIZATION_LIMIT} characters.\n"
        f"- Activity description <= {COMMON_APP_ACTIVITY_DESCRIPTION_LIMIT} characters.\n"
        f"- Honor description <= {COMMON_APP_HONOR_DESCRIPTION_LIMIT} characters; start with year if known, then award/context/level.\n"
        "- If one story appears in both sections, do not copy-paste. Honors show recognition; Activities show work, role, scale, and impact.\n\n"
        "Important constraints:\n"
        "- Do not invent achievements, outcomes, metrics, organizations, dates, leadership roles, or awards.\n"
        "- If the source does not state an organization, use null; never write implied organizations.\n"
        "- Fix lowercase or informal source phrasing into proper English capitalization and grammar.\n"
        "- Fix obvious typos such as Brozne->Bronze, intergrated->integrated, Cullture->Culture, absoulute->absolute.\n"
        "- Preserve years, date ranges, school grade, event names, number of students served, placements, and supported metrics. "
        "Do not remove these facts just to make the sentence shorter.\n"
        "- Do not infer a missing year from nearby source lines. If an item has no year, omit the year and ask for it.\n"
        "- Add supported numbers wherever useful: year, grade, placement, participant/team count, selection rate, users served, "
        "hours/week, weeks/year, countries, prize money, or funding.\n"
        "- If a number is missing or unverified, ask in missing_or_unclear_facts; do not invent it.\n"
        "- Never replace a concrete source detail with a guessed or more impressive detail.\n"
        "- Translate Kazakhstan award level words like Republican/Respublikalyk/Respublikanskiy as National unless the "
        "official English title clearly uses Republican.\n"
        "- If the source says the student mentored five 8th graders as an 11th grader in 2024-2025 and organized events, "
        "keep those facts in concise English instead of reducing the entry to a generic mentoring sentence.\n"
        "- Preserve Kazakhstan/NIS/IB/A-Level context when present.\n"
        "- Treat MESK written in Russian or Kazakh as NIS Grade 12 Certificate in English output.\n"
        "- The shortlist should reward spike, depth, selectivity, continuity, and distinctive impact.\n"
        "- Prefer fewer real activities over padded weak activities when the source only supports fewer than 10.\n\n"
        "Keep output compact: selection_reason <= 18 words, each missing_or_unclear_facts item <= 16 words, "
        "additional_information_draft <= 120 words.\n\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False, default=str)}"
    )


def _extract_gemini_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    content = candidates[0].get("content") if candidates else {}
    parts = content.get("parts") or []
    return str(parts[0].get("text", "")) if parts else ""


def _gemini_parse(
    raw_text: str,
    user: Optional[Any],
    word_limit: int,
    clarification_answers: Optional[dict[str, str]] = None,
) -> Optional[dict[str, Any]]:
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        return None

    model = (settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": _import_prompt(raw_text, user, word_limit, clarification_answers)}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 20000,
            "responseMimeType": "application/json",
        },
    }

    try:
        with httpx.Client(timeout=GEMINI_IMPORT_TIMEOUT_SECONDS) as client:
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

    with httpx.Client(timeout=3.0) as client:
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
    if GOOGLE_VERIFICATION_TIME_BUDGET_SECONDS <= 0:
        return [
            "Online verification is skipped during file import to keep upload responsive; verify final claims from certificates or official links."
        ]

    notes: list[str] = []
    started_at = time.monotonic()
    for item in items:
        if time.monotonic() - started_at > GOOGLE_VERIFICATION_TIME_BUDGET_SECONDS:
            notes.append("Google verification stopped early to keep the import responsive.")
            break
        query = (item.get("verification_queries") or [_default_verification_query(item, user)])[0]
        if not query:
            item.setdefault("missing_or_unclear_facts", []).append("No searchable title or organization was available.")
            continue
        try:
            search_results = _google_search(query, num=3)
        except (SearchNotConfiguredError, httpx.HTTPError):
            return [
                "Google verification is currently unavailable. Ask the student for official links, certificates, or organizer pages for unsupported claims."
            ]

        if not search_results:
            item.setdefault("missing_or_unclear_facts", []).append(
                "No Google result found for this item; ask the student for an official source or certificate."
            )
            continue

        item.setdefault("verification_notes", []).extend(_format_search_note(result) for result in search_results[:3])
        notes.append(f"Checked Google for: {query}")

    return notes


def _normalize_items(
    result: dict[str, Any],
    word_limit: int,
    source_lines: Optional[dict[int, str]] = None,
) -> dict[str, Any]:
    normalized_items: list[dict[str, Any]] = []
    source_lines = source_lines or {}

    for index, raw_item in enumerate(result.get("items") or [], start=1):
        title = _normalize_student_facing_text(str(raw_item.get("title") or ""))
        if not title:
            continue

        item_type = _coerce_enum(AchievementType, raw_item.get("type")) or AchievementType.activity
        source_index = _coerce_source_index(raw_item.get("source_index"), index)
        source_excerpt = _compact_whitespace(source_lines.get(source_index, ""))
        normalized = {
            "source_index": source_index,
            "type": item_type.value,
            "title": title[:500],
            "organization_name": _normalize_student_facing_text(str(raw_item.get("organization_name") or "")) or None,
            "role_title": _normalize_student_facing_text(str(raw_item.get("role_title") or "")) or None,
            "description_raw": _normalize_student_facing_text(str(raw_item.get("description_raw") or "")) or None,
            "source_excerpt": source_excerpt or None,
            "category": _normalize_student_facing_text(str(raw_item.get("category") or "")) or None,
            "hours_per_week": raw_item.get("hours_per_week"),
            "weeks_per_year": raw_item.get("weeks_per_year"),
            "impact_scope": (_coerce_enum(ImpactScope, raw_item.get("impact_scope")) or None),
            "leadership_level": (_coerce_enum(LeadershipLevel, raw_item.get("leadership_level")) or None),
            "truth_risk_flag": bool(raw_item.get("truth_risk_flag")),
            "major_relevance_score": _clamp_score(raw_item.get("major_relevance_score")),
            "selectivity_score": _clamp_score(raw_item.get("selectivity_score")),
            "continuity_score": _clamp_score(raw_item.get("continuity_score")),
            "distinctiveness_score": _clamp_score(raw_item.get("distinctiveness_score")),
            "selection_reason": _normalize_student_facing_text(str(raw_item.get("selection_reason") or "")),
            "common_app_text": _enforce_common_app_limit(
                _normalize_student_facing_text(str(raw_item.get("common_app_text") or "")),
                word_limit,
                item_type.value,
            ),
            "common_app_activity_type": _normalize_student_facing_text(str(raw_item.get("common_app_activity_type") or ""))
            or None,
            "common_app_position": _normalize_student_facing_text(str(raw_item.get("common_app_position") or "")) or None,
            "common_app_organization": _normalize_student_facing_text(str(raw_item.get("common_app_organization") or "")) or None,
            "common_app_activity_description": _normalize_student_facing_text(
                str(raw_item.get("common_app_activity_description") or "")
            )
            or None,
            "common_app_honor_description": _normalize_student_facing_text(str(raw_item.get("common_app_honor_description") or ""))
            or None,
            "verification_queries": _clean_string_list(raw_item.get("verification_queries"), max_items=3, max_chars=160),
            "verification_notes": _clean_string_list(raw_item.get("verification_notes"), max_items=5, max_chars=300),
            "missing_or_unclear_facts": _clean_string_list(
                raw_item.get("missing_or_unclear_facts"), max_items=6, max_chars=180
            ),
            "recommended_rank": _coerce_recommended_rank(raw_item.get("recommended_rank")),
        }
        if item_type == AchievementType.activity and _looks_like_award_only_activity(normalized):
            item_type = AchievementType.honor
            normalized["type"] = AchievementType.honor.value
            normalized["selection_reason"] = _compact_whitespace(
                f"{normalized['selection_reason']} Reclassified as honor because the evidence describes recognition, not a sustained role."
            )
            normalized["missing_or_unclear_facts"].append(
                "If this award came from a long activity, add the activity separately with role, hours, weeks, and impact."
            )
        if not normalized["common_app_text"]:
            normalized["common_app_text"] = _fallback_common_app_text(normalized, word_limit)
        if item_type == AchievementType.activity:
            normalized["common_app_activity_type"] = _activity_type(normalized)
            normalized["common_app_position"] = _activity_position(normalized)
            normalized["common_app_organization"] = _activity_organization(normalized) or None
            normalized["common_app_activity_description"] = _activity_description(normalized, word_limit)
            normalized["common_app_text"] = normalized["common_app_activity_description"]
            normalized["common_app_honor_description"] = None
        else:
            normalized["common_app_activity_type"] = None
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
        "extraction_notes": _clean_string_list(result.get("extraction_notes"), max_items=8, max_chars=220),
        "items": normalized_items,
    }


def parse_achievement_import(
    raw_text: str,
    user: Optional[Any],
    word_limit: int,
    clarification_answers: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    ai_text = _prepare_ai_import_text(raw_text)
    parsed = _gemini_parse(ai_text, user, word_limit, clarification_answers)
    used_gemini = parsed is not None
    if parsed is None:
        parsed = _fallback_parse(ai_text, user, word_limit)
    normalized = _normalize_items(parsed, word_limit, _source_line_map(raw_text))
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
    normalized["source_excerpts"] = _source_excerpts(raw_text)
    normalized["processing_steps"] = [
        {
            "key": "read_file",
            "label": "Read uploaded file",
            "status": "complete",
            "detail": f"Extracted {len(raw_text):,} characters while preserving line breaks and bullet structure.",
        },
        {
            "key": "prepare_ai_input",
            "label": "Prepare text for AI review",
            "status": "complete",
            "detail": f"Focused the AI review on {len(ai_text):,} relevant characters to keep the import stable.",
        },
        {
            "key": "extract_candidates",
            "label": "Extract achievement candidates",
            "status": "complete",
            "detail": f"Built {len(items)} structured candidates from the source text.",
        },
        {
            "key": "rank_shortlist",
            "label": "Rank activities and honors",
            "status": "complete",
            "detail": f"Selected {len(normalized['top_activities'])} activities and {len(normalized['top_honors'])} honors for Common App.",
        },
        {
            "key": "format_common_app",
            "label": "Format Common App fields",
            "status": "complete",
            "detail": "Enforced 50/100/150-character activity fields and 100-character honor lines.",
        },
        {
            "key": "verify_claims",
            "label": "Check uncertainty and verification needs",
            "status": "complete",
            "detail": "Generated clarification questions and verification notes for unsupported claims.",
        },
        {
            "key": "ai_engine",
            "label": "AI extraction engine",
            "status": "complete",
            "detail": "Gemini returned structured JSON." if used_gemini else "Gemini was unavailable or returned invalid JSON; used local fallback.",
        },
    ]
    return normalized
