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
)
from ..models.achievement import Achievement, AchievementEvidenceFile, AchievementType
from ..routes.auth import get_current_user
from ..services.chancellor_analysis import estimate_chancellor_scores
from ..services.achievement_import_service import decode_import_file, parse_achievement_import

router = APIRouter(prefix="/api/achievements", tags=["achievements"])


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

    parsed = parse_achievement_import(raw_text, current_user, word_limit)

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
            "selection_reason": item.get("selection_reason") or None,
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
            imported_achievements=[
                AchievementOut.model_validate(achievement).model_dump()
                for achievement in imported_achievements
            ],
            top_activities=activity_selection,
            top_honors=honor_selection,
        ).model_dump(),
        "message": "Achievements imported",
    }
