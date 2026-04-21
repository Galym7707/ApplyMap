from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from ..models.university import WeightPreset, SourceType, ReliabilityTier


class PolicyEntryCreate(BaseModel):
    title: str = Field(max_length=500)
    content: str
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_type: SourceType
    reliability_tier: ReliabilityTier = ReliabilityTier.B
    excerpt: Optional[str] = None


class PolicyEntryUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_type: Optional[SourceType] = None
    reliability_tier: Optional[ReliabilityTier] = None
    excerpt: Optional[str] = None


class PolicyEntryOut(BaseModel):
    id: UUID
    university_id: UUID
    title: str
    content: str
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_type: SourceType
    reliability_tier: ReliabilityTier
    excerpt: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UniversityCreate(BaseModel):
    slug: str = Field(max_length=100)
    name: str = Field(max_length=255)
    country: str = Field(max_length=100)
    application_system: Optional[str] = None
    application_source_url: Optional[str] = None
    short_description: Optional[str] = None
    weight_preset: WeightPreset = WeightPreset.balanced_holistic
    region: Optional[str] = None
    city: Optional[str] = None
    is_common_app: bool = False
    teaching_languages: List[str] = []
    major_strengths: List[str] = []
    education_years_required: Optional[int] = None
    school_years_note: Optional[str] = None
    aid_type: Optional[str] = None
    aid_strength: Optional[int] = None
    selectivity_score: Optional[int] = None
    full_ride_possible: bool = False
    full_tuition_possible: bool = False
    aid_notes: Optional[str] = None
    funding_source_url: Optional[str] = None
    funding_source_title: Optional[str] = None
    eligibility_notes: Optional[str] = None
    is_active: bool = True


class UniversityUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=100)
    application_system: Optional[str] = None
    application_source_url: Optional[str] = None
    short_description: Optional[str] = None
    weight_preset: Optional[WeightPreset] = None
    region: Optional[str] = None
    city: Optional[str] = None
    is_common_app: Optional[bool] = None
    teaching_languages: Optional[List[str]] = None
    major_strengths: Optional[List[str]] = None
    education_years_required: Optional[int] = None
    school_years_note: Optional[str] = None
    aid_type: Optional[str] = None
    aid_strength: Optional[int] = None
    selectivity_score: Optional[int] = None
    full_ride_possible: Optional[bool] = None
    full_tuition_possible: Optional[bool] = None
    aid_notes: Optional[str] = None
    funding_source_url: Optional[str] = None
    funding_source_title: Optional[str] = None
    eligibility_notes: Optional[str] = None
    is_active: Optional[bool] = None


class UniversityOut(BaseModel):
    id: UUID
    slug: str
    name: str
    country: str
    application_system: Optional[str] = None
    application_source_url: Optional[str] = None
    short_description: Optional[str] = None
    weight_preset: WeightPreset
    region: Optional[str] = None
    city: Optional[str] = None
    is_common_app: bool = False
    teaching_languages: List[str] = []
    major_strengths: List[str] = []
    education_years_required: Optional[int] = None
    school_years_note: Optional[str] = None
    aid_type: Optional[str] = None
    aid_strength: Optional[int] = None
    selectivity_score: Optional[int] = None
    full_ride_possible: bool = False
    full_tuition_possible: bool = False
    aid_notes: Optional[str] = None
    funding_source_url: Optional[str] = None
    funding_source_title: Optional[str] = None
    eligibility_notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    policy_entries: List[PolicyEntryOut] = []

    model_config = {"from_attributes": True}


class UniversityListOut(BaseModel):
    id: UUID
    slug: str
    name: str
    country: str
    application_system: Optional[str] = None
    short_description: Optional[str] = None
    weight_preset: WeightPreset
    is_active: bool
    region: Optional[str] = None
    city: Optional[str] = None
    is_common_app: bool = False
    application_source_url: Optional[str] = None
    teaching_languages: List[str] = []
    major_strengths: List[str] = []
    education_years_required: Optional[int] = None
    school_years_note: Optional[str] = None
    aid_type: Optional[str] = None
    aid_strength: Optional[int] = None
    selectivity_score: Optional[int] = None
    full_ride_possible: bool = False
    full_tuition_possible: bool = False
    aid_notes: Optional[str] = None
    funding_source_url: Optional[str] = None
    funding_source_title: Optional[str] = None
    eligibility_notes: Optional[str] = None

    model_config = {"from_attributes": True}


class CommonAppRecommendationRequest(BaseModel):
    top_honor_ids: List[UUID] = Field(default_factory=list, max_length=5)
    top_activity_ids: List[UUID] = Field(default_factory=list, max_length=10)
    preferences: dict = Field(default_factory=dict)
    save_preferences: bool = True


class UniversityAdvisorRequest(BaseModel):
    university_name: str = Field(min_length=2, max_length=255)
    intended_major: str = Field(min_length=2, max_length=255)


class CommonAppRecommendationOut(BaseModel):
    university_id: UUID
    slug: str
    name: str
    country: str
    category: str
    rationale: str
    fit_notes: Optional[str] = None
    aid_notes: Optional[str] = None
    funding_source_url: Optional[str] = None
