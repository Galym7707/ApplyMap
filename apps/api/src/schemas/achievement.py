from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from ..models.achievement import AchievementType, ImpactScope, LeadershipLevel


class AchievementCreate(BaseModel):
    type: AchievementType
    title: str = Field(max_length=500)
    organization_name: Optional[str] = Field(None, max_length=255)
    role_title: Optional[str] = Field(None, max_length=255)
    description_raw: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hours_per_week: Optional[float] = Field(None, ge=0, le=168)
    weeks_per_year: Optional[int] = Field(None, ge=0, le=52)
    impact_scope: Optional[ImpactScope] = None
    leadership_level: Optional[LeadershipLevel] = None
    truth_risk_flag: Optional[bool] = None


class AchievementUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    organization_name: Optional[str] = Field(None, max_length=255)
    role_title: Optional[str] = Field(None, max_length=255)
    description_raw: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hours_per_week: Optional[float] = Field(None, ge=0, le=168)
    weeks_per_year: Optional[int] = Field(None, ge=0, le=52)
    impact_scope: Optional[ImpactScope] = None
    leadership_level: Optional[LeadershipLevel] = None
    truth_risk_flag: Optional[bool] = None


class AchievementShortlistRequest(BaseModel):
    word_limit: int = Field(22, ge=5, le=40)


class EvidenceFileOut(BaseModel):
    id: UUID
    file_url: str
    file_name: str
    mime_type: Optional[str] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class AchievementOut(BaseModel):
    id: UUID
    user_id: UUID
    type: AchievementType
    title: str
    organization_name: Optional[str] = None
    role_title: Optional[str] = None
    description_raw: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hours_per_week: Optional[float] = None
    weeks_per_year: Optional[int] = None
    impact_scope: Optional[ImpactScope] = None
    leadership_level: Optional[LeadershipLevel] = None
    major_relevance_score: Optional[float] = None
    continuity_score: Optional[float] = None
    selectivity_score: Optional[float] = None
    distinctiveness_score: Optional[float] = None
    truth_risk_flag: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    evidence_files: List[EvidenceFileOut] = []

    model_config = {"from_attributes": True}


class AchievementImportSelectionItem(BaseModel):
    achievement_id: UUID
    type: AchievementType
    rank: int
    title: str
    common_app_text: str
    word_count: int
    character_count: int
    common_app_position: Optional[str] = None
    common_app_organization: Optional[str] = None
    common_app_activity_type: Optional[str] = None
    common_app_activity_description: Optional[str] = None
    common_app_activity_grade_levels: Optional[str] = None
    common_app_activity_participation_timing: Optional[str] = None
    common_app_activity_hours_per_week: Optional[str] = None
    common_app_activity_weeks_per_year: Optional[str] = None
    common_app_activity_continue: Optional[str] = None
    common_app_honor_description: Optional[str] = None
    common_app_honor_level: Optional[str] = None
    common_app_honor_grade_levels: Optional[str] = None
    position_character_count: Optional[int] = None
    organization_character_count: Optional[int] = None
    activity_description_character_count: Optional[int] = None
    honor_character_count: Optional[int] = None
    selection_reason: Optional[str] = None
    verification_notes: List[str] = []
    missing_or_unclear_facts: List[str] = []


class AchievementImportStep(BaseModel):
    key: str
    label: str
    status: str
    detail: str


class AchievementImportOut(BaseModel):
    file_name: str
    word_limit: int
    imported_count: int
    strongest_angle: str
    needs_student_clarification: bool = False
    clarifying_questions: List[str] = []
    additional_information_recommended: bool = False
    additional_information_reason: Optional[str] = None
    additional_information_draft: Optional[str] = None
    formatting_notes: List[str] = []
    extraction_notes: List[str] = []
    source_excerpts: List[str] = []
    processing_steps: List[AchievementImportStep] = []
    imported_achievements: List[AchievementOut]
    top_activities: List[AchievementImportSelectionItem]
    top_honors: List[AchievementImportSelectionItem]
