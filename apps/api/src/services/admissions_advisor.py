"""Deterministic stretch / realistic / safety advisor.

This module is deliberately *not* an LLM. Given a `StudentProfile`, the user's
`Achievement` records, and a list of `University` rows, it returns three
brackets of recommendations:

* **Stretch** — selectivity sits 2+ bands above the student's current band.
  Honest about the long odds.
* **Realistic** — selectivity within ±1 band of the student's profile.
* **Safety** — selectivity 2+ bands below the student's current band. Acts as
  the academic backstop.

Every recommendation carries a structured `rationale` so the frontend can
explain *why* a school landed where it did, and a `profile_actions` payload at
the top level lists concrete improvements the student can make.

The output also flags `transparency_note` strings so reports separate
"official source", "public example", and "system suggestion" — matching the
PR #1 prosecution pattern.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Literal, Optional

from ..models.achievement import (
    Achievement,
    ActivityCategory,
    ActivityRole,
    ImpactScope,
    LeadershipLevel,
)
from ..models.university import University


Bracket = Literal["stretch", "realistic", "safety"]


# ---------------------------------------------------------------------------
# Profile strength scoring
# ---------------------------------------------------------------------------

# Test-score → 0-30 band.
SAT_BANDS: list[tuple[int, int]] = [
    (1550, 30),
    (1500, 28),
    (1450, 25),
    (1400, 22),
    (1350, 19),
    (1300, 16),
    (1250, 13),
    (1200, 10),
    (1150, 8),
    (1100, 6),
    (1000, 4),
    (0, 2),
]
ACT_BANDS: list[tuple[int, int]] = [
    (35, 30),
    (34, 28),
    (33, 25),
    (32, 22),
    (31, 19),
    (30, 16),
    (29, 13),
    (28, 10),
    (26, 8),
    (24, 6),
    (22, 4),
    (0, 2),
]
IELTS_BANDS: list[tuple[float, int]] = [
    (8.5, 30),
    (8.0, 27),
    (7.5, 24),
    (7.0, 20),
    (6.5, 16),
    (6.0, 12),
    (5.5, 8),
    (0.0, 4),
]
TOEFL_BANDS: list[tuple[int, int]] = [
    (115, 30),
    (110, 28),
    (105, 25),
    (100, 22),
    (95, 19),
    (90, 16),
    (85, 13),
    (80, 10),
    (75, 8),
    (70, 6),
    (0, 4),
]
DUOLINGO_BANDS: list[tuple[int, int]] = [
    (140, 30),
    (130, 26),
    (120, 22),
    (110, 18),
    (100, 14),
    (90, 10),
    (0, 6),
]


def _bucket(value: float, bands: list[tuple[float, int]]) -> int:
    for threshold, score in bands:
        if value >= threshold:
            return score
    return bands[-1][1]


def _parse_ielts(raw: str | None) -> Optional[float]:
    if not raw:
        return None
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _test_score_component(profile: Any) -> tuple[int, list[str]]:
    """0-30 component reflecting the strongest demonstrated test score."""
    if profile is None:
        return 0, ["No test scores captured yet — add SAT/ACT/IELTS/TOEFL to profile."]

    notes: list[str] = []
    candidates: list[int] = []

    sat = getattr(profile, "sat_score", None)
    if sat:
        candidates.append(_bucket(float(sat), SAT_BANDS))
        notes.append(f"SAT total {sat}")

    act = getattr(profile, "act_score", None)
    if act:
        candidates.append(_bucket(float(act), ACT_BANDS))
        notes.append(f"ACT composite {act}")

    ielts = _parse_ielts(getattr(profile, "ielts_score", None))
    if ielts is not None:
        candidates.append(_bucket(ielts, IELTS_BANDS))
        notes.append(f"IELTS overall {ielts}")

    toefl = getattr(profile, "toefl_score", None)
    if toefl:
        candidates.append(_bucket(float(toefl), TOEFL_BANDS))
        notes.append(f"TOEFL total {toefl}")

    duolingo = getattr(profile, "duolingo_score", None)
    if duolingo:
        candidates.append(_bucket(float(duolingo), DUOLINGO_BANDS))
        notes.append(f"Duolingo {duolingo}")

    if not candidates:
        return 0, ["No standardized scores yet — add SAT/ACT/IELTS/TOEFL/Duolingo to profile."]

    return max(candidates), notes


# Curriculum strength → 0-15.
CURRICULUM_BANDS: dict[str, int] = {
    "ib": 14,
    "international baccalaureate": 14,
    "a-level": 13,
    "a level": 13,
    "alevel": 13,
    "ap": 12,
    "advanced placement": 12,
    "nis": 11,
    "nazarbayev intellectual school": 11,
    "kazakh-turkish lyceum": 9,
    "high school": 7,
    "general high school": 7,
    "technical school": 6,
}


def _curriculum_component(profile: Any) -> tuple[int, str | None]:
    if profile is None:
        return 6, None
    raw = (getattr(profile, "curriculum", None) or "").strip().lower()
    if not raw:
        return 6, None
    for key, band in CURRICULUM_BANDS.items():
        if key in raw:
            return band, raw
    return 8, raw


# Achievement strength: 0-40 from the top achievements.
LEADERSHIP_BOOST: dict[LeadershipLevel, float] = {
    LeadershipLevel.none: 0.0,
    LeadershipLevel.member: 0.5,
    LeadershipLevel.lead: 1.5,
    LeadershipLevel.captain: 2.0,
    LeadershipLevel.founder: 2.5,
}

IMPACT_BOOST: dict[ImpactScope, float] = {
    ImpactScope.personal: 0.0,
    ImpactScope.family: 0.2,
    ImpactScope.school: 0.5,
    ImpactScope.local: 1.0,
    ImpactScope.regional: 1.5,
    ImpactScope.national: 2.0,
    ImpactScope.international: 2.5,
}

ROLE_BOOST: dict[ActivityRole, float] = {
    ActivityRole.anchor: 1.5,
    ActivityRole.supporting: 0.7,
    ActivityRole.contextual: 0.0,
}


def _achievement_intensity(achievement: Achievement) -> float:
    """A 0-10ish number combining the existing scoring plus categorical boosts."""
    raw_scores = [
        achievement.major_relevance_score,
        achievement.continuity_score,
        achievement.selectivity_score,
        achievement.distinctiveness_score,
    ]
    numeric = [s for s in raw_scores if isinstance(s, (int, float))]
    base = sum(numeric) / len(numeric) if numeric else 4.0

    if achievement.leadership_level:
        base += LEADERSHIP_BOOST.get(achievement.leadership_level, 0.0)
    if achievement.impact_scope:
        base += IMPACT_BOOST.get(achievement.impact_scope, 0.0)
    if achievement.activity_role:
        base += ROLE_BOOST.get(achievement.activity_role, 0.0)

    return max(0.0, min(base, 10.0))


def _achievement_component(achievements: list[Achievement]) -> tuple[int, list[str]]:
    if not achievements:
        return 0, [
            "Profile has no recorded achievements yet — start by adding 5-8 activities to "
            "the Vault so the advisor can see real signal."
        ]

    intensities = sorted(
        (_achievement_intensity(a) for a in achievements), reverse=True
    )
    top_n = intensities[:5]
    average_top = sum(top_n) / len(top_n)
    component = int(round(average_top * 4))  # 0-40 scale (0..10 → 0..40)

    notes: list[str] = []
    notes.append(
        f"Top {len(top_n)} achievement intensity averages {average_top:.1f}/10."
    )
    if len(achievements) < 6:
        notes.append(
            "Fewer than 6 logged achievements; Common App allows 10 activities and 5 honors — "
            "add more to give admissions readers a complete picture."
        )
    return min(component, 40), notes


def _major_fit_component(profile: Any, achievements: list[Achievement]) -> tuple[int, str | None]:
    if profile is None:
        return 4, None
    intended = (getattr(profile, "intended_major", None) or "").strip().lower()
    if not intended:
        return 4, "No intended major declared yet."

    relevance = [
        a.major_relevance_score
        for a in achievements
        if isinstance(a.major_relevance_score, (int, float))
    ]
    if not relevance:
        return 6, f"Intended major declared ({intended}) but no major-aligned achievements yet."
    avg = sum(relevance) / len(relevance)
    band = int(round(avg * 1.5))
    return min(15, band + 3), f"Average major relevance {avg:.1f}/10."


@dataclass
class ProfileStrength:
    score: int                       # 0-100
    band: int                        # 1-10 mapping for university selectivity bracket
    test_component: int
    achievement_component: int
    curriculum_component: int
    major_fit_component: int
    notes: list[str]

    def summary(self) -> str:
        return (
            f"Profile strength {self.score}/100 (band {self.band}/10): "
            f"tests {self.test_component}/30, "
            f"achievements {self.achievement_component}/40, "
            f"curriculum {self.curriculum_component}/15, "
            f"major fit {self.major_fit_component}/15."
        )


def compute_profile_strength(
    profile: Any,
    achievements: Iterable[Achievement] | None,
) -> ProfileStrength:
    achievement_list = list(achievements or [])
    test_score, test_notes = _test_score_component(profile)
    ach_score, ach_notes = _achievement_component(achievement_list)
    curriculum_score, curriculum_note = _curriculum_component(profile)
    major_fit_score, major_note = _major_fit_component(profile, achievement_list)

    total = test_score + ach_score + curriculum_score + major_fit_score
    band = max(1, min(10, int(round(total / 10))))
    notes = list(test_notes) + list(ach_notes)
    if curriculum_note:
        notes.append(f"Curriculum: {curriculum_note}.")
    if major_note:
        notes.append(major_note)
    return ProfileStrength(
        score=total,
        band=band,
        test_component=test_score,
        achievement_component=ach_score,
        curriculum_component=curriculum_score,
        major_fit_component=major_fit_score,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# University ranking
# ---------------------------------------------------------------------------

@dataclass
class UniversityFit:
    university_id: str
    slug: str
    name: str
    country: str
    selectivity_score: int | None
    aid_strength: int | None
    bracket: Bracket
    fit_score: int                   # 0-100, used for sort within a bracket
    rationale: list[str]
    transparency_note: str
    full_ride_possible: bool
    application_system: str | None
    teaching_languages: list[str]
    major_strengths: list[str]


def _normalize_languages(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, list):
        return [str(v).strip().lower() for v in values if v]
    if isinstance(values, str):
        return [values.strip().lower()]
    return []


def _normalize_majors(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, list):
        return [str(v).strip().lower() for v in values if v]
    if isinstance(values, str):
        return [values.strip().lower()]
    return []


def _major_match_boost(intended_major: str | None, university_majors: list[str]) -> tuple[int, str | None]:
    if not intended_major or not university_majors:
        return 0, None
    needle = intended_major.strip().lower()
    if not needle:
        return 0, None
    for tag in university_majors:
        if needle in tag or tag in needle:
            return 10, f"Major fit: {intended_major} aligns with university strength '{tag}'."
        # also match common synonyms
        if any(token and token in tag for token in needle.split()):
            return 6, f"Major fit: '{intended_major}' partially overlaps with '{tag}'."
    return -2, f"Intended major '{intended_major}' is not listed among this school's stated strengths."


def _language_match(profile: Any, university_languages: list[str]) -> tuple[bool, str]:
    if not university_languages:
        return True, "Teaching language not specified — assume English-friendly."

    # Always include "english" as the international fallback
    student_languages = {"english"}
    if profile is not None:
        country = (getattr(profile, "country", None) or "").lower()
        if "kazakhstan" in country or "kz" in country:
            student_languages.update(["russian", "kazakh"])
    target = {l.lower() for l in university_languages}
    if target & student_languages:
        return True, ""
    return False, (
        f"Teaching languages ({', '.join(university_languages)}) don't overlap with the "
        "student's working languages — recommend boosting language proficiency before applying."
    )


def _aid_alignment(profile: Any, university: University) -> tuple[int, str | None]:
    aid_needed = bool(getattr(profile, "aid_needed", None))
    aid_strength = university.aid_strength or 0
    if not aid_needed:
        return 0, None
    if aid_strength >= 8 or university.full_ride_possible:
        return 8, "Aid alignment: school is generous with international financial aid."
    if aid_strength >= 6:
        return 4, "Aid alignment: school offers meaningful merit/need aid for internationals."
    if aid_strength <= 3:
        return -10, (
            "Aid mismatch: this school offers little institutional aid to internationals — "
            "be cautious unless an external scholarship covers the cost."
        )
    return 0, None


def _bracket_for(uni_band: int, profile_band: int) -> Bracket:
    delta = uni_band - profile_band
    if delta >= 2:
        return "stretch"
    if delta <= -2:
        return "safety"
    return "realistic"


def rank_universities(
    profile: Any,
    achievements: list[Achievement],
    universities: list[University],
    *,
    limit_per_bracket: int = 6,
) -> tuple[ProfileStrength, list[UniversityFit]]:
    strength = compute_profile_strength(profile, achievements)
    intended = getattr(profile, "intended_major", None) if profile is not None else None

    fits: list[UniversityFit] = []
    for university in universities:
        if not getattr(university, "is_active", True):
            continue
        if university.selectivity_score is None:
            continue

        languages = _normalize_languages(university.teaching_languages)
        majors = _normalize_majors(university.major_strengths)

        rationale: list[str] = []
        score = 50

        # Selectivity bracket
        bracket = _bracket_for(university.selectivity_score, strength.band)
        if bracket == "stretch":
            score -= (university.selectivity_score - strength.band) * 6
            rationale.append(
                f"Selectivity band {university.selectivity_score}/10 sits "
                f"{university.selectivity_score - strength.band} bands above the student's "
                f"current strength — honest stretch."
            )
        elif bracket == "realistic":
            score += 20
            rationale.append(
                f"Selectivity band {university.selectivity_score}/10 closely matches "
                f"the student's strength band {strength.band}/10."
            )
        else:
            score += 10
            rationale.append(
                f"Selectivity band {university.selectivity_score}/10 is below the student's "
                f"strength band {strength.band}/10 — suitable academic safety."
            )

        # Major fit
        boost, msg = _major_match_boost(intended, majors)
        score += boost
        if msg:
            rationale.append(msg)

        # Aid alignment (only if aid_needed)
        aid_boost, aid_msg = _aid_alignment(profile, university)
        score += aid_boost
        if aid_msg:
            rationale.append(aid_msg)

        # Language compatibility (hard filter applied as soft penalty so we
        # still surface the result with a warning)
        ok, lang_note = _language_match(profile, languages)
        if not ok:
            score -= 25
            rationale.append(lang_note)

        # Aid generosity is a tiebreaker for stretch schools
        if bracket == "stretch" and (university.aid_strength or 0) >= 8:
            score += 5
            rationale.append("Strong international aid keeps this stretch school realistic to afford if admitted.")

        score = max(1, min(100, score))

        fits.append(
            UniversityFit(
                university_id=str(university.id) if university.id else "",
                slug=university.slug,
                name=university.name,
                country=university.country,
                selectivity_score=university.selectivity_score,
                aid_strength=university.aid_strength,
                bracket=bracket,
                fit_score=score,
                rationale=rationale,
                transparency_note=(
                    "system_suggestion: bracket assignment is computed from public selectivity bands "
                    "and the student's profile — verify with each official admissions page before applying."
                ),
                full_ride_possible=bool(university.full_ride_possible),
                application_system=university.application_system,
                teaching_languages=list(university.teaching_languages or []),
                major_strengths=list(university.major_strengths or []),
            )
        )

    fits.sort(key=lambda f: (-f.fit_score, f.name))
    return strength, _trim_per_bracket(fits, limit_per_bracket)


def _trim_per_bracket(fits: list[UniversityFit], limit: int) -> list[UniversityFit]:
    bucketed: dict[Bracket, list[UniversityFit]] = {"stretch": [], "realistic": [], "safety": []}
    for fit in fits:
        if len(bucketed[fit.bracket]) < limit:
            bucketed[fit.bracket].append(fit)
    return bucketed["stretch"] + bucketed["realistic"] + bucketed["safety"]


# ---------------------------------------------------------------------------
# Profile improvement actions
# ---------------------------------------------------------------------------

@dataclass
class ProfileAction:
    title: str
    description: str
    priority: Literal["high", "medium", "low"]
    category: str
    transparency_note: str = (
        "system_suggestion: rule-based hint derived from your current profile — not an official "
        "admissions requirement."
    )


def _missing_test_actions(profile: Any) -> list[ProfileAction]:
    actions: list[ProfileAction] = []
    if profile is None:
        return [ProfileAction(
            title="Create your profile",
            description="Add intended major, graduation year, and at least one test score "
                        "so the advisor can give meaningful recommendations.",
            priority="high",
            category="profile_basics",
        )]

    sat = getattr(profile, "sat_score", None)
    act = getattr(profile, "act_score", None)
    if not sat and not act:
        actions.append(ProfileAction(
            title="Take the SAT or ACT",
            description="US selective universities still consider standardized scores. Aim for "
                        "SAT 1450+ (or ACT 33+) to clear the threshold for top-15 schools.",
            priority="high",
            category="standardized_test",
        ))
    elif sat and sat < 1400:
        actions.append(ProfileAction(
            title="Retake the SAT to push past 1450",
            description=f"Current SAT {sat}. Reaching 1450+ moves you out of the academic-risk band "
                        "for selective US programs.",
            priority="medium",
            category="standardized_test",
        ))
    elif act and act < 32:
        actions.append(ProfileAction(
            title="Retake the ACT to push past 33",
            description=f"Current ACT {act}. ACT 33+ aligns with the median for top-25 US universities.",
            priority="medium",
            category="standardized_test",
        ))

    ielts = _parse_ielts(getattr(profile, "ielts_score", None))
    toefl = getattr(profile, "toefl_score", None)
    duolingo = getattr(profile, "duolingo_score", None)
    if not ielts and not toefl and not duolingo:
        actions.append(ProfileAction(
            title="Add an English-proficiency score",
            description="Most international students need IELTS 7.0+ / TOEFL 100+ / Duolingo 120+ "
                        "for selective programs. Sit for the test that fits your budget and timeline.",
            priority="high",
            category="english_test",
        ))
    elif ielts and ielts < 7.0:
        actions.append(ProfileAction(
            title="Retake IELTS to clear 7.0 overall",
            description=f"Current IELTS {ielts}. Many selective programs require 7.0+ with no band below 6.5.",
            priority="medium",
            category="english_test",
        ))
    elif toefl and toefl < 100:
        actions.append(ProfileAction(
            title="Retake TOEFL to clear 100",
            description=f"Current TOEFL {toefl}. TOEFL 100+ is the typical floor for top-50 US universities.",
            priority="medium",
            category="english_test",
        ))

    return actions


def _achievement_balance_actions(achievements: list[Achievement]) -> list[ProfileAction]:
    actions: list[ProfileAction] = []
    if not achievements:
        actions.append(ProfileAction(
            title="Add your first 5 achievements",
            description="Log activities, leadership roles, awards, paid work, and family responsibilities. "
                        "Achievements are how the advisor inferences your strengths.",
            priority="high",
            category="achievements",
        ))
        return actions

    categories = {a.activity_category for a in achievements if a.activity_category}
    roles = {a.activity_role for a in achievements if a.activity_role}

    if ActivityRole.anchor not in roles:
        actions.append(ProfileAction(
            title="Designate one anchor activity",
            description="An anchor is the single activity that defines your strongest spike. "
                        "Mark the strongest one in the Vault so reports highlight it.",
            priority="medium",
            category="narrative",
        ))

    if {ActivityCategory.research, ActivityCategory.technical, ActivityCategory.business}.isdisjoint(categories):
        actions.append(ProfileAction(
            title="Add at least one research, technical, or entrepreneurship project",
            description="Selective programs increasingly favor evidence of independent work — a research "
                        "paper, a coding project on GitHub, or a small business / NGO you launched.",
            priority="medium",
            category="depth",
        ))

    if {ActivityCategory.service, ActivityCategory.volunteering, ActivityCategory.community_initiative}.isdisjoint(categories):
        actions.append(ProfileAction(
            title="Add a service or community initiative",
            description="Top US schools weigh service heavily. A multi-month volunteering or community "
                        "initiative shows commitment beyond academics.",
            priority="low",
            category="breadth",
        ))

    return actions


def _course_recommendations(profile: Any) -> list[ProfileAction]:
    if profile is None:
        return []
    intended = (getattr(profile, "intended_major", None) or "").lower()
    actions: list[ProfileAction] = []

    if any(k in intended for k in ("computer science", "software", "ai", "data")):
        actions.append(ProfileAction(
            title="Take a public CS course (Coursera / edX / CS50)",
            description="Harvard's CS50x (free on edX) and Stanford's Code in Place are widely "
                        "recognized signals for CS applicants. Finish at least one with a project portfolio.",
            priority="medium",
            category="coursework",
        ))
    elif any(k in intended for k in ("business", "economics", "finance", "management")):
        actions.append(ProfileAction(
            title="Take Wharton's Business Foundations or a Coursera economics specialization",
            description="Free Coursera tracks from Wharton, Yale, and the University of Michigan are "
                        "credible coursework signals; pair them with a small revenue project or pitch deck.",
            priority="medium",
            category="coursework",
        ))
    elif any(k in intended for k in ("engineer", "physics", "mathematics", "robotics")):
        actions.append(ProfileAction(
            title="Take MIT OCW or edX engineering / math sequence",
            description="MIT OCW's 6.0001 (CS) and 18.01 (Calculus), or edX MicroMasters, give "
                        "international applicants comparable rigor evidence to AP/IB.",
            priority="medium",
            category="coursework",
        ))
    elif any(k in intended for k in ("medicine", "biology", "public health", "neuroscience")):
        actions.append(ProfileAction(
            title="Take Yale's Science of Wellbeing or Johns Hopkins public-health track",
            description="Pair a Coursera health-sciences specialization with shadowing or "
                        "lab volunteering at a local clinic / NGO.",
            priority="medium",
            category="coursework",
        ))
    elif any(k in intended for k in ("political", "international", "policy", "law")):
        actions.append(ProfileAction(
            title="Take a Yale or Sciences Po MOOC on global affairs",
            description="Yale's Moral Foundations of Politics and Sciences Po's Espace mondial are "
                        "credible signals for IR/Politics applicants.",
            priority="medium",
            category="coursework",
        ))
    return actions


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

@dataclass
class AdvisorOutput:
    profile_strength: ProfileStrength
    fits: list[UniversityFit]
    profile_actions: list[ProfileAction]
    summary: str
    transparency_note: str = (
        "ApplyMap separates official requirements (from each school's admissions page) from "
        "system suggestions like this advisor. The brackets here are a deterministic recommender — "
        "always verify exact requirements with each university before applying."
    )


def generate_advisor_output(
    profile: Any,
    achievements: list[Achievement],
    universities: list[University],
    *,
    limit_per_bracket: int = 6,
) -> AdvisorOutput:
    strength, fits = rank_universities(
        profile, achievements, universities, limit_per_bracket=limit_per_bracket
    )
    actions = (
        _missing_test_actions(profile)
        + _achievement_balance_actions(list(achievements or []))
        + _course_recommendations(profile)
    )

    bracket_counts = {b: 0 for b in ("stretch", "realistic", "safety")}
    for f in fits:
        bracket_counts[f.bracket] += 1
    summary = (
        f"{strength.summary()} "
        f"{bracket_counts['stretch']} stretch / "
        f"{bracket_counts['realistic']} realistic / "
        f"{bracket_counts['safety']} safety schools surfaced."
    )

    return AdvisorOutput(
        profile_strength=strength,
        fits=fits,
        profile_actions=actions,
        summary=summary,
    )
