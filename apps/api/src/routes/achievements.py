import json
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from uuid import UUID

from ..database import get_db
from ..schemas.achievement import (
    AchievementCreate,
    AchievementUpdate,
    AchievementOut,
    EvidenceFileOut,
    AchievementImportOut,
    AchievementShortlistRequest,
)
from ..models.achievement import Achievement, AchievementEvidenceFile, AchievementType
from ..routes.auth import get_current_user
from ..services.chancellor_analysis import estimate_chancellor_scores
from ..services.achievement_import_service import decode_import_file, parse_achievement_import

router = APIRouter(prefix="/api/achievements", tags=["achievements"])

ACTIVITY_POSITION_LIMIT = 50
ACTIVITY_ORGANIZATION_LIMIT = 100
ACTIVITY_DESCRIPTION_LIMIT = 150
HONOR_DESCRIPTION_LIMIT = 100
TOP_ACTIVITY_LIMIT = 10
TOP_HONOR_LIMIT = 5
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

CYRILLIC_TRANSLATIONS = (
    (r"оффлайн\s+год\s+обучения\s+языку\s+программирования\s+python", "offline Python programming year"),
    (r"год\s+обучения\s+языку\s+программирования\s+python", "Python programming year"),
    (r"языку\s+программирования\s+python", "Python programming"),
    (r"был\s+личным\s+ментором", "mentored"),
    (r"личным\s+ментором", "mentor"),
    (r"пятерых", "5"),
    (r"8-?классникам", "8th-graders"),
    (r"11\s+классником", "11th-grader"),
    (r"организовали", "organized"),
    (r"главных\s+ивента", "main events"),
    (r"подарочные\s+открытки", "greeting cards"),
    (r"финалист", "Finalist"),
    (r"полуфиналист", "Semifinalist"),
    (r"победитель", "Winner"),
    (r"бронз[а-я]*", "Bronze"),
    (r"серебр[а-я]*", "Silver"),
    (r"золот[а-я]*", "Gold"),
    (r"республиканск[а-я]*", "National"),
    (r"национальн[а-я]*", "National"),
    (r"международн[а-я]*", "International"),
    (r"областн[а-я]*", "Regional"),
    (r"городск[а-я]*", "City"),
    (r"место", "Place"),
)


def _common_app_activity_type(achievement: Achievement, item: dict | None = None) -> str:
    candidates = [
        item.get("common_app_activity_type") if item else None,
        achievement.category,
        achievement.title,
        achievement.organization_name,
        achievement.role_title,
        achievement.description_raw,
    ]
    compact_types = {option.lower(): option for option in COMMON_APP_ACTIVITY_TYPES}
    for value in candidates:
        cleaned = _clean_text(value).lower()
        if cleaned in compact_types:
            return compact_types[cleaned]
    text = " ".join(_clean_text(value).lower() for value in candidates if value)
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
    if any(word in text for word in ("intern", "internship")):
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
    if any(word in text for word in ("dance",)):
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
    if any(word in text for word in ("religious", "religion")):
        return "Religious"
    if any(word in text for word in ("sport", "athletic", "football", "basketball", "swim", "varsity")):
        return "Athletics: JV/Varsity"
    return "Other Club/Activity"


