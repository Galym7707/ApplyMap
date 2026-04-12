from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from ..models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    country: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    country: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    email: str
    role: UserRole
    full_name: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileCreate(BaseModel):
    graduation_year: Optional[int] = None
    curriculum: Optional[str] = None
    intended_major: Optional[str] = None
    sat_score: Optional[int] = None
    act_score: Optional[int] = None
    ielts_score: Optional[str] = None
    toefl_score: Optional[int] = None
    budget_range: Optional[str] = None
    aid_needed: Optional[bool] = None


class ProfileUpdate(ProfileCreate):
    pass


class ProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    graduation_year: Optional[int] = None
    curriculum: Optional[str] = None
    intended_major: Optional[str] = None
    sat_score: Optional[int] = None
    act_score: Optional[int] = None
    ielts_score: Optional[str] = None
    toefl_score: Optional[int] = None
    budget_range: Optional[str] = None
    aid_needed: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
