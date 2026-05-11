"""Deterministic advisor brackets endpoint.

Returns three brackets (stretch / realistic / safety) of universities chosen
from the seeded catalog along with concrete profile-improvement actions.
Unlike `/api/universities/advisor/plan` (which calls the LLM + Google search),
this endpoint is fully deterministic and works offline.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.achievement import Achievement
from ..models.university import University
from ..routes.auth import get_current_user
from ..schemas.advisor import (
    AdvisorBracketsOut,
    ProfileActionOut,
    ProfileStrengthOut,
    UniversityFitOut,
)
from ..services.admissions_advisor import (
    AdvisorOutput,
    UniversityFit,
    generate_advisor_output,
)


router = APIRouter(prefix="/api/advisor", tags=["advisor"])


def _bracket_subset(advisor: AdvisorOutput, bracket: str) -> list[UniversityFit]:
    return [fit for fit in advisor.fits if fit.bracket == bracket]


@router.get("/brackets", response_model=dict)
def advisor_brackets(
    limit_per_bracket: int = Query(default=6, ge=1, le=20),
    country: Optional[str] = Query(default=None),
    common_app_only: bool = Query(default=False),
    full_ride_only: bool = Query(default=False),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = user.profile
    achievements = (
        db.query(Achievement).filter(Achievement.user_id == user.id).all()
    )

    universities_query = db.query(University).filter(
        University.is_active == True,  # noqa: E712
        University.selectivity_score.isnot(None),
    )
    if country:
        universities_query = universities_query.filter(University.country == country)
    if common_app_only:
        universities_query = universities_query.filter(University.is_common_app == True)  # noqa: E712
    if full_ride_only:
        universities_query = universities_query.filter(University.full_ride_possible == True)  # noqa: E712

    universities = universities_query.all()

    output = generate_advisor_output(
        profile=profile,
        achievements=achievements,
        universities=universities,
        limit_per_bracket=limit_per_bracket,
    )

    payload = AdvisorBracketsOut(
        summary=output.summary,
        transparency_note=output.transparency_note,
        profile_strength=ProfileStrengthOut(
            score=output.profile_strength.score,
            band=output.profile_strength.band,
            test_component=output.profile_strength.test_component,
            achievement_component=output.profile_strength.achievement_component,
            curriculum_component=output.profile_strength.curriculum_component,
            major_fit_component=output.profile_strength.major_fit_component,
            notes=output.profile_strength.notes,
            summary=output.profile_strength.summary(),
        ),
        stretch=[_to_fit_out(f) for f in _bracket_subset(output, "stretch")],
        realistic=[_to_fit_out(f) for f in _bracket_subset(output, "realistic")],
        safety=[_to_fit_out(f) for f in _bracket_subset(output, "safety")],
        profile_actions=[
            ProfileActionOut(
                title=a.title,
                description=a.description,
                priority=a.priority,
                category=a.category,
                transparency_note=a.transparency_note,
            )
            for a in output.profile_actions
        ],
    )
    return {"data": payload.model_dump(), "message": "Advisor brackets generated"}


def _to_fit_out(fit: UniversityFit) -> UniversityFitOut:
    return UniversityFitOut(
        university_id=fit.university_id,
        slug=fit.slug,
        name=fit.name,
        country=fit.country,
        bracket=fit.bracket,
        fit_score=fit.fit_score,
        selectivity_score=fit.selectivity_score,
        aid_strength=fit.aid_strength,
        application_system=fit.application_system,
        teaching_languages=fit.teaching_languages,
        major_strengths=fit.major_strengths,
        full_ride_possible=fit.full_ride_possible,
        rationale=fit.rationale,
        transparency_note=fit.transparency_note,
    )
