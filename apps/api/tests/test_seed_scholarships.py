"""Sanity tests for the scholarship seed data and idempotent loader."""
from __future__ import annotations

from src.models.scholarship import FundingCoverage, Scholarship, ScholarshipScope
from src.seeds.seed_scholarships import SCHOLARSHIPS, seed_scholarships


def test_seed_data_has_expected_minimum_count():
    assert len(SCHOLARSHIPS) >= 20, "Seed list should contain at least 20 scholarships"


def test_each_seed_entry_has_required_fields():
    seen_slugs = set()
    for seed in SCHOLARSHIPS:
        assert seed.slug, f"Missing slug for {seed.name}"
        assert seed.slug not in seen_slugs, f"Duplicate slug: {seed.slug}"
        seen_slugs.add(seed.slug)
        assert seed.name
        assert seed.sponsor
        assert seed.source_url, f"{seed.name}: source_url is required for transparency"
        assert seed.last_verified_at, f"{seed.name}: last_verified_at is required"
        assert isinstance(seed.scope, ScholarshipScope)
        assert isinstance(seed.coverage, FundingCoverage)


def test_seed_loader_is_idempotent(db_session):
    first = seed_scholarships(db_session)
    assert first == len(SCHOLARSHIPS)
    rows_after_first = db_session.query(Scholarship).count()

    # Re-running should not duplicate rows.
    second = seed_scholarships(db_session)
    rows_after_second = db_session.query(Scholarship).count()

    assert rows_after_first == rows_after_second
    assert second == len(SCHOLARSHIPS)
