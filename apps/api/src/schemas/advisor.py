"""Schemas for the deterministic stretch/realistic/safety advisor."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel


class ProfileStrengthOut(BaseModel):
    score: int
    band: int
    test_component: int
    achievement_component: int
    curriculum_component: int
    major_fit_component: int
    notes: List[str] = []
    summary: str


class UniversityFitOut(BaseModel):
    university_id: str
    slug: str
    name: str
    country: str
    bracket: Literal["stretch", "realistic", "safety"]
    fit_score: int
    selectivity_score: Optional[int] = None
    aid_strength: Optional[int] = None
    application_system: Optional[str] = None
    teaching_languages: List[str] = []
    major_strengths: List[str] = []
    full_ride_possible: bool = False
    rationale: List[str] = []
    transparency_note: str


class ProfileActionOut(BaseModel):
    title: str
    description: str
    priority: Literal["high", "medium", "low"]
    category: str
    transparency_note: str


class AdvisorBracketsOut(BaseModel):
    summary: str
    transparency_note: str
    profile_strength: ProfileStrengthOut
    stretch: List[UniversityFitOut]
    realistic: List[UniversityFitOut]
    safety: List[UniversityFitOut]
    profile_actions: List[ProfileActionOut]
