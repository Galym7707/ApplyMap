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
    short_description: Optional[str] = None
    weight_preset: WeightPreset = WeightPreset.balanced_holistic
    is_active: bool = True


class UniversityUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=100)
    application_system: Optional[str] = None
    short_description: Optional[str] = None
    weight_preset: Optional[WeightPreset] = None
    is_active: Optional[bool] = None


class UniversityOut(BaseModel):
    id: UUID
    slug: str
    name: str
    country: str
    application_system: Optional[str] = None
    short_description: Optional[str] = None
    weight_preset: WeightPreset
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

    model_config = {"from_attributes": True}
