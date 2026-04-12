import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from ..database import Base


class UserRole(str, enum.Enum):
    student = "student"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # nullable for OAuth users
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    full_name = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    target_universities = relationship("TargetUniversity", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("OptimizationReport", back_populates="user", cascade="all, delete-orphan")
    evidence_files = relationship("AchievementEvidenceFile", back_populates="user", cascade="all, delete-orphan")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    graduation_year = Column(Integer, nullable=True)
    curriculum = Column(String(100), nullable=True)  # IB, AP, A-Level, etc.
    intended_major = Column(String(255), nullable=True)

    # Test scores
    sat_score = Column(Integer, nullable=True)
    act_score = Column(Integer, nullable=True)
    ielts_score = Column(String(10), nullable=True)  # e.g. "7.5"
    toefl_score = Column(Integer, nullable=True)

    # Financial
    budget_range = Column(String(100), nullable=True)  # e.g. "50k-75k"
    aid_needed = Column(Boolean, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="profile")
