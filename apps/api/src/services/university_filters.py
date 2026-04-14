from typing import Any, Iterable

from ..models.university import University


def enrich_university(university: University) -> dict[str, Any]:
    return {
        "id": university.id,
        "slug": university.slug,
        "name": university.name,
        "country": university.country,
        "application_system": university.application_system,
        "application_source_url": university.application_source_url,
        "short_description": university.short_description,
        "weight_preset": university.weight_preset,
        "is_active": university.is_active,
        "region": university.region,
        "city": university.city,
        "is_common_app": university.is_common_app,
        "teaching_languages": university.teaching_languages or [],
        "major_strengths": university.major_strengths or [],
        "education_years_required": university.education_years_required,
        "school_years_note": university.school_years_note,
        "aid_type": university.aid_type,
        "aid_strength": university.aid_strength,
        "selectivity_score": university.selectivity_score,
        "full_ride_possible": university.full_ride_possible,
        "full_tuition_possible": university.full_tuition_possible,
        "aid_notes": university.aid_notes,
        "funding_source_url": university.funding_source_url,
        "funding_source_title": university.funding_source_title,
        "eligibility_notes": university.eligibility_notes,
        "created_at": university.created_at,
        "updated_at": university.updated_at,
    }


def filter_universities(
    universities: Iterable[dict[str, Any]],
    *,
    search: str | None = None,
    country: str | None = None,
    region: str | None = None,
    application_system: str | None = None,
    teaching_language: str | None = None,
    major: str | None = None,
    school_years: int | None = None,
    full_ride_only: bool = False,
    common_app_only: bool = False,
    aid_type: str | None = None,
    sort_by: str = "name",
    sort_dir: str = "asc",
) -> list[dict[str, Any]]:
    result = list(universities)

    if search:
        needle = search.lower()
        result = [
            item for item in result
            if needle in item["name"].lower()
            or needle in (item.get("country") or "").lower()
            or needle in " ".join(item.get("major_strengths") or []).lower()
        ]
    if country:
        result = [item for item in result if (item.get("country") or "").lower() == country.lower()]
    if region:
        result = [item for item in result if (item.get("region") or "").lower() == region.lower()]
    if application_system:
        needle = application_system.lower()
        result = [item for item in result if needle in (item.get("application_system") or "").lower()]
    if teaching_language:
        result = [
            item for item in result
            if teaching_language.lower() in [language.lower() for language in item.get("teaching_languages") or []]
        ]
    if major:
        major_needle = major.lower()
        result = [
            item for item in result
            if major_needle in " ".join(item.get("major_strengths") or []).lower()
        ]
    if school_years:
        result = [
            item for item in result
            if not item.get("education_years_required")
            or int(item["education_years_required"]) <= school_years
        ]
    if full_ride_only:
        result = [item for item in result if item.get("full_ride_possible")]
    if common_app_only:
        result = [item for item in result if item.get("is_common_app")]
    if aid_type:
        result = [item for item in result if item.get("aid_type") == aid_type]

    sort_key = sort_by if sort_by in {"name", "country", "aid_strength", "selectivity_score", "education_years_required"} else "name"
    reverse = sort_dir == "desc"
    return sorted(result, key=lambda item: (item.get(sort_key) is None, item.get(sort_key)), reverse=reverse)
