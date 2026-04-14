import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Enum, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from ..database import Base


class AchievementType(str, enum.Enum):
    activity = "activity"
    honor = "honor"


class ImpactScope(str, enum.Enum):
    school = "school"
    local = "local"
    regional = "regional"
    national = "national"
    international = "international"
    family = "family"
    personal = "personal"


class LeadershipLevel(str, enum.Enum):
    none = "none"
    member = "member"
    lead = "lead"
    founder = "founder"
    captain = "captain"


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    type = Column(Enum(AchievementType), nullable=False)
    title = Column(String(500), nullable=False)
    organization_name = Column(String(255), nullable=True)
    role_title = Column(String(255), nullable=True)
    description_raw = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # e.g. "Science", "Arts", "Community Service"

    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    hours_per_week = Column(Float, nullable=True)
    weeks_per_year = Column(Integer, nullable=True)

    impact_scope = Column(Enum(ImpactScope), nullable=True)
    leadership_level = Column(Enum(LeadershipLevel), nullable=True)

    # Computed Chancellor scores (0-10)
    major_relevance_score = Column(Float, nullable=True)
    continuity_score = Column(Float, nullable=True)
    selectivity_score = Column(Float, nullable=True)
    distinctiveness_score = Column(Float, nullable=True)

    truth_risk_flag = Column(Boolean, nullable=True, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="achievements")
    evidence_files = relationship("AchievementEvidenceFile", back_populates="achievement", cascade="all, delete-orphan")
    recommendations = relationship("ReportRecommendation", back_populates="achievement", cascade="all, delete-orphan")
    rewrite_variants = relationship("RewriteVariant", back_populates="achievement", cascade="all, delete-orphan")


class AchievementEvidenceFile(Base):
    __tablename__ = "achievement_evidence_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_url = Column(String(1000), nullable=False)
    file_name = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    achievement = relationship("Achievement", back_populates="evidence_files")
    user = relationship("User", back_populates="evidence_files")
