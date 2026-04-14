from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ..database import get_db
from ..schemas.university import (
    UniversityOut,
    UniversityListOut,
    PolicyEntryOut,
    CommonAppRecommendationRequest,
)
from ..models.achievement import Achievement
from ..models.university import University, UniversityPolicyEntry
from ..routes.auth import get_current_user
from ..services.university_filters import enrich_university, filter_universities
from ..services.university_recommender import recommend_common_app_universities

router = APIRouter(prefix="/api/universities", tags=["universities"])


@router.get("", response_model=dict)
def list_universities(
    search: Optional[str] = None,
    country: Optional[str] = None,
    region: Optional[str] = None,
    application_system: Optional[str] = None,
    teaching_language: Optional[str] = None,
    major: Optional[str] = None,
    school_years: Optional[int] = None,
    full_ride_only: bool = False,
    common_app_only: bool = False,
    aid_type: Optional[str] = None,
    sort_by: str = "name",
    sort_dir: str = "asc",
    db: Session = Depends(get_db),
):
    query = db.query(University).filter(University.is_active == True)
    universities = [
        enrich_university(university)
        for university in query.order_by(University.name).all()
    ]
    universities = filter_universities(
        universities,
        search=search,
        country=country,
        region=region,
        application_system=application_system,
        teaching_language=teaching_language,
        major=major,
        school_years=school_years,
        full_ride_only=full_ride_only,
        common_app_only=common_app_only,
        aid_type=aid_type,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return {
        "data": [UniversityListOut.model_validate(u).model_dump() for u in universities],
        "message": "OK",
    }


@router.post("/recommendations/common-app", response_model=dict, status_code=status.HTTP_201_CREATED)
def recommend_common_app(
    payload: CommonAppRecommendationRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.top_honor_ids and not payload.top_activity_ids:
        raise HTTPException(status_code=400, detail="Select up to 5 honors and up to 10 activities first")

    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=400, detail="Complete your profile before generating recommendations")

    existing_preferences = profile.application_preferences_json or {}
    preferences = {
        **existing_preferences,
        **payload.preferences,
        "top_honor_ids": [str(item) for item in payload.top_honor_ids[:5]],
        "top_activity_ids": [str(item) for item in payload.top_activity_ids[:10]],
        "intended_major": payload.preferences.get("intended_major") or profile.intended_major,
        "curriculum": profile.curriculum,
        "graduation_year": profile.graduation_year,
    }
    if payload.save_preferences:
        profile.application_preferences_json = preferences
        db.commit()
        db.refresh(profile)

    achievements = db.query(Achievement).filter(Achievement.user_id == current_user.id).all()
    by_id = {str(achievement.id): achievement for achievement in achievements}
    selected_honors = [
        by_id[str(item)]
        for item in payload.top_honor_ids[:5]
        if str(item) in by_id and by_id[str(item)].type.value == "honor"
    ]
    selected_activities = [
        by_id[str(item)]
        for item in payload.top_activity_ids[:10]
        if str(item) in by_id and by_id[str(item)].type.value == "activity"
    ]
    if not selected_honors and not selected_activities:
        raise HTTPException(status_code=400, detail="Selected achievements were not found")

    universities = [
        enrich_university(university)
        for university in db.query(University).filter(University.is_active == True).all()
    ]
    common_app_universities = filter_universities(
        universities,
        common_app_only=True,
        school_years=int(preferences["school_years"]) if str(preferences.get("school_years") or "").isdigit() else None,
        sort_by="aid_strength",
        sort_dir="desc",
    )

    recommendations = recommend_common_app_universities(
        selected_honors=selected_honors,
        selected_activities=selected_activities,
        preferences=preferences,
        universities=common_app_universities,
    )
    return {
        "data": {
            "recommendations": recommendations,
            "selected_honors": len(selected_honors),
            "selected_activities": len(selected_activities),
            "available_common_app_universities": len(common_app_universities),
            "category_note": "Safe means relative safety within the funded Common App shortlist, not guaranteed admission or aid.",
        },
        "message": "Recommendations generated",
    }


@router.get("/{university_id}", response_model=dict)
def get_university(university_id: UUID, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    return {
        "data": UniversityOut.model_validate(university).model_dump(),
        "message": "OK",
    }


@router.get("/{university_id}/sources", response_model=dict)
def get_university_sources(university_id: UUID, db: Session = Depends(get_db)):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    entries = db.query(UniversityPolicyEntry).filter(
        UniversityPolicyEntry.university_id == university_id
    ).all()

    return {
        "data": [PolicyEntryOut.model_validate(e).model_dump() for e in entries],
        "message": "OK",
    }
