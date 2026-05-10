from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.scholarship import FundingCoverage, Scholarship, ScholarshipScope
from ..schemas.scholarship import ScholarshipOut

router = APIRouter(prefix="/api/scholarships", tags=["scholarships"])


@router.get("", response_model=dict)
def list_scholarships(
    country: Optional[str] = Query(
        None,
        description="ISO country code; matches scholarships explicitly listing the country or marked WORLDWIDE.",
    ),
    level: Optional[str] = Query(
        None, description="undergraduate | graduate"
    ),
    coverage: Optional[FundingCoverage] = None,
    scope: Optional[ScholarshipScope] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Scholarship).filter(Scholarship.is_active == True)  # noqa: E712
    if coverage:
        query = query.filter(Scholarship.coverage == coverage)
    if scope:
        query = query.filter(Scholarship.scope == scope)

    items = query.order_by(Scholarship.name).all()

    if country:
        country_code = country.upper()
        items = [
            item
            for item in items
            if (item.eligible_countries or [])
            and (
                country_code in item.eligible_countries
                or "WORLDWIDE" in item.eligible_countries
            )
        ]
    if level:
        level_lower = level.lower()
        items = [
            item
            for item in items
            if not item.eligible_levels or level_lower in item.eligible_levels
        ]
    if search:
        needle = search.lower()
        items = [
            item
            for item in items
            if needle in (item.name or "").lower()
            or needle in (item.sponsor or "").lower()
            or needle in (item.eligibility_criteria or "").lower()
        ]

    return {
        "data": [ScholarshipOut.model_validate(item).model_dump(mode="json") for item in items],
        "message": "OK",
    }
