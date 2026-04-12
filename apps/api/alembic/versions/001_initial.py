"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("role", sa.Enum("student", "admin", name="userrole"), default="student", nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # student_profiles
    op.create_table(
        "student_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("graduation_year", sa.Integer, nullable=True),
        sa.Column("curriculum", sa.String(100), nullable=True),
        sa.Column("intended_major", sa.String(255), nullable=True),
        sa.Column("sat_score", sa.Integer, nullable=True),
        sa.Column("act_score", sa.Integer, nullable=True),
        sa.Column("ielts_score", sa.String(10), nullable=True),
        sa.Column("toefl_score", sa.Integer, nullable=True),
        sa.Column("budget_range", sa.String(100), nullable=True),
        sa.Column("aid_needed", sa.Boolean, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # universities
    op.create_table(
        "universities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("application_system", sa.String(100), nullable=True),
        sa.Column("short_description", sa.Text, nullable=True),
        sa.Column("weight_preset", sa.Enum("research_heavy", "leadership_heavy", "balanced_holistic", "community_service_heavy", name="weightpreset"), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_universities_slug", "universities", ["slug"])

    # university_policy_entries
    op.create_table(
        "university_policy_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("university_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("universities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("source_title", sa.String(500), nullable=True),
        sa.Column("source_type", sa.Enum("official", "public_example", name="sourcetype"), nullable=False),
        sa.Column("reliability_tier", sa.Enum("A", "B", "C", "D", name="reliabilitytier"), nullable=False),
        sa.Column("excerpt", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_university_policy_entries_university_id", "university_policy_entries", ["university_id"])

    # achievements
    op.create_table(
        "achievements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum("activity", "honor", name="achievementtype"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("organization_name", sa.String(255), nullable=True),
        sa.Column("role_title", sa.String(255), nullable=True),
        sa.Column("description_raw", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("hours_per_week", sa.Float, nullable=True),
        sa.Column("weeks_per_year", sa.Integer, nullable=True),
        sa.Column("impact_scope", sa.Enum("school", "local", "regional", "national", "international", "family", "personal", name="impactscope"), nullable=True),
        sa.Column("leadership_level", sa.Enum("none", "member", "lead", "founder", "captain", name="leadershiplevel"), nullable=True),
        sa.Column("major_relevance_score", sa.Float, nullable=True),
        sa.Column("continuity_score", sa.Float, nullable=True),
        sa.Column("selectivity_score", sa.Float, nullable=True),
        sa.Column("distinctiveness_score", sa.Float, nullable=True),
        sa.Column("truth_risk_flag", sa.Boolean, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_achievements_user_id", "achievements", ["user_id"])

    # achievement_evidence_files
    op.create_table(
        "achievement_evidence_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("achievement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_url", sa.String(1000), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("uploaded_at", sa.DateTime, nullable=False),
    )

    # target_universities
    op.create_table(
        "target_universities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("university_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("universities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("priority_order", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_target_universities_user_id", "target_universities", ["user_id"])

    # optimization_reports
    op.create_table(
        "optimization_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("university_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("universities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum("pending", "processing", "completed", "failed", name="reportstatus"), nullable=False),
        sa.Column("summary_text", sa.Text, nullable=True),
        sa.Column("version_number", sa.Integer, default=1, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_optimization_reports_user_id", "optimization_reports", ["user_id"])

    # report_recommendations
    op.create_table(
        "report_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("optimization_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("achievement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommendation_type", sa.Enum("keep", "remove", "merge", "rewrite", "reorder", name="recommendationtype"), nullable=False),
        sa.Column("suggested_rank", sa.Integer, nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("confidence_label", sa.Enum("low", "medium", "high", name="confidencelabel"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # rewrite_variants
    op.create_table(
        "rewrite_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("achievement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("optimization_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("style_mode", sa.String(50), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("character_count", sa.Integer, nullable=False),
        sa.Column("is_recommended", sa.Boolean, default=False),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # source_references
    op.create_table(
        "source_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("optimization_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("university_policy_entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("university_policy_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section", sa.Enum("official_guidance", "public_examples", "recommendation_support", name="sourcesection"), nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # admin_audit_logs
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("admin_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(255), nullable=True),
        sa.Column("metadata_json", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("admin_audit_logs")
    op.drop_table("source_references")
    op.drop_table("rewrite_variants")
    op.drop_table("report_recommendations")
    op.drop_table("optimization_reports")
    op.drop_table("target_universities")
    op.drop_table("achievement_evidence_files")
    op.drop_table("achievements")
    op.drop_table("university_policy_entries")
    op.drop_table("universities")
    op.drop_table("student_profiles")
    op.drop_table("users")
