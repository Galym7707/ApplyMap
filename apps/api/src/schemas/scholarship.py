from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from ..models.scholarship import FundingCoverage, ScholarshipScope


class ScholarshipOut(BaseModel):
    id: UUID
    slug: str
    name: str
    sponsor: Optional[str] = None
    scope: ScholarshipScope
    coverage: FundingCoverage
    university_id: Optional[UUID] = None
    eligible_countries: Optional[list[str]] = None
    eligible_levels: Optional[list[str]] = None
    intended_majors: Optional[list[str]] = None
    minimum_test_scores: Optional[dict[str, Any]] = None
    eligibility_criteria: Optional[str] = None
    estimated_amount_usd: Optional[int] = None
    estimated_amount_note: Optional[str] = None
    application_deadline: Optional[date] = None
    application_url: Optional[str] = None
    requires_essay: bool = False
    requires_recommendation: bool = False
    requires_interview: bool = False
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    last_verified_at: Optional[date] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
