from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ..schemas.achievement import AchievementCreate, AchievementUpdate, AchievementOut, EvidenceFileOut
from ..models.achievement import Achievement, AchievementEvidenceFile, AchievementType
from ..routes.auth import get_current_user
from ..services.chancellor_analysis import estimate_chancellor_scores

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
