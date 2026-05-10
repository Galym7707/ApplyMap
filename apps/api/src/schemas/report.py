from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from ..models.report import (
    ConfidenceLabel,
    RecommendationType,
    ReportStatus,
    SourceClassification,
    SourceSection,
)
from .achievement import AchievementOut
from .university import UniversityListOut, PolicyEntryOut


class TargetUniversityCreate(BaseModel):
    university_id: UUID
    priority_order: Optional[int] = None
    fit_category: str = "target"


class TargetUniversityOut(BaseModel):
    id: UUID
    user_id: UUID
    university_id: UUID
    priority_order: Optional[int] = None
    fit_category: str = "target"
    created_at: datetime
    university: UniversityListOut

    model_config = {"from_attributes": True}


class RecommendationOut(BaseModel):
    id: UUID
    report_id: UUID
    achievement_id: UUID
    recommendation_type: RecommendationType
    suggested_rank: Optional[int] = None
    rationale: Optional[str] = None
    confidence_label: ConfidenceLabel
    source_classification: SourceClassification = SourceClassification.system_suggestion
    transparency_note: Optional[str] = None
    created_at: datetime
    achievement: AchievementOut

    model_config = {"from_attributes": True}


class RewriteVariantOut(BaseModel):
    id: UUID
    achievement_id: UUID
    report_id: UUID
    style_mode: str
    text: str
    character_count: int
    is_recommended: bool
    explanation: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceReferenceOut(BaseModel):
    id: UUID
    report_id: UUID
    university_policy_entry_id: UUID
    section: SourceSection
    note: Optional[str] = None
    created_at: datetime
    policy_entry: PolicyEntryOut

    model_config = {"from_attributes": True}


class AdvisorProgramOut(BaseModel):
    name: str
    why_it_matters: str
    funding_note: str
    priority: str


class AdvisorActionOut(BaseModel):
    title: str
    detail: str


class AdvisorSnapshotOut(BaseModel):
    title: str
    subtitle: str
    target_major: str
    report_note: str
    focus_areas: List[str] = []
    research_programs: List[AdvisorProgramOut] = []
    funding_plan: List[str] = []
    action_plan: List[AdvisorActionOut] = []


class ReportOut(BaseModel):
    id: UUID
    user_id: UUID
    university_id: UUID
    status: ReportStatus
    summary_text: Optional[str] = None
    advisor_snapshot_json: Optional[AdvisorSnapshotOut] = None
    version_number: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    university: UniversityListOut

    model_config = {"from_attributes": True}


class ReportDetailOut(ReportOut):
    recommendations: List[RecommendationOut] = []
    rewrite_variants: List[RewriteVariantOut] = []
    source_references: List[SourceReferenceOut] = []

    model_config = {"from_attributes": True}
