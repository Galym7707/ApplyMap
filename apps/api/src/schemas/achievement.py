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
    selection_reason: Optional[str] = None


class AchievementImportOut(BaseModel):
    file_name: str
    word_limit: int
    imported_count: int
    strongest_angle: str
    imported_achievements: List[AchievementOut]
    top_activities: List[AchievementImportSelectionItem]
    top_honors: List[AchievementImportSelectionItem]
