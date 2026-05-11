"""Unit tests for the deterministic stretch / realistic / safety advisor."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import uuid

import pytest

from src.models.achievement import (
    Achievement,
    ActivityCategory,
    ActivityRole,
    ImpactScope,
    LeadershipLevel,
)
from src.models.university import University, WeightPreset
from src.services.admissions_advisor import (
    AdvisorOutput,
    ProfileStrength,
    compute_profile_strength,
    generate_advisor_output,
    rank_universities,
)


@dataclass
class FakeProfile:
    sat_score: Optional[int] = None
    act_score: Optional[int] = None
    ielts_score: Optional[str] = None
    toefl_score: Optional[int] = None
    duolingo_score: Optional[int] = None
    curriculum: Optional[str] = None
    intended_major: Optional[str] = None
    aid_needed: Optional[bool] = False
    country: Optional[str] = "Kazakhstan"


def _achievement(
    *,
    major_relevance: float | None = None,
    selectivity: float | None = None,
    continuity: float | None = None,
    distinctiveness: float | None = None,
    leadership: LeadershipLevel | None = None,
    impact: ImpactScope | None = None,
    category: ActivityCategory | None = None,
    role: ActivityRole | None = None,
) -> Achievement:
    a = Achievement(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        type="activity",
        title="Sample",
    )
    a.major_relevance_score = major_relevance
    a.selectivity_score = selectivity
    a.continuity_score = continuity
    a.distinctiveness_score = distinctiveness
    a.leadership_level = leadership
    a.impact_scope = impact
    a.activity_category = category
    a.activity_role = role
    return a


def _university(
    *,
    slug: str,
    name: str,
    country: str = "United States",
    selectivity: int | None = 7,
    aid_strength: int | None = 5,
    full_ride: bool = False,
    languages: list[str] | None = None,
    majors: list[str] | None = None,
    is_common_app: bool = False,
    application_system: str | None = "Common App",
) -> University:
    u = University()
    u.id = uuid.uuid4()
    u.slug = slug
    u.name = name
    u.country = country
    u.selectivity_score = selectivity
    u.aid_strength = aid_strength
    u.full_ride_possible = full_ride
    u.teaching_languages = languages or ["English"]
    u.major_strengths = majors or []
    u.is_common_app = is_common_app
    u.application_system = application_system
    u.is_active = True
    u.weight_preset = WeightPreset.balanced_holistic
    return u


# ---------------------------------------------------------------------------
# Profile strength
# ---------------------------------------------------------------------------

def test_profile_strength_with_no_profile_is_floor():
    strength = compute_profile_strength(profile=None, achievements=[])
    assert isinstance(strength, ProfileStrength)
    assert strength.score >= 0
    assert strength.band >= 1
    assert "No test scores" in strength.notes[0]


def test_strong_test_scores_lift_band():
    profile = FakeProfile(sat_score=1550, ielts_score="8.0", curriculum="IB", intended_major="Computer Science")
    achievements = [
        _achievement(major_relevance=9, selectivity=8, continuity=7, distinctiveness=7,
                     leadership=LeadershipLevel.founder, impact=ImpactScope.national,
                     category=ActivityCategory.research, role=ActivityRole.anchor)
        for _ in range(6)
    ]
    strength = compute_profile_strength(profile, achievements)
    assert strength.score >= 80
    assert strength.band >= 8


def test_weak_profile_lands_in_low_band():
    profile = FakeProfile(sat_score=1100, ielts_score="6.0", curriculum="general high school")
    strength = compute_profile_strength(profile, [])
    assert strength.score < 50
    assert strength.band <= 5


# ---------------------------------------------------------------------------
# Bracket assignment
# ---------------------------------------------------------------------------

def test_bracket_assignment_separates_stretch_realistic_safety():
    # A mid-band profile (≈band 6) should split a wide selectivity range into
    # all three brackets.
    profile = FakeProfile(sat_score=1300, ielts_score="6.5", curriculum="high school",
                          intended_major="Computer Science")
    achievements = [
        _achievement(major_relevance=5, selectivity=4, continuity=4, distinctiveness=4)
        for _ in range(3)
    ]
    universities = [
        _university(slug="harvard", name="Harvard", selectivity=10),       # stretch (delta +4)
        _university(slug="caltech", name="Caltech", selectivity=10),       # stretch (delta +4)
        _university(slug="duke", name="Duke", selectivity=9),              # stretch (delta +3)
        _university(slug="ucla", name="UCLA", selectivity=7),              # realistic (delta +1)
        _university(slug="bu", name="BU", selectivity=6),                  # realistic (delta 0)
        _university(slug="purdue", name="Purdue", selectivity=3),          # safety
        _university(slug="osu", name="OSU", selectivity=3),                # safety
    ]
    strength, fits = rank_universities(profile, achievements, universities)
    by_bracket = {b: [f.slug for f in fits if f.bracket == b]
                  for b in ("stretch", "realistic", "safety")}

    assert "harvard" in by_bracket["stretch"]
    assert "caltech" in by_bracket["stretch"]
    assert "duke" in by_bracket["stretch"]
    assert any(slug in by_bracket["safety"] for slug in ("purdue", "osu"))
    assert any(slug in by_bracket["realistic"] for slug in ("ucla", "bu"))


def test_major_fit_boosts_relevant_universities():
    profile = FakeProfile(sat_score=1450, ielts_score="7.5", curriculum="IB",
                          intended_major="Computer Science")
    universities = [
        _university(slug="cs-school", name="CS School", selectivity=8,
                    majors=["Computer Science", "Engineering"]),
        _university(slug="hum-school", name="Humanities School", selectivity=8,
                    majors=["Liberal Arts", "Humanities"]),
    ]
    strength, fits = rank_universities(profile, [_achievement(major_relevance=7)], universities)
    by_slug = {f.slug: f for f in fits}
    assert by_slug["cs-school"].fit_score > by_slug["hum-school"].fit_score


def test_aid_mismatch_drops_score_when_aid_needed():
    profile = FakeProfile(sat_score=1400, ielts_score="7.0", aid_needed=True,
                          curriculum="IB", intended_major="Engineering")
    universities = [
        _university(slug="generous", name="Generous Aid", selectivity=8,
                    aid_strength=9, majors=["Engineering"]),
        _university(slug="stingy", name="Stingy Aid", selectivity=8,
                    aid_strength=2, majors=["Engineering"]),
    ]
    strength, fits = rank_universities(profile, [_achievement(major_relevance=7)], universities)
    by_slug = {f.slug: f for f in fits}
    assert by_slug["generous"].fit_score > by_slug["stingy"].fit_score


def test_language_mismatch_lowers_score():
    profile = FakeProfile(sat_score=1450, ielts_score="7.0", curriculum="IB",
                          intended_major="Engineering")
    universities = [
        _university(slug="english-only", name="English School", selectivity=7,
                    languages=["English"], majors=["Engineering"]),
        _university(slug="french-only", name="French School", selectivity=7,
                    languages=["French"], majors=["Engineering"]),
    ]
    strength, fits = rank_universities(profile, [_achievement(major_relevance=7)], universities)
    by_slug = {f.slug: f for f in fits}
    assert by_slug["english-only"].fit_score > by_slug["french-only"].fit_score
    french_rationale = " ".join(by_slug["french-only"].rationale)
    assert "language" in french_rationale.lower() or "Teaching languages" in french_rationale


def test_inactive_universities_are_excluded():
    profile = FakeProfile(sat_score=1450, ielts_score="7.0")
    inactive = _university(slug="ghost", name="Ghost", selectivity=7)
    inactive.is_active = False
    universities = [inactive, _university(slug="alive", name="Alive", selectivity=7)]
    strength, fits = rank_universities(profile, [], universities)
    slugs = [f.slug for f in fits]
    assert "ghost" not in slugs
    assert "alive" in slugs


def test_universities_without_selectivity_are_skipped():
    profile = FakeProfile(sat_score=1450, ielts_score="7.0")
    universities = [
        _university(slug="missing", name="Missing", selectivity=None),
        _university(slug="present", name="Present", selectivity=7),
    ]
    strength, fits = rank_universities(profile, [], universities)
    slugs = [f.slug for f in fits]
    assert "missing" not in slugs
    assert "present" in slugs


# ---------------------------------------------------------------------------
# Profile actions
# ---------------------------------------------------------------------------

def test_missing_test_scores_produce_high_priority_actions():
    profile = FakeProfile(curriculum="IB", intended_major="Computer Science")
    output = generate_advisor_output(profile, [], [])
    titles = [a.title for a in output.profile_actions]
    priorities = {a.title: a.priority for a in output.profile_actions}
    assert any("SAT" in t or "ACT" in t for t in titles)
    assert any("English" in t or "IELTS" in t or "TOEFL" in t for t in titles)
    high_priority_titles = [t for t, p in priorities.items() if p == "high"]
    assert high_priority_titles, "Missing tests should produce at least one high-priority action"


def test_anchor_recommendation_when_role_missing():
    profile = FakeProfile(sat_score=1500, ielts_score="7.5", curriculum="IB",
                          intended_major="Computer Science")
    achievements = [
        _achievement(major_relevance=7, role=ActivityRole.contextual,
                     category=ActivityCategory.research)
    ]
    output = generate_advisor_output(profile, achievements, [])
    titles = [a.title for a in output.profile_actions]
    assert any("anchor" in t.lower() for t in titles)


def test_course_recommendation_for_cs_major():
    profile = FakeProfile(sat_score=1500, ielts_score="7.5", curriculum="IB",
                          intended_major="Computer Science")
    output = generate_advisor_output(profile, [], [])
    titles = [a.title for a in output.profile_actions]
    assert any("CS50" in t or "edX" in t or "Coursera" in t for t in titles)


def test_advisor_output_has_transparency_note():
    profile = FakeProfile(sat_score=1500, ielts_score="7.5", curriculum="IB",
                          intended_major="Computer Science")
    output = generate_advisor_output(profile, [], [_university(slug="x", name="X")])
    assert "system_suggestion" in output.transparency_note or "system suggestions" in output.transparency_note
    assert "verify" in output.transparency_note.lower() or "official" in output.transparency_note.lower()


def test_summary_reports_bracket_counts():
    profile = FakeProfile(sat_score=1450, ielts_score="7.0", curriculum="IB",
                          intended_major="Engineering")
    universities = [
        _university(slug="ivy", name="Ivy", selectivity=10),
        _university(slug="match", name="Match", selectivity=7),
        _university(slug="back", name="Backup", selectivity=4),
    ]
    output = generate_advisor_output(profile, [_achievement(major_relevance=7)], universities)
    assert "stretch" in output.summary
    assert "realistic" in output.summary
    assert "safety" in output.summary


def test_limit_per_bracket_is_respected():
    profile = FakeProfile(sat_score=1400, ielts_score="7.0", curriculum="IB",
                          intended_major="Engineering")
    # 10 stretch, 10 realistic, 10 safety candidates
    universities = (
        [_university(slug=f"st-{i}", name=f"Stretch {i}", selectivity=10) for i in range(10)]
        + [_university(slug=f"r-{i}", name=f"Realistic {i}", selectivity=7) for i in range(10)]
        + [_university(slug=f"sa-{i}", name=f"Safety {i}", selectivity=4) for i in range(10)]
    )
    output = generate_advisor_output(profile, [_achievement(major_relevance=7)],
                                     universities, limit_per_bracket=3)
    counts = {b: 0 for b in ("stretch", "realistic", "safety")}
    for fit in output.fits:
        counts[fit.bracket] += 1
    for b, n in counts.items():
        assert n <= 3, f"{b} bracket exceeds limit"
