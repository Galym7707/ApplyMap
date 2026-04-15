from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.user import ProfileCreate, ProfileUpdate, ProfileOut, UserOut, UserUpdate
from ..models.user import StudentProfile
from ..routes.auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=dict)
def get_profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return {
        "data": {
            "user": UserOut.model_validate(current_user).model_dump(),
            "profile": ProfileOut.model_validate(profile).model_dump(),
        },
        "message": "OK",
    }


@router.put("", response_model=dict)
def update_profile(
    payload: ProfileUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return {
        "data": ProfileOut.model_validate(profile).model_dump(),
        "message": "Profile updated",
    }


@router.put("/user", response_model=dict)
def update_user(
    payload: UserUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return {
        "data": UserOut.model_validate(current_user).model_dump(),
        "message": "User updated",
    }
