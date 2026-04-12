import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from ..database import Base


class WeightPreset(str, enum.Enum):
    research_heavy = "research_heavy"
    leadership_heavy = "leadership_heavy"
    balanced_holistic = "balanced_holistic"
    community_service_heavy = "community_service_heavy"


class SourceType(str, enum.Enum):
    official = "official"
    public_example = "public_example"


class ReliabilityTier(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class University(Base):
    __tablename__ = "universities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    application_system = Column(String(100), nullable=True)  # CommonApp, Coalition, etc.
    short_description = Column(Text, nullable=True)
    weight_preset = Column(Enum(WeightPreset), nullable=False, default=WeightPreset.balanced_holistic)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    policy_entries = relationship("UniversityPolicyEntry", back_populates="university", cascade="all, delete-orphan")
    target_universities = relationship("TargetUniversity", back_populates="university")
    reports = relationship("OptimizationReport", back_populates="university")


class UniversityPolicyEntry(Base):
    __tablename__ = "university_policy_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    university_id = Column(UUID(as_uuid=True), ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(1000), nullable=True)
    source_title = Column(String(500), nullable=True)
    source_type = Column(Enum(SourceType), nullable=False)
    reliability_tier = Column(Enum(ReliabilityTier), nullable=False, default=ReliabilityTier.B)
    excerpt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    university = relationship("University", back_populates="policy_entries")
    source_references = relationship("SourceReference", back_populates="policy_entry")
