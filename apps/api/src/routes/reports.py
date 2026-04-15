from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import json

from ..database import get_db
from ..schemas.report import ReportOut, ReportDetailOut, TargetUniversityCreate, TargetUniversityOut
from ..models.report import (
    OptimizationReport, TargetUniversity, ReportStatus,
)
from ..models.achievement import Achievement
from ..models.university import University
from ..routes.auth import get_current_user
from ..services.optimization_engine import run_optimization
from ..services.rewrite_service import generate_rewrite_variants

router = APIRouter(prefix="/api", tags=["reports"])


# --- Target Universities ---

@router.get("/targets", response_model=dict)
def list_targets(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    targets = (
        db.query(TargetUniversity)
        .filter(TargetUniversity.user_id == current_user.id)
        .order_by(TargetUniversity.priority_order)
        .all()
    )
    return {
        "data": [TargetUniversityOut.model_validate(t).model_dump() for t in targets],
        "message": "OK",
    }


@router.post("/targets", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_target(
    payload: TargetUniversityCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fit_category = payload.fit_category if payload.fit_category in {"dream", "target", "safe"} else "target"
    # Check university exists
    university = db.query(University).filter(University.id == payload.university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    # Check not already targeted
    existing = db.query(TargetUniversity).filter(
        TargetUniversity.user_id == current_user.id,
        TargetUniversity.university_id == payload.university_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="University already in targets")

    target = TargetUniversity(
        user_id=current_user.id,
        university_id=payload.university_id,
        priority_order=payload.priority_order,
        fit_category=fit_category,
    )
    db.add(target)
    db.commit()
    db.refresh(target)

    return {
        "data": TargetUniversityOut.model_validate(target).model_dump(),
        "message": "University added to targets",
    }


@router.delete("/targets/{target_id}", response_model=dict)
def remove_target(
    target_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = db.query(TargetUniversity).filter(
        TargetUniversity.id == target_id,
        TargetUniversity.user_id == current_user.id,
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    db.delete(target)
    db.commit()
    return {"data": None, "message": "Target removed"}


# --- Reports ---

def _run_report_generation(db: Session, report_id: UUID):
    """Background task to generate the report."""
    report = db.query(OptimizationReport).filter(OptimizationReport.id == report_id).first()
    if not report:
        return

    try:
        report.status = ReportStatus.processing
        db.commit()

        university = db.query(University).filter(University.id == report.university_id).first()
        achievements = db.query(Achievement).filter(Achievement.user_id == report.user_id).all()

        run_optimization(db, report, achievements, university)

        # Generate rewrite variants for top kept recommendations
        from ..models.report import ReportRecommendation, RecommendationType
        kept_recs = db.query(ReportRecommendation).filter(
            ReportRecommendation.report_id == report.id,
            ReportRecommendation.recommendation_type.in_([
                RecommendationType.keep,
                RecommendationType.rewrite,
            ]),
        ).all()

        for rec in kept_recs[:15]:  # Limit rewrites to top 15
            achievement = db.query(Achievement).filter(Achievement.id == rec.achievement_id).first()
            if achievement:
                variants = generate_rewrite_variants(db, achievement, report)
                db.add_all(variants)

        db.commit()

    except Exception as e:
        report.status = ReportStatus.failed
        report.summary_text = f"Generation failed: {str(e)}"
        db.commit()
        raise


@router.post("/reports/generate", response_model=dict, status_code=status.HTTP_201_CREATED)
def generate_report(
    university_id: UUID,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    # Check for existing pending/processing report
    existing = db.query(OptimizationReport).filter(
        OptimizationReport.user_id == current_user.id,
        OptimizationReport.university_id == university_id,
        OptimizationReport.status.in_([ReportStatus.pending, ReportStatus.processing]),
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="A report for this university is already being processed")

    # Determine version number
    prev_reports = db.query(OptimizationReport).filter(
        OptimizationReport.user_id == current_user.id,
        OptimizationReport.university_id == university_id,
    ).count()

    report = OptimizationReport(
        user_id=current_user.id,
        university_id=university_id,
        status=ReportStatus.pending,
        version_number=prev_reports + 1,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Run synchronously for MVP (can be moved to background task with proper async setup)
    try:
        _run_report_generation(db, report.id)
        db.refresh(report)
    except Exception:
        pass

    return {
        "data": ReportOut.model_validate(report).model_dump(),
        "message": "Report generated",
    }


@router.get("/reports", response_model=dict)
def list_reports(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    reports = (
        db.query(OptimizationReport)
        .filter(OptimizationReport.user_id == current_user.id)
        .order_by(OptimizationReport.created_at.desc())
        .all()
    )
    return {
        "data": [ReportOut.model_validate(r).model_dump() for r in reports],
        "message": "OK",
    }


@router.get("/reports/{report_id}", response_model=dict)
def get_report(
    report_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(OptimizationReport).filter(
        OptimizationReport.id == report_id,
        OptimizationReport.user_id == current_user.id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "data": ReportDetailOut.model_validate(report).model_dump(),
        "message": "OK",
    }


@router.get("/reports/{report_id}/export", response_model=dict)
def export_report(
    report_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.query(OptimizationReport).filter(
        OptimizationReport.id == report_id,
        OptimizationReport.user_id == current_user.id,
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    detail = ReportDetailOut.model_validate(report).model_dump()

    # Build export-friendly structure
    export = {
        "report_id": str(report.id),
        "university": detail["university"]["name"],
        "generated_at": detail["created_at"],
        "summary": detail["summary_text"],
        "recommendations": [
            {
                "rank": r["suggested_rank"],
                "type": r["recommendation_type"],
                "title": r["achievement"]["title"],
                "rationale": r["rationale"],
                "confidence": r["confidence_label"],
            }
            for r in detail["recommendations"]
            if r["suggested_rank"] is not None
        ],
        "rewrite_variants": [
            {
                "achievement_title": next(
                    (r["achievement"]["title"] for r in detail["recommendations"] if r["achievement_id"] == v["achievement_id"]),
                    "Unknown",
                ),
                "style": v["style_mode"],
                "text": v["text"],
                "char_count": v["character_count"],
            }
            for v in detail["rewrite_variants"]
            if v["is_recommended"]
        ],
        "sources": [
            {
                "section": s["section"],
                "title": s["policy_entry"]["title"],
                "source_type": s["policy_entry"]["source_type"],
                "reliability_tier": s["policy_entry"]["reliability_tier"],
                "url": s["policy_entry"]["source_url"],
            }
            for s in detail["source_references"]
        ],
    }

    return {"data": export, "message": "OK"}
