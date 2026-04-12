from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from ..database import get_db
from ..schemas.university import UniversityOut, UniversityListOut, PolicyEntryOut
from ..models.university import University, UniversityPolicyEntry
from ..routes.auth import get_current_user

router = APIRouter(prefix="/api/universities", tags=["universities"])


@router.get("", response_model=dict)
def list_universities(
    search: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(University).filter(University.is_active == True)

    if search:
        query = query.filter(University.name.ilike(f"%{search}%"))
    if country:
        query = query.filter(University.country.ilike(f"%{country}%"))

    universities = query.order_by(University.name).all()
    return {
        "data": [UniversityListOut.model_validate(u).model_dump() for u in universities],
        "message": "OK",
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
