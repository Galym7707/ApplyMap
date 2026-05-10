"""Phase 1 + 3 + 10 foundation: activity categorization, scholarships, transparency.

- Adds `activity_category` and `activity_role` columns to `achievements`.
- Adds `source_classification` and `transparency_note` columns to
  `report_recommendations`.
- Creates the `scholarships` table.

Revision ID: 002
Revises: 001
Create Date: 2026-05-10 11:30:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ACTIVITY_CATEGORY_VALUES = (
    "academic",
    "leadership",
    "service",
    "family_responsibility",
    "paid_work",
    "volunteering",
    "community_initiative",
    "research",
    "business",
    "technical",
    "arts",
    "athletics",
    "religious",
    "other",
)
ACTIVITY_ROLE_VALUES = ("anchor", "supporting", "contextual")
SOURCE_CLASSIFICATION_VALUES = ("official", "public_example", "system_suggestion")
SCHOLARSHIP_SCOPE_VALUES = ("institution", "country", "international", "private")
FUNDING_COVERAGE_VALUES = (
    "full_ride",
    "full_tuition",
    "partial_tuition",
    "living_stipend",
    "travel_grant",
    "other",
)


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    activity_category_type = sa.Enum(
        *ACTIVITY_CATEGORY_VALUES, name="activitycategory"
    )
    activity_role_type = sa.Enum(*ACTIVITY_ROLE_VALUES, name="activityrole")
    source_classification_type = sa.Enum(
        *SOURCE_CLASSIFICATION_VALUES, name="sourceclassification"
    )
    scholarship_scope_type = sa.Enum(
        *SCHOLARSHIP_SCOPE_VALUES, name="scholarshipscope"
    )
    funding_coverage_type = sa.Enum(
        *FUNDING_COVERAGE_VALUES, name="fundingcoverage"
    )

    if is_postgres:
        activity_category_type.create(bind, checkfirst=True)
        activity_role_type.create(bind, checkfirst=True)
        source_classification_type.create(bind, checkfirst=True)
        scholarship_scope_type.create(bind, checkfirst=True)
        funding_coverage_type.create(bind, checkfirst=True)

    op.add_column(
        "achievements",
        sa.Column("activity_category", activity_category_type, nullable=True),
    )
    op.add_column(
        "achievements",
        sa.Column("activity_role", activity_role_type, nullable=True),
    )

    op.add_column(
        "report_recommendations",
        sa.Column(
            "source_classification",
            source_classification_type,
            nullable=False,
            server_default="system_suggestion",
        ),
    )
    op.add_column(
        "report_recommendations",
        sa.Column("transparency_note", sa.Text(), nullable=True),
    )

    op.create_table(
        "scholarships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(150), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sponsor", sa.String(255), nullable=True),
        sa.Column("scope", scholarship_scope_type, nullable=False, server_default="international"),
        sa.Column("coverage", funding_coverage_type, nullable=False, server_default="other"),
        sa.Column(
            "university_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("universities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("eligible_countries", postgresql.JSONB if is_postgres else sa.JSON, nullable=True),
        sa.Column("eligible_levels", postgresql.JSONB if is_postgres else sa.JSON, nullable=True),
        sa.Column("intended_majors", postgresql.JSONB if is_postgres else sa.JSON, nullable=True),
        sa.Column("minimum_test_scores", postgresql.JSONB if is_postgres else sa.JSON, nullable=True),
        sa.Column("eligibility_criteria", sa.Text(), nullable=True),
        sa.Column("estimated_amount_usd", sa.Integer(), nullable=True),
        sa.Column("estimated_amount_note", sa.String(255), nullable=True),
        sa.Column("application_deadline", sa.Date(), nullable=True),
        sa.Column("application_url", sa.String(1000), nullable=True),
        sa.Column("requires_essay", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_recommendation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_interview", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("source_title", sa.String(500), nullable=True),
        sa.Column("last_verified_at", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_scholarships_university_id", "scholarships", ["university_id"])
    op.create_index("ix_scholarships_slug", "scholarships", ["slug"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    op.drop_index("ix_scholarships_slug", table_name="scholarships")
    op.drop_index("ix_scholarships_university_id", table_name="scholarships")
    op.drop_table("scholarships")

    op.drop_column("report_recommendations", "transparency_note")
    op.drop_column("report_recommendations", "source_classification")

    op.drop_column("achievements", "activity_role")
    op.drop_column("achievements", "activity_category")

    if is_postgres:
        for enum_name in (
            "fundingcoverage",
            "scholarshipscope",
            "sourceclassification",
            "activityrole",
            "activitycategory",
        ):
            op.execute(f"DROP TYPE IF EXISTS {enum_name}")
