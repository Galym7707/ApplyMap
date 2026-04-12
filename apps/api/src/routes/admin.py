from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..schemas.university import UniversityCreate, UniversityUpdate, UniversityOut, PolicyEntryCreate, PolicyEntryUpdate, PolicyEntryOut
from ..models.university import University, UniversityPolicyEntry
from ..models.report import AdminAuditLog
from ..routes.auth import get_admin_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def log_action(db: Session, admin_id, action: str, entity_type: str, entity_id: str, metadata: dict = None):
    log = AdminAuditLog(
        admin_user_id=admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata or {},
    )
    db.add(log)


@router.post("/universities", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_university(
    payload: UniversityCreate,
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    existing = db.query(University).filter(University.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already in use")

    university = University(**payload.model_dump())
    db.add(university)
    db.flush()

    log_action(db, admin.id, "create_university", "university", str(university.id))
    db.commit()
    db.refresh(university)

    return {
        "data": UniversityOut.model_validate(university).model_dump(),
        "message": "University created",
    }


@router.put("/universities/{university_id}", response_model=dict)
def update_university(
    university_id: UUID,
    payload: UniversityUpdate,
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(university, field, value)

    log_action(db, admin.id, "update_university", "university", str(university_id))
    db.commit()
    db.refresh(university)

    return {
        "data": UniversityOut.model_validate(university).model_dump(),
        "message": "University updated",
    }


@router.delete("/universities/{university_id}", response_model=dict)
def delete_university(
    university_id: UUID,
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    log_action(db, admin.id, "delete_university", "university", str(university_id))
    db.delete(university)
    db.commit()

    return {"data": None, "message": "University deleted"}


@router.post("/universities/{university_id}/sources", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_policy_entry(
    university_id: UUID,
    payload: PolicyEntryCreate,
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    entry = UniversityPolicyEntry(university_id=university_id, **payload.model_dump())
    db.add(entry)
    db.flush()

    log_action(db, admin.id, "create_policy_entry", "policy_entry", str(entry.id))
    db.commit()
    db.refresh(entry)

    return {
        "data": PolicyEntryOut.model_validate(entry).model_dump(),
        "message": "Policy entry created",
    }


@router.put("/sources/{entry_id}", response_model=dict)
def update_policy_entry(
    entry_id: UUID,
    payload: PolicyEntryUpdate,
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    entry = db.query(UniversityPolicyEntry).filter(UniversityPolicyEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Policy entry not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    log_action(db, admin.id, "update_policy_entry", "policy_entry", str(entry_id))
    db.commit()
    db.refresh(entry)

    return {
        "data": PolicyEntryOut.model_validate(entry).model_dump(),
        "message": "Policy entry updated",
    }


@router.delete("/sources/{entry_id}", response_model=dict)
def delete_policy_entry(
    entry_id: UUID,
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    entry = db.query(UniversityPolicyEntry).filter(UniversityPolicyEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Policy entry not found")

    log_action(db, admin.id, "delete_policy_entry", "policy_entry", str(entry_id))
    db.delete(entry)
    db.commit()

    return {"data": None, "message": "Policy entry deleted"}


@router.get("/audit-logs", response_model=dict)
def list_audit_logs(
    limit: int = 50,
    offset: int = 0,
    admin=Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(AdminAuditLog)
        .order_by(AdminAuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "data": [
            {
                "id": str(l.id),
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ],
        "message": "OK",
    }