def _clean_text(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _english_clean_text(value, fallback: str = "") -> str:
    text = _clean_text(value)
    if not text:
        return _clean_text(fallback)

    text = re.sub(r"\bRepublican\b", "National", text, flags=re.IGNORECASE)
    text = re.sub(r"\bRespublikalyk\b", "National", text, flags=re.IGNORECASE)
    text = re.sub(r"\bRespublikanskiy\b", "National", text, flags=re.IGNORECASE)
    for pattern, replacement in CYRILLIC_TRANSLATIONS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Common App fields must be student-facing English. If a raw stored entry still
    # contains untranslated Russian/Kazakh fragments, keep the verified English
    # parts and remove only the remaining untranslated script.
    text = re.sub(r"\([^)]*[\u0400-\u04FF][^)]*\)", "", text)
    text = re.sub(r"[\u0400-\u04FF]+", "", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"([,.;:]){2,}", r"\1", text)
    text = _clean_text(text).strip(" -;,.:")

    if not text:
        text = _clean_text(fallback)
    if not text:
        return ""

    for index, char in enumerate(text):
        if char.isalpha():
            return text[:index] + char.upper() + text[index + 1 :]
    return text


def _enum_value(value) -> str:
    if value is None:
        return ""
    return getattr(value, "value", str(value))


def _truncate(value: str, limit: int) -> str:
    text = _clean_text(value)
    if len(text) <= limit:
        return text
    truncated = text[:limit]
    last_space = truncated.rfind(" ")
    if last_space > max(0, limit - 24):
        truncated = truncated[:last_space]
    return truncated.rstrip(",.;: ")


def _profile_graduation_year(user: Any | None) -> int | None:
    profile = getattr(user, "profile", None)
    graduation_year = getattr(profile, "graduation_year", None)
    try:
        return int(graduation_year) if graduation_year else None
    except (TypeError, ValueError):
        return None


def _years_from_text(*values: Any) -> list[int]:
    years: list[int] = []
    for value in values:
        for match in re.findall(r"\b(20\d{2}|19\d{2})\b", _clean_text(value)):
            year = int(match)
            if 1990 <= year <= 2100 and year not in years:
                years.append(year)
    return years


def _achievement_year(achievement: Achievement) -> int | None:
    if achievement.end_date:
        return achievement.end_date.year
    if achievement.start_date:
        return achievement.start_date.year
    years = _years_from_text(
        achievement.title,
        achievement.organization_name,
        achievement.role_title,
        achievement.description_raw,
    )
    return max(years) if years else None


def _grade_for_year(year: int | None, graduation_year: int | None) -> int | None:
    if not year or not graduation_year:
        return None
    grade = 12 - (graduation_year - year)
    if 9 <= grade <= 12:
        return grade
    return None


def _activity_grade_levels(achievement: Achievement, user: Any | None) -> str | None:
    graduation_year = _profile_graduation_year(user)
    years: list[int] = []
    if achievement.start_date and achievement.end_date:
        years = list(range(achievement.start_date.year, achievement.end_date.year + 1))
    elif achievement.start_date:
        years = list(range(achievement.start_date.year, min(date.today().year, achievement.start_date.year + 4) + 1))
    else:
        years = _years_from_text(
            achievement.title,
            achievement.organization_name,
            achievement.role_title,
            achievement.description_raw,
        )

    grades = sorted(
        {
            grade
            for grade in (_grade_for_year(year, graduation_year) for year in years)
            if grade is not None
        }
    )
    return ", ".join(str(grade) for grade in grades) or None


def _honor_grade_level(achievement: Achievement, user: Any | None) -> str | None:
    grade = _grade_for_year(_achievement_year(achievement), _profile_graduation_year(user))
    return str(grade) if grade is not None else None


def _activity_timing(achievement: Achievement) -> str | None:
    if achievement.weeks_per_year is None:
        return None
    if achievement.weeks_per_year >= 45:
        return "All year"
    if achievement.weeks_per_year >= 20:
        return "School year"
    return "School break / seasonal"


def _activity_continue(achievement: Achievement) -> str | None:
    if achievement.end_date is None:
        return "Continue"
    return "Continue" if achievement.end_date >= date.today() else "Completed"


def _number_label(value: Any) -> str | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return f"{number:g}"


def _common_app_honor_level(achievement: Achievement, item: dict | None = None) -> str | None:
    candidates = [
        item.get("common_app_honor_level") if item else None,
        item.get("honor_level") if item else None,
        _enum_value(achievement.impact_scope),
        achievement.title,
        achievement.organization_name,
        achievement.description_raw,
    ]
    text = " ".join(_english_clean_text(value).lower() for value in candidates if _clean_text(value))
    if not text:
        return None
    if "international" in text:
        return "International"
    if "national" in text or "republican" in text or "respublik" in text:
        return "National"
    if "regional" in text or "state" in text or "city" in text or "local" in text:
        return "State/Regional"
    if "school" in text:
        return "School"

    scope = _enum_value(achievement.impact_scope)
    if scope == "international":
        return "International"
    if scope == "national":
        return "National"
    if scope in {"regional", "local"}:
        return "State/Regional"
    if scope == "school":
        return "School"
    return None


def _format_honor_description(achievement: Achievement, item: dict | None = None) -> str:
    raw_value = (
        item.get("common_app_honor_description")
        if item
        else None
    ) or (
        item.get("common_app_text")
        if item
        else None
    ) or achievement.title
    value = _english_clean_text(raw_value, achievement.title)
    organization = _english_clean_text(achievement.organization_name)
    if organization and organization.lower() not in value.lower() and len(value) + len(organization) + 2 <= HONOR_DESCRIPTION_LIMIT:
        value = f"{value}, {organization}"

    year = _achievement_year(achievement)
    if year:
        value = re.sub(rf"\b{year}\b", "", value).strip(" ,;-")
        value = _clean_text(f"{year} {value}")
    return _truncate(value, HONOR_DESCRIPTION_LIMIT)


def _format_activity_description(achievement: Achievement, item: dict | None = None, word_limit: int | None = None) -> str:
    raw_value = (
        item.get("common_app_activity_description")
        if item
        else None
    ) or (
        item.get("common_app_text")
        if item
        else None
    ) or achievement.description_raw or achievement.title
    value = _english_clean_text(raw_value, achievement.title)
    if not value:
        role = _english_clean_text(achievement.role_title)
        org = _english_clean_text(achievement.organization_name)
        title = _english_clean_text(achievement.title)
        value = ". ".join(part for part in (role, org, title) if part)
    if word_limit and word_limit > 0:
        words = value.split()
        if len(words) > word_limit:
            value = " ".join(words[:word_limit])
    return _truncate(value, ACTIVITY_DESCRIPTION_LIMIT)


def _missing_facts_for_achievement(achievement: Achievement, user: Any | None) -> list[str]:
    questions: list[str] = []
    if achievement.type == AchievementType.activity:
        if not _activity_grade_levels(achievement, user):
            questions.append("Participation grade levels")
        if achievement.hours_per_week is None:
            questions.append("Hours per week")
        if achievement.weeks_per_year is None:
            questions.append("Weeks per year")
        if achievement.end_date is None:
            questions.append("Current status: continue or completed")
        return questions

    if _achievement_year(achievement) is None:
        questions.append("Award year")
    if not _common_app_honor_level(achievement):
        questions.append("Level of recognition: School, State/Regional, National, or International")
    if not _honor_grade_level(achievement, user):
        questions.append("Grade level when received")
    return questions


def _actionable_missing_facts(
    achievement: Achievement,
    item: dict,
    user: Any | None,
) -> list[str]:
    generic_fragments = (
        "review the original evidence before final submission",
        "verify the wording against the original evidence",
    )
    questions: list[str] = []
    for value in item.get("missing_or_unclear_facts") or []:
        text = _english_clean_text(value)
        if not text:
            continue
        normalized = text.lower().rstrip(".")
        if any(fragment in normalized for fragment in generic_fragments):
            continue
        if text not in questions:
            questions.append(text)

    for question in _missing_facts_for_achievement(achievement, user):
        if question not in questions:
            questions.append(question)
    return questions


def _local_achievement_score(achievement: Achievement) -> float:
    return sum(
        float(getattr(achievement, field) or 0)
        for field in (
            "major_relevance_score",
            "selectivity_score",
            "continuity_score",
            "distinctiveness_score",
        )
    )


def _achievement_shortlist_block(index: int, achievement: Achievement) -> str:
    fields = [
        ("Source index", index),
        ("Stored achievement id", achievement.id),
        ("Stored type", _enum_value(achievement.type)),
        ("Title", achievement.title),
        ("Organization", achievement.organization_name),
        ("Role", achievement.role_title),
        ("Description", achievement.description_raw),
        ("Category", achievement.category),
        ("Start date", achievement.start_date),
        ("End date", achievement.end_date),
        ("Hours per week", achievement.hours_per_week),
        ("Weeks per year", achievement.weeks_per_year),
        ("Impact scope", _enum_value(achievement.impact_scope)),
        ("Leadership level", _enum_value(achievement.leadership_level)),
        ("Major relevance score", achievement.major_relevance_score),
        ("Selectivity score", achievement.selectivity_score),
        ("Continuity score", achievement.continuity_score),
        ("Distinctiveness score", achievement.distinctiveness_score),
        ("Truth risk flag", achievement.truth_risk_flag),
    ]
    return "\n".join(f"{label}: {value}" for label, value in fields if value not in (None, ""))


def _selection_from_parsed_item(
    achievement: Achievement,
    item: dict,
    rank: int,
    user: Any | None = None,
    word_limit: int | None = None,
) -> dict:
    common_app_position = _truncate(
        _english_clean_text(
            item.get("common_app_position") or achievement.role_title or achievement.title,
            achievement.title,
        ),
        ACTIVITY_POSITION_LIMIT,
    )
    common_app_organization = _truncate(
        _english_clean_text(item.get("common_app_organization") or achievement.organization_name or ""),
        ACTIVITY_ORGANIZATION_LIMIT,
    )
    common_app_activity_description = _format_activity_description(
        achievement,
        item,
        word_limit,
    )
    common_app_honor_description = _format_honor_description(
        achievement,
        item,
    )
    common_app_text = (
        common_app_activity_description
        if achievement.type == AchievementType.activity
        else common_app_honor_description
    )

    return {
        "achievement_id": achievement.id,
        "type": achievement.type,
        "rank": rank,
        "title": _english_clean_text(achievement.title, achievement.title) or achievement.title,
        "common_app_text": common_app_text,
        "word_count": len(common_app_text.split()),
        "character_count": len(common_app_text),
        "common_app_position": common_app_position if achievement.type == AchievementType.activity else None,
        "common_app_organization": common_app_organization if achievement.type == AchievementType.activity else None,
        "common_app_activity_type": (
            _common_app_activity_type(achievement, item) if achievement.type == AchievementType.activity else None
        ),
        "common_app_activity_description": (
            common_app_activity_description if achievement.type == AchievementType.activity else None
        ),
        "common_app_activity_grade_levels": (
            _activity_grade_levels(achievement, user) if achievement.type == AchievementType.activity else None
        ),
        "common_app_activity_participation_timing": (
            _activity_timing(achievement) if achievement.type == AchievementType.activity else None
        ),
        "common_app_activity_hours_per_week": (
            _number_label(achievement.hours_per_week) if achievement.type == AchievementType.activity else None
        ),
        "common_app_activity_weeks_per_year": (
            _number_label(achievement.weeks_per_year) if achievement.type == AchievementType.activity else None
        ),
        "common_app_activity_continue": (
            _activity_continue(achievement) if achievement.type == AchievementType.activity else None
        ),
        "common_app_honor_description": (
            common_app_honor_description if achievement.type == AchievementType.honor else None
        ),
        "common_app_honor_level": (
            _common_app_honor_level(achievement, item) if achievement.type == AchievementType.honor else None
        ),
        "common_app_honor_grade_levels": (
            _honor_grade_level(achievement, user) if achievement.type == AchievementType.honor else None
        ),
        "position_character_count": len(common_app_position) if achievement.type == AchievementType.activity else None,
        "organization_character_count": len(common_app_organization) if achievement.type == AchievementType.activity else None,
        "activity_description_character_count": (
            len(common_app_activity_description) if achievement.type == AchievementType.activity else None
        ),
        "honor_character_count": (
            len(common_app_honor_description) if achievement.type == AchievementType.honor else None
        ),
        "selection_reason": item.get("selection_reason") or "Selected from the current vault shortlist pass.",
        "verification_notes": item.get("verification_notes") or [],
        "missing_or_unclear_facts": _actionable_missing_facts(achievement, item, user),
    }


def _fallback_selection_from_achievement(
    achievement: Achievement,
    rank: int,
    user: Any | None = None,
    word_limit: int | None = None,
) -> dict:
    fallback_item = {
        "common_app_position": achievement.role_title or achievement.title,
        "common_app_organization": achievement.organization_name or "",
        "common_app_activity_type": _common_app_activity_type(achievement),
        "common_app_activity_description": _format_activity_description(achievement, word_limit=word_limit),
        "common_app_honor_description": _format_honor_description(achievement),
        "selection_reason": "Ranked from stored Chancellor scores and formatted for Common App fields.",
        "verification_notes": [],
        "missing_or_unclear_facts": _missing_facts_for_achievement(achievement, user),
    }
    return _selection_from_parsed_item(achievement, fallback_item, rank, user, word_limit)


def _mapped_selection(
    parsed_items: list[dict],
    achievement_type: AchievementType,
    by_source_index: dict[int, Achievement],
    selected_ids: set,
    limit: int,
    user: Any | None = None,
    word_limit: int | None = None,
) -> list[dict]:
    selection: list[dict] = []
    sorted_items = sorted(
        parsed_items,
        key=lambda item: (
            item.get("recommended_rank") is None,
            item.get("recommended_rank") or 99,
        ),
    )
    for item in sorted_items:
        if len(selection) >= limit:
            break
        try:
            source_index = int(item.get("source_index") or 0)
        except (TypeError, ValueError):
            continue
        achievement = by_source_index.get(source_index)
        if not achievement or achievement.type != achievement_type or achievement.id in selected_ids:
            continue
        selected_ids.add(achievement.id)
        selection.append(_selection_from_parsed_item(achievement, item, len(selection) + 1, user, word_limit))
    return selection


def _fill_selection_from_vault(
    selection: list[dict],
    achievements: list[Achievement],
    achievement_type: AchievementType,
    selected_ids: set,
    limit: int,
    user: Any | None = None,
    word_limit: int | None = None,
) -> list[dict]:
    candidates = sorted(
        (achievement for achievement in achievements if achievement.type == achievement_type),
        key=lambda achievement: (_local_achievement_score(achievement), achievement.created_at),
        reverse=True,
    )
    for achievement in candidates:
        if len(selection) >= limit:
            break
        if achievement.id in selected_ids:
            continue
        selected_ids.add(achievement.id)
        selection.append(_fallback_selection_from_achievement(achievement, len(selection) + 1, user, word_limit))
    return selection


@router.get("", response_model=dict)
def list_achievements(
    type: Optional[AchievementType] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Achievement).filter(Achievement.user_id == current_user.id)
    if type:
        query = query.filter(Achievement.type == type)
    achievements = query.order_by(Achievement.created_at.desc()).all()
    return {
        "data": [AchievementOut.model_validate(a).model_dump() for a in achievements],
        "message": "OK",
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_achievement(
    payload: AchievementCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    achievement_data = payload.model_dump()
    achievement_data.update(estimate_chancellor_scores(payload, current_user))
    achievement = Achievement(
        user_id=current_user.id,
        **achievement_data,
    )
    db.add(achievement)
    db.commit()
    db.refresh(achievement)
    return {
        "data": AchievementOut.model_validate(achievement).model_dump(),
        "message": "Achievement created",
    }


@router.get("/{achievement_id}", response_model=dict)
def get_achievement(
    achievement_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    achievement = db.query(Achievement).filter(
        Achievement.id == achievement_id,
        Achievement.user_id == current_user.id,
    ).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return {
        "data": AchievementOut.model_validate(achievement).model_dump(),
        "message": "OK",
    }


@router.put("/{achievement_id}", response_model=dict)
def update_achievement(
    achievement_id: UUID,
    payload: AchievementUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    achievement = db.query(Achievement).filter(
        Achievement.id == achievement_id,
        Achievement.user_id == current_user.id,
    ).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(achievement, field, value)

    for field, value in estimate_chancellor_scores(achievement, current_user).items():
        setattr(achievement, field, value)

    db.commit()
    db.refresh(achievement)
    return {
        "data": AchievementOut.model_validate(achievement).model_dump(),
        "message": "Achievement updated",
    }


@router.delete("/{achievement_id}", response_model=dict)
def delete_achievement(
    achievement_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    achievement = db.query(Achievement).filter(
        Achievement.id == achievement_id,
        Achievement.user_id == current_user.id,
    ).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    db.delete(achievement)
    db.commit()
    return {"data": None, "message": "Achievement deleted"}


@router.post("/shortlist", response_model=dict)
def build_shortlist_from_current_vault(
    payload: AchievementShortlistRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    achievements = (
        db.query(Achievement)
        .filter(Achievement.user_id == current_user.id)
        .order_by(Achievement.created_at.asc())
        .all()
    )
    if not achievements:
        raise HTTPException(
            status_code=400,
            detail="Add at least one achievement before building a Common App shortlist.",
        )

    selected_activity_ids: set = set()
    selected_honor_ids: set = set()
    activity_selection = _fill_selection_from_vault(
        [],
        achievements,
        AchievementType.activity,
        selected_activity_ids,
        TOP_ACTIVITY_LIMIT,
        current_user,
        payload.word_limit,
    )
    honor_selection = _fill_selection_from_vault(
        [],
        achievements,
        AchievementType.honor,
        selected_honor_ids,
        TOP_HONOR_LIMIT,
        current_user,
        payload.word_limit,
    )

    processing_steps = [
        {
            "key": "read_vault",
            "label": "Read current vault",
            "status": "complete",
            "detail": f"Loaded {len(achievements)} saved achievements from Achievement Vault.",
        },
        {
            "key": "analyze_vault",
            "label": "Analyze stored achievements",
            "status": "complete",
            "detail": (
                f"Ranked {len([a for a in achievements if a.type == AchievementType.activity])} activities "
                f"and {len([a for a in achievements if a.type == AchievementType.honor])} honors."
            ),
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
    ]

    return {
        "data": AchievementImportOut(
            file_name="Current Vault",
            word_limit=payload.word_limit,
            imported_count=0,
            strongest_angle=(
                "Use the highest-scoring sustained activities first, then support them with the strongest academic honors."
            ),
            needs_student_clarification=any(
                item.get("missing_or_unclear_facts") for item in [*activity_selection, *honor_selection]
            ),
            clarifying_questions=[],
            additional_information_recommended=False,
            additional_information_reason=None,
            additional_information_draft=None,
            formatting_notes=[
                "Built from achievements already saved in the current vault.",
                "Common App activity fields use: Activity type, position/leadership <= 50 chars, organization <= 100 chars, description <= 150 chars.",
                "Common App honors use one honor title/description field <= 100 chars.",
            ],
            extraction_notes=[
                "No new achievements were imported; this pass only generated the shortlist from saved vault entries.",
            ],
            source_excerpts=[
                _truncate(
                    " - ".join(
                        _clean_text(value)
                        for value in (achievement.title, achievement.organization_name, achievement.description_raw)
                        if _clean_text(value)
                    ),
                    240,
                )
                for achievement in achievements[:8]
            ],
            processing_steps=processing_steps,
            imported_achievements=[
                AchievementOut.model_validate(achievement).model_dump()
                for achievement in achievements
            ],
            top_activities=activity_selection,
            top_honors=honor_selection,
        ).model_dump(),
        "message": "Common App shortlist generated from current vault",
    }


@router.post("/{achievement_id}/upload", response_model=dict)
async def upload_evidence(
    achievement_id: UUID,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    achievement = db.query(Achievement).filter(
        Achievement.id == achievement_id,
        Achievement.user_id == current_user.id,
    ).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    # In production, upload to S3; for now, store locally
    file_url = f"/uploads/{achievement_id}/{file.filename}"

    evidence = AchievementEvidenceFile(
        achievement_id=achievement_id,
        user_id=current_user.id,
        file_url=file_url,
        file_name=file.filename,
        mime_type=file.content_type,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return {
        "data": EvidenceFileOut.model_validate(evidence).model_dump(),
        "message": "File uploaded",
    }


@router.post("/import-all", response_model=dict, status_code=status.HTTP_201_CREATED)
async def import_all_achievements(
    file: UploadFile = File(...),
    word_limit: int = Form(22),
    clarification_answers: Optional[str] = Form(None),
    previous_import_ids: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if word_limit < 5 or word_limit > 40:
        raise HTTPException(status_code=400, detail="Word limit must be between 5 and 40.")

    raw_bytes = await file.read()
    try:
        raw_text = decode_import_file(file.filename or "import.txt", raw_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    parsed_clarification_answers: dict[str, str] = {}
    if clarification_answers:
        try:
            raw_answers = json.loads(clarification_answers)
            if isinstance(raw_answers, dict):
                parsed_clarification_answers = {
                    str(key): str(value).strip()
                    for key, value in raw_answers.items()
                    if str(value).strip()
                }
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid clarification answers JSON.") from exc

    parsed_previous_ids: list[UUID] = []
    if previous_import_ids:
        try:
            raw_ids = json.loads(previous_import_ids)
            if isinstance(raw_ids, list):
                parsed_previous_ids = [UUID(str(value)) for value in raw_ids]
        except (json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="Invalid previous import ids JSON.") from exc

    try:
        parsed = parse_achievement_import(
            raw_text,
            current_user,
            word_limit,
            parsed_clarification_answers,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Import failed while analyzing the file. Try a smaller text-based PDF, DOCX, TXT, MD, CSV, "
                "or JSON file; scanned image PDFs are not supported yet."
            ),
        ) from exc

    if parsed_previous_ids:
        db.query(Achievement).filter(
            Achievement.user_id == current_user.id,
            Achievement.id.in_(parsed_previous_ids),
        ).delete(synchronize_session=False)
        db.flush()

    imported_achievements: list[Achievement] = []
    selection_items: list[tuple[Achievement, dict]] = []

    for item in parsed["items"]:
        achievement = Achievement(
            user_id=current_user.id,
            type=AchievementType(item["type"]),
            title=item["title"],
            organization_name=item["organization_name"],
            role_title=item["role_title"],
            description_raw=item["description_raw"],
            category=item["category"],
            hours_per_week=item["hours_per_week"],
            weeks_per_year=item["weeks_per_year"],
            impact_scope=item["impact_scope"],
            leadership_level=item["leadership_level"],
            truth_risk_flag=item["truth_risk_flag"],
            major_relevance_score=item["major_relevance_score"],
            selectivity_score=item["selectivity_score"],
            continuity_score=item["continuity_score"],
            distinctiveness_score=item["distinctiveness_score"],
        )
        db.add(achievement)
        imported_achievements.append(achievement)
        selection_items.append((achievement, item))

    db.commit()

    for achievement in imported_achievements:
        db.refresh(achievement)

    activity_selection = []
    honor_selection = []

    for achievement, item in selection_items:
        try:
            rank = int(item.get("recommended_rank") or 0)
        except (TypeError, ValueError):
            rank = 0
        if not rank:
            continue
        selection_item = _selection_from_parsed_item(
            achievement,
            item,
            rank,
            current_user,
            word_limit,
        )
        if achievement.type == AchievementType.activity and rank <= 10:
            activity_selection.append(selection_item)
        if achievement.type == AchievementType.honor and rank <= 5:
            honor_selection.append(selection_item)

    activity_selection.sort(key=lambda item: item["rank"])
    honor_selection.sort(key=lambda item: item["rank"])

    return {
        "data": AchievementImportOut(
            file_name=file.filename or "import.txt",
            word_limit=word_limit,
            imported_count=len(imported_achievements),
            strongest_angle=parsed["strongest_angle"],
            needs_student_clarification=parsed.get("needs_student_clarification", False),
            clarifying_questions=parsed.get("clarifying_questions", []),
            additional_information_recommended=parsed.get("additional_information_recommended", False),
            additional_information_reason=parsed.get("additional_information_reason") or None,
            additional_information_draft=parsed.get("additional_information_draft") or None,
            formatting_notes=parsed.get("formatting_notes", []),
            extraction_notes=parsed.get("extraction_notes", []),
            source_excerpts=parsed.get("source_excerpts", []),
            processing_steps=[
                *parsed.get("processing_steps", []),
                {
                    "key": "save_vault",
                    "label": "Save imported achievements",
                    "status": "complete",
                    "detail": f"Saved {len(imported_achievements)} extracted items to Achievement Vault.",
                },
            ],
            imported_achievements=[
                AchievementOut.model_validate(achievement).model_dump()
                for achievement in imported_achievements
            ],
            top_activities=activity_selection,
            top_honors=honor_selection,
        ).model_dump(),
        "message": "Achievements imported",
    }
