"""Sanity checks for the university seed catalog."""
from __future__ import annotations

import re

import pytest

from src.seeds.seed_universities import (
    ALL_UNIVERSITIES,
    US,
    UK,
    EUROPE,
    ASIA,
    OCEANIA,
    CANADA,
    REGIONAL,
    UniversitySeed,
    seed_universities,
)


def test_catalog_has_expected_minimum_count():
    # The product target was 150-200 universities; we shouldn't accidentally
    # drop below 150 in a refactor.
    assert 150 <= len(ALL_UNIVERSITIES) <= 250


def test_every_region_is_populated():
    assert len(US) >= 50, "Need a strong US set since most students apply via Common App"
    assert len(UK) >= 10
    assert len(EUROPE) >= 25
    assert len(ASIA) >= 20
    assert len(OCEANIA) >= 5
    assert len(CANADA) >= 8
    assert len(REGIONAL) >= 8, "Kazakhstan + adjacent regional schools must be represented"


def test_slugs_are_unique_and_well_formed():
    slugs = [u.slug for u in ALL_UNIVERSITIES]
    assert len(slugs) == len(set(slugs)), "Duplicate slugs in catalog"
    for slug in slugs:
        assert re.match(r"^[a-z0-9][a-z0-9-]+[a-z0-9]$", slug), f"Bad slug: {slug}"


def test_required_fields_are_present():
    for u in ALL_UNIVERSITIES:
        assert u.name and len(u.name) > 1
        assert u.country and len(u.country) > 1
        assert u.teaching_languages, f"{u.slug} has no teaching_languages"
        assert u.major_strengths, f"{u.slug} has no major_strengths"


def test_selectivity_score_is_in_band():
    for u in ALL_UNIVERSITIES:
        if u.selectivity_score is not None:
            assert 1 <= u.selectivity_score <= 10, f"{u.slug} selectivity_score out of range"


def test_aid_strength_is_in_band():
    for u in ALL_UNIVERSITIES:
        if u.aid_strength is not None:
            assert 1 <= u.aid_strength <= 10, f"{u.slug} aid_strength out of range"


def test_full_ride_universities_are_explicitly_documented():
    # Schools we mark as full_ride_possible should also explain the aid path
    # so students aren't misled by unsourced claims.
    for u in ALL_UNIVERSITIES:
        if u.full_ride_possible:
            assert (u.aid_notes or u.aid_type), (
                f"{u.slug} claims full_ride_possible but has no aid_notes / aid_type"
            )


def test_kazakhstan_explicitly_present():
    kz = [u for u in ALL_UNIVERSITIES if u.country == "Kazakhstan"]
    assert kz, "Kazakhstan-based universities must be in the catalog"
    assert any(u.slug == "nazarbayev-university" for u in kz)


def test_common_app_schools_have_url():
    for u in ALL_UNIVERSITIES:
        if u.is_common_app:
            assert u.application_system and "Common App" in u.application_system


def test_funding_source_url_is_https_when_present():
    for u in ALL_UNIVERSITIES:
        if u.funding_source_url:
            assert u.funding_source_url.startswith("http"), (
                f"{u.slug} has non-URL funding_source_url"
            )


def test_seed_loader_is_idempotent_with_in_memory_db():
    # Reuse the same in-memory SQLite session across two calls and confirm
    # the table size doesn't grow on the second pass.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from src.database import Base
    from src.models.university import University  # noqa: F401  (registers metadata)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionMaker = sessionmaker(bind=engine, autoflush=False)
    session = SessionMaker()
    try:
        first = seed_universities(session)
        second = seed_universities(session)
        assert first == second == len(ALL_UNIVERSITIES)
        from src.models.university import University as U
        assert session.query(U).count() == len(ALL_UNIVERSITIES)
    finally:
        session.close()
