from sqlalchemy import inspect, text

from .database import engine


def ensure_application_schema() -> None:
    inspector = inspect(engine)
    student_profile_columns = {column["name"] for column in inspector.get_columns("student_profiles")}
    university_columns = {column["name"] for column in inspector.get_columns("universities")}
    report_columns = {column["name"] for column in inspector.get_columns("optimization_reports")}

    if "application_preferences_json" not in student_profile_columns:
        column_type = "JSONB" if engine.dialect.name == "postgresql" else "JSON"
        with engine.begin() as connection:
            connection.execute(
                text(f"ALTER TABLE student_profiles ADD COLUMN application_preferences_json {column_type}")
            )

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
