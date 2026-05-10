import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from ..database import Base


class ReportStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class RecommendationType(str, enum.Enum):
    keep = "keep"
    remove = "remove"
    merge = "merge"
    rewrite = "rewrite"
    reorder = "reorder"


class ConfidenceLabel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class SourceSection(str, enum.Enum):
    official_guidance = "official_guidance"
    public_examples = "public_examples"
    recommendation_support = "recommendation_support"


class SourceClassification(str, enum.Enum):
    """Where a recommendation's evidence comes from.

    Used to keep ApplyMap honest: official policies vs. public examples
    vs. system-derived heuristics must never be presented the same way.
    """

    official = "official"
    public_example = "public_example"
    system_suggestion = "system_suggestion"


class TargetUniversity(Base):
    __tablename__ = "target_universities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    university_id = Column(UUID(as_uuid=True), ForeignKey("universities.id", ondelete="CASCADE"), nullable=False)
    priority_order = Column(Integer, nullable=True)
    fit_category = Column(String(20), default="target", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="target_universities")
    university = relationship("University", back_populates="target_universities")


class OptimizationReport(Base):
    __tablename__ = "optimization_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    university_id = Column(UUID(as_uuid=True), ForeignKey("universities.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.pending, nullable=False)
    summary_text = Column(Text, nullable=True)
    advisor_snapshot_json = Column(JSON, nullable=True)
    version_number = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="reports")
    university = relationship("University", back_populates="reports")
    recommendations = relationship("ReportRecommendation", back_populates="report", cascade="all, delete-orphan")
    rewrite_variants = relationship("RewriteVariant", back_populates="report", cascade="all, delete-orphan")
    source_references = relationship("SourceReference", back_populates="report", cascade="all, delete-orphan")


class ReportRecommendation(Base):
    __tablename__ = "report_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("optimization_reports.id", ondelete="CASCADE"), nullable=False)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    recommendation_type = Column(Enum(RecommendationType), nullable=False)
    suggested_rank = Column(Integer, nullable=True)
    rationale = Column(Text, nullable=True)
    confidence_label = Column(Enum(ConfidenceLabel), nullable=False, default=ConfidenceLabel.medium)
    source_classification = Column(
        Enum(SourceClassification),
        nullable=False,
        default=SourceClassification.system_suggestion,
    )
    transparency_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    report = relationship("OptimizationReport", back_populates="recommendations")
    achievement = relationship("Achievement", back_populates="recommendations")


class RewriteVariant(Base):
    __tablename__ = "rewrite_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey("optimization_reports.id", ondelete="CASCADE"), nullable=False)
    style_mode = Column(String(50), nullable=False)  # factual, impact_first, understated
    text = Column(Text, nullable=False)
    character_count = Column(Integer, nullable=False)
    is_recommended = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    achievement = relationship("Achievement", back_populates="rewrite_variants")
    report = relationship("OptimizationReport", back_populates="rewrite_variants")


class SourceReference(Base):
    __tablename__ = "source_references"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("optimization_reports.id", ondelete="CASCADE"), nullable=False)
    university_policy_entry_id = Column(UUID(as_uuid=True), ForeignKey("university_policy_entries.id", ondelete="CASCADE"), nullable=False)
    section = Column(Enum(SourceSection), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    report = relationship("OptimizationReport", back_populates="source_references")
    policy_entry = relationship("UniversityPolicyEntry", back_populates="source_references")


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
