import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
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


def _clean_text(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


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
) -> dict:
    common_app_position = _truncate(
        item.get("common_app_position") or achievement.role_title or achievement.title,
        ACTIVITY_POSITION_LIMIT,
    )
    common_app_organization = _truncate(
        item.get("common_app_organization") or achievement.organization_name or "",
        ACTIVITY_ORGANIZATION_LIMIT,
    )
    common_app_activity_description = _truncate(
        item.get("common_app_activity_description")
        or item.get("common_app_text")
        or achievement.description_raw
        or achievement.title,
        ACTIVITY_DESCRIPTION_LIMIT,
    )
    common_app_honor_description = _truncate(
        item.get("common_app_honor_description") or item.get("common_app_text") or achievement.title,
        HONOR_DESCRIPTION_LIMIT,
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
        "title": achievement.title,
        "common_app_text": common_app_text,
        "word_count": len(common_app_text.split()),
        "character_count": len(common_app_text),
        "common_app_position": common_app_position if achievement.type == AchievementType.activity else None,
        "common_app_organization": common_app_organization if achievement.type == AchievementType.activity else None,
        "common_app_activity_description": (
            common_app_activity_description if achievement.type == AchievementType.activity else None
        ),
        "common_app_honor_description": (
            common_app_honor_description if achievement.type == AchievementType.honor else None
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
        "missing_or_unclear_facts": item.get("missing_or_unclear_facts") or [],
    }


def _fallback_selection_from_achievement(achievement: Achievement, rank: int) -> dict:
    fallback_item = {
        "common_app_position": achievement.role_title or achievement.title,
        "common_app_organization": achievement.organization_name or "",
        "common_app_activity_description": achievement.description_raw or achievement.title,
        "common_app_honor_description": (
            f"{achievement.title}, {achievement.organization_name}"
            if achievement.organization_name
            else achievement.title
        ),
        "selection_reason": "Added from stored Chancellor scores because no mapped AI shortlist item was returned.",
        "verification_notes": [],
        "missing_or_unclear_facts": [
            "Review the original evidence before final submission."
        ],
    }
    return _selection_from_parsed_item(achievement, fallback_item, rank)


def _mapped_selection(
    parsed_items: list[dict],
    achievement_type: AchievementType,
    by_source_index: dict[int, Achievement],
    selected_ids: set,
    limit: int,
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
        selection.append(_selection_from_parsed_item(achievement, item, len(selection) + 1))
    return selection


def _fill_selection_from_vault(
    selection: list[dict],
    achievements: list[Achievement],
    achievement_type: AchievementType,
    selected_ids: set,
    limit: int,
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
        selection.append(_fallback_selection_from_achievement(achievement, len(selection) + 1))
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

    raw_text = "\n\n".join(
        _achievement_shortlist_block(index, achievement)
        for index, achievement in enumerate(achievements, start=1)
    )
    parsed = parse_achievement_import(raw_text, current_user, payload.word_limit)
    by_source_index = {
        index: achievement
        for index, achievement in enumerate(achievements, start=1)
    }

    selected_activity_ids: set = set()
    selected_honor_ids: set = set()
    activity_selection = _mapped_selection(
        parsed.get("top_activities", []),
        AchievementType.activity,
        by_source_index,
        selected_activity_ids,
        TOP_ACTIVITY_LIMIT,
    )
    honor_selection = _mapped_selection(
        parsed.get("top_honors", []),
        AchievementType.honor,
        by_source_index,
        selected_honor_ids,
        TOP_HONOR_LIMIT,
    )

    activity_selection = _fill_selection_from_vault(
        activity_selection,
        achievements,
        AchievementType.activity,
        selected_activity_ids,
        TOP_ACTIVITY_LIMIT,
    )
    honor_selection = _fill_selection_from_vault(
        honor_selection,
        achievements,
        AchievementType.honor,
        selected_honor_ids,
        TOP_HONOR_LIMIT,
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
            strongest_angle=parsed["strongest_angle"],
            needs_student_clarification=parsed.get("needs_student_clarification", False),
            clarifying_questions=parsed.get("clarifying_questions", []),
            additional_information_recommended=parsed.get("additional_information_recommended", False),
            additional_information_reason=parsed.get("additional_information_reason") or None,
            additional_information_draft=parsed.get("additional_information_draft") or None,
            formatting_notes=[
                "Built from achievements already saved in the current vault.",
                *parsed.get("formatting_notes", []),
            ],
            extraction_notes=[
                "No new achievements were imported; this pass only generated the shortlist.",
                *parsed.get("extraction_notes", []),
            ],
            source_excerpts=parsed.get("source_excerpts", []),
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

    parsed = parse_achievement_import(
        raw_text,
        current_user,
        word_limit,
        parsed_clarification_answers,
    )

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
        rank = item.get("recommended_rank")
        if not rank:
            continue
        selection_item = {
            "achievement_id": achievement.id,
            "type": achievement.type,
            "rank": rank,
            "title": achievement.title,
            "common_app_text": item["common_app_text"],
            "word_count": len(item["common_app_text"].split()),
            "character_count": len(item["common_app_text"]),
            "common_app_position": item.get("common_app_position"),
            "common_app_organization": item.get("common_app_organization"),
            "common_app_activity_description": item.get("common_app_activity_description"),
            "common_app_honor_description": item.get("common_app_honor_description"),
            "position_character_count": len(item.get("common_app_position") or ""),
            "organization_character_count": len(item.get("common_app_organization") or ""),
            "activity_description_character_count": len(item.get("common_app_activity_description") or ""),
            "honor_character_count": len(item.get("common_app_honor_description") or ""),
            "selection_reason": item.get("selection_reason") or None,
            "verification_notes": item.get("verification_notes") or [],
            "missing_or_unclear_facts": item.get("missing_or_unclear_facts") or [],
        }
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
