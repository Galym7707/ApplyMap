from sqlalchemy import inspect, text

from .database import engine


def _ensure_enum_value(connection, enum_name: str, value: str) -> None:
    """Add a value to a Postgres enum if it doesn't exist."""
    if engine.dialect.name != "postgresql":
        return
    connection.execute(
        text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'")
    )


def ensure_application_schema() -> None:
    inspector = inspect(engine)
    student_profile_columns = {column["name"] for column in inspector.get_columns("student_profiles")}
    university_columns = {column["name"] for column in inspector.get_columns("universities")}
    report_columns = {column["name"] for column in inspector.get_columns("optimization_reports")}
    target_university_columns = {column["name"] for column in inspector.get_columns("target_universities")}
    achievement_columns = {column["name"] for column in inspector.get_columns("achievements")}
    recommendation_columns = {column["name"] for column in inspector.get_columns("report_recommendations")}
    existing_tables = set(inspector.get_table_names())

    if "application_preferences_json" not in student_profile_columns:
        column_type = "JSONB" if engine.dialect.name == "postgresql" else "JSON"
        with engine.begin() as connection:
            connection.execute(
                text(f"ALTER TABLE student_profiles ADD COLUMN application_preferences_json {column_type}")
            )

    student_profile_column_defs = {
        "sat_math": "INTEGER",
        "sat_ebrw": "INTEGER",
        "ielts_listening": "VARCHAR(10)",
        "ielts_reading": "VARCHAR(10)",
        "ielts_writing": "VARCHAR(10)",
        "ielts_speaking": "VARCHAR(10)",
        "toefl_reading": "INTEGER",
        "toefl_listening": "INTEGER",
        "toefl_speaking": "INTEGER",
        "toefl_writing": "INTEGER",
        "duolingo_score": "INTEGER",
        "a_level_subjects": "VARCHAR(500)",
        "a_level_predicted": "VARCHAR(255)",
        "ap_subjects": "VARCHAR(500)",
        "ib_predicted_score": "INTEGER",
        "unt_score": "INTEGER",
        "nis_grade12_certificate_gpa": "VARCHAR(50)",
    }
    missing_student_profile_columns = [
        (name, column_type)
        for name, column_type in student_profile_column_defs.items()
        if name not in student_profile_columns
    ]
    if missing_student_profile_columns:
        with engine.begin() as connection:
            for name, column_type in missing_student_profile_columns:
                connection.execute(text(f"ALTER TABLE student_profiles ADD COLUMN {name} {column_type}"))

    json_type = "JSONB" if engine.dialect.name == "postgresql" else "JSON"
    university_column_defs = {
        "application_source_url": "VARCHAR(1000)",
        "region": "VARCHAR(100)",
        "city": "VARCHAR(255)",
        "is_common_app": "BOOLEAN DEFAULT FALSE NOT NULL",
        "teaching_languages": json_type,
        "major_strengths": json_type,
        "education_years_required": "INTEGER",
        "school_years_note": "TEXT",
        "aid_type": "VARCHAR(100)",
        "aid_strength": "INTEGER",
        "selectivity_score": "INTEGER",
        "full_ride_possible": "BOOLEAN DEFAULT FALSE NOT NULL",
        "full_tuition_possible": "BOOLEAN DEFAULT FALSE NOT NULL",
        "aid_notes": "TEXT",
        "funding_source_url": "VARCHAR(1000)",
        "funding_source_title": "VARCHAR(500)",
        "eligibility_notes": "TEXT",
    }

    missing_university_columns = [
        (name, column_type)
        for name, column_type in university_column_defs.items()
        if name not in university_columns
    ]
    if missing_university_columns:
        with engine.begin() as connection:
            for name, column_type in missing_university_columns:
                connection.execute(text(f"ALTER TABLE universities ADD COLUMN {name} {column_type}"))

    if "advisor_snapshot_json" not in report_columns:
        with engine.begin() as connection:
            connection.execute(
                text(f"ALTER TABLE optimization_reports ADD COLUMN advisor_snapshot_json {json_type}")
            )

    if "fit_category" not in target_university_columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE target_universities ADD COLUMN fit_category VARCHAR(20) DEFAULT 'target' NOT NULL")
            )

    # New columns for activity categorization (Phase 1).
    achievement_column_defs = {
        "activity_category": "VARCHAR(40)",
        "activity_role": "VARCHAR(20)",
    }
    missing_achievement_columns = [
        (name, column_type)
        for name, column_type in achievement_column_defs.items()
        if name not in achievement_columns
    ]
    if missing_achievement_columns:
        with engine.begin() as connection:
            for name, column_type in missing_achievement_columns:
                connection.execute(
                    text(f"ALTER TABLE achievements ADD COLUMN {name} {column_type}")
                )

    # Transparency fields on report_recommendations (Phase 10).
    recommendation_column_defs = {
        "source_classification": "VARCHAR(40) DEFAULT 'system_suggestion' NOT NULL",
        "transparency_note": "TEXT",
    }
    missing_recommendation_columns = [
        (name, column_type)
        for name, column_type in recommendation_column_defs.items()
        if name not in recommendation_columns
    ]
    if missing_recommendation_columns:
        with engine.begin() as connection:
            for name, column_type in missing_recommendation_columns:
                connection.execute(
                    text(f"ALTER TABLE report_recommendations ADD COLUMN {name} {column_type}")
                )

    # Scholarships table (Phase 3 foundation).
    if "scholarships" not in existing_tables:
        json_column = "JSONB" if engine.dialect.name == "postgresql" else "JSON"
        uuid_pk = "UUID" if engine.dialect.name == "postgresql" else "VARCHAR(36)"
        uuid_fk = "UUID" if engine.dialect.name == "postgresql" else "VARCHAR(36)"
        with engine.begin() as connection:
            connection.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS scholarships (
                        id {uuid_pk} PRIMARY KEY,
                        slug VARCHAR(150) UNIQUE NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        sponsor VARCHAR(255),
                        scope VARCHAR(40) NOT NULL DEFAULT 'international',
                        coverage VARCHAR(40) NOT NULL DEFAULT 'other',
                        university_id {uuid_fk} REFERENCES universities(id) ON DELETE SET NULL,
                        eligible_countries {json_column},
                        eligible_levels {json_column},
                        intended_majors {json_column},
                        minimum_test_scores {json_column},
                        eligibility_criteria TEXT,
                        estimated_amount_usd INTEGER,
                        estimated_amount_note VARCHAR(255),
                        application_deadline DATE,
                        application_url VARCHAR(1000),
                        requires_essay BOOLEAN NOT NULL DEFAULT FALSE,
                        requires_recommendation BOOLEAN NOT NULL DEFAULT FALSE,
                        requires_interview BOOLEAN NOT NULL DEFAULT FALSE,
                        source_url VARCHAR(1000),
                        source_title VARCHAR(500),
                        last_verified_at DATE,
                        notes TEXT,
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    )
                    """
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_scholarships_university_id "
                    "ON scholarships(university_id)"
                )
            )
