"""Scholarship model.

Stored separately from `University` because a single scholarship may apply to
many universities (e.g. Chevening, Erasmus Mundus, Fulbright) or to none in
particular (country-wide). The optional `university_id` link still lets us
attach school-specific named awards.
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class ScholarshipScope(str, enum.Enum):
    institution = "institution"
    country = "country"
    international = "international"
    private = "private"


class FundingCoverage(str, enum.Enum):
    full_ride = "full_ride"
    full_tuition = "full_tuition"
    partial_tuition = "partial_tuition"
    living_stipend = "living_stipend"
    travel_grant = "travel_grant"
    other = "other"


class Scholarship(Base):
    __tablename__ = "scholarships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(150), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sponsor = Column(String(255), nullable=True)

    scope = Column(Enum(ScholarshipScope), nullable=False, default=ScholarshipScope.international)
    coverage = Column(Enum(FundingCoverage), nullable=False, default=FundingCoverage.other)

    # Scholarships may be tied to a single university (e.g. Yale World
    # Scholar) or be country/private (kept null).
    university_id = Column(
        UUID(as_uuid=True),
        ForeignKey("universities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Eligibility and process metadata. Lists/dicts kept as JSON so we can
    # iterate quickly without a forest of side tables.
    eligible_countries = Column(JSON, nullable=True)  # list[str] ISO codes
    eligible_levels = Column(JSON, nullable=True)  # list[str]: undergraduate, graduate, ...
    intended_majors = Column(JSON, nullable=True)  # list[str]
    minimum_test_scores = Column(JSON, nullable=True)  # {"sat": 1400, "ielts": "7.0", ...}
    eligibility_criteria = Column(Text, nullable=True)

    estimated_amount_usd = Column(Integer, nullable=True)
    estimated_amount_note = Column(String(255), nullable=True)

    application_deadline = Column(Date, nullable=True)
    application_url = Column(String(1000), nullable=True)
    requires_essay = Column(Boolean, nullable=False, default=False)
    requires_recommendation = Column(Boolean, nullable=False, default=False)
    requires_interview = Column(Boolean, nullable=False, default=False)

    source_url = Column(String(1000), nullable=True)
    source_title = Column(String(500), nullable=True)
    last_verified_at = Column(Date, nullable=True)

    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    university = relationship("University", lazy="joined")
