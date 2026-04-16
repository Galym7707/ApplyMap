from __future__ import annotations

from typing import Any

from ..models.university import University
from ..models.user import StudentProfile


PROGRAM_LIBRARY: dict[str, list[dict[str, str]]] = {
    "mit": [
        {
            "name": "MIT PRIMES",
            "why_it_matters": "High-signal math and computer science research track that reads as real academic depth, not just another club.",
            "funding_note": "Treat as top priority if you can access the remote track, but verify the current international eligibility and cost rules.",
            "priority": "verify",
        },
        {
            "name": "Research Science Institute (RSI)",
            "why_it_matters": "Elite research credential with immediate value for STEM-heavy applications and a much stronger narrative than a generic summer school.",
            "funding_note": "Prioritize because the program has historically been fully funded for admitted students, but still verify the current cycle.",
            "priority": "full-funding",
        },
        {
            "name": "MITES",
            "why_it_matters": "Strong MIT-branded pre-college signal for STEM readiness and academic stretch.",
            "funding_note": "Useful only if the current cycle accepts your profile and funding route. Verify international access before planning around it.",
            "priority": "verify",
        },
        {
            "name": "Beaver Works Summer Institute",
            "why_it_matters": "Good applied CS, AI, and robotics proof if you need a stronger technical build before applications.",
            "funding_note": "Do not assume full funding. Apply only if scholarship or sponsored access is available.",
            "priority": "scholarship",
        },
    ],
    "default_cs": [
        {
            "name": "Research Science Institute (RSI)",
            "why_it_matters": "Recognizable research signal for highly selective STEM admissions.",
            "funding_note": "Prioritize first because it has historically offered a strong funding route for admitted students, but verify the current cycle.",
            "priority": "full-funding",
        },
        {
            "name": "Pioneer Academics",
            "why_it_matters": "Produces an actual research output and helps move your story from project-builder to research-capable applicant.",
            "funding_note": "Apply only if scholarship support is available. Do not treat it as an automatic full-funding option.",
            "priority": "scholarship",
        },
        {
            "name": "PROMYS",
            "why_it_matters": "Strong fit if your target major needs proof of mathematical rigor behind CS or AI ambitions.",
            "funding_note": "Useful when aid is available. Verify current scholarship access for international students.",
            "priority": "verify",
        },
        {
            "name": "YYGS IST",
            "why_it_matters": "Not as strong as true research, but still better than a generic enrichment camp if you need a branded academic program.",
            "funding_note": "Only worth it with substantial aid or sponsorship.",
            "priority": "scholarship",
        },
    ],
    "default_engineering": [
        {
            "name": "Research Science Institute (RSI)",
            "why_it_matters": "Adds hard research credibility for engineering-heavy applications.",
            "funding_note": "Prioritize because the funding path has historically been strong for admitted students, but verify the current cycle.",
            "priority": "full-funding",
        },
        {
            "name": "Beaver Works Summer Institute",
            "why_it_matters": "Strong applied engineering and robotics signal when you need a build-heavy program.",
            "funding_note": "Use only with scholarship support or sponsor backing.",
            "priority": "scholarship",
        },
        {
            "name": "PROMYS",
            "why_it_matters": "Helpful if your engineering target expects serious math underneath the build work.",
            "funding_note": "Verify current financial aid options for international students.",
            "priority": "verify",
        },
    ],
}

MAJOR_KEYWORDS = {
    "cs": ["computer science", "cs", "artificial intelligence", "ai", "machine learning", "software"],
    "engineering": ["engineering", "electrical", "mechanical", "robotics"],
    "business": ["business", "economics", "finance", "management"],
    "life_sciences": ["biology", "biotech", "medicine", "neuroscience", "chemistry"],
}


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def _includes_any(value: str, terms: list[str]) -> bool:
    return any(term in value for term in terms)


def _detect_track(university: University, major: str) -> str:
    combined = " ".join(
        [
            _normalize(major),
            _normalize(" ".join(university.major_strengths or [])),
        ]
    )

    if _includes_any(combined, MAJOR_KEYWORDS["cs"]):
        return "cs"
    if _includes_any(combined, MAJOR_KEYWORDS["engineering"]):
        return "engineering"
    if _includes_any(combined, MAJOR_KEYWORDS["business"]):
        return "business"
    if _includes_any(combined, MAJOR_KEYWORDS["life_sciences"]):
        return "life_sciences"
    return "general"


def _programs_for(university: University, major: str) -> list[dict[str, str]]:
    slug = _normalize(university.slug)
    if slug in PROGRAM_LIBRARY:
        return PROGRAM_LIBRARY[slug]

    track = _detect_track(university, major)
    if track == "cs":
        return PROGRAM_LIBRARY["default_cs"]
    if track == "engineering":
        return PROGRAM_LIBRARY["default_engineering"]

    return [
        {
            "name": "Professor-led summer research program",
            "why_it_matters": "You still need a real academic signal tied to the target major, not only extracurricular activity.",
            "funding_note": "Choose only options with a clear scholarship or sponsor route.",
            "priority": "verify",
        }
    ]


def _focus_areas(university: University, major: str, profile: StudentProfile | None) -> list[str]:
    school_years = None
    preferences = profile.application_preferences_json if profile else None
    if isinstance(preferences, dict):
        raw_school_years = preferences.get("school_years")
        if raw_school_years is not None:
            school_years = str(raw_school_years)

    focus = [
        f"Target major: {major}. Keep the advisor anchored to this major, not to the whole student profile.",
        f"Application route: {university.application_system}." if university.application_system else "",
        f"Curriculum context: {profile.curriculum}." if profile and profile.curriculum else "",
        (
            f"Academic baseline: the school expects {university.education_years_required}+ years of schooling."
            if university.education_years_required
            else ""
        ),
        f"Your saved school-years setting is {school_years}." if school_years else "",
        f"School-years note: {university.school_years_note}" if university.school_years_note else "",
        (
            f"The university already reads strongest for: {', '.join((university.major_strengths or [])[:4])}."
            if university.major_strengths
            else ""
        ),
        (
            "This school profile rewards research depth and proof of technical rigor more than generic leadership packaging."
            if getattr(university.weight_preset, "value", university.weight_preset) == "research_heavy"
            else ""
        ),
        (
            "This school profile rewards leadership and initiative, but it still needs major-specific substance."
            if getattr(university.weight_preset, "value", university.weight_preset) == "leadership_heavy"
            else ""
        ),
        (
            "This school profile is balanced, so academic rigor, fit, and a clear narrative all matter."
            if getattr(university.weight_preset, "value", university.weight_preset) == "balanced_holistic"
            else ""
        ),
        (
            "This school profile values community impact, but the story still has to stay connected to the intended major."
            if getattr(university.weight_preset, "value", university.weight_preset) == "community_service_heavy"
            else ""
        ),
    ]

    return _dedupe(focus)[:5]


def _funding_plan(university: University, user_country: str | None) -> list[str]:
    country_label = user_country or "your country"
    funding = [
        (
            f"This university stays on the shortlist because a full-funding route appears possible for an international applicant from {country_label}."
            if university.full_ride_possible
            else "Do not position this university as full-ride-safe yet. Keep it only if you can cover the gap or find a separate sponsor route."
        ),
        f"Funding route in the dataset: {university.aid_type.replace('_', ' ')}." if university.aid_type else "",
        f"Aid note: {university.aid_notes}" if university.aid_notes else "",
        f"Eligibility check: {university.eligibility_notes}" if university.eligibility_notes else "",
        (
            "Before final submission, verify the current aid policy on the university funding page."
            if university.funding_source_url
            else "Before final submission, verify the current aid policy on the official admissions and financial aid pages."
        ),
    ]
    return _dedupe(funding)


def _action_plan(university: University, major: str, programs: list[dict[str, str]]) -> list[dict[str, str]]:
    top_programs = ", ".join(program["name"] for program in programs[:3])
    return [
        {
            "title": "Lock the exact application lane",
            "detail": f"Keep this advisor strictly on {major} at {university.name}. Do not dilute it into a generic student summary.",
        },
        {
            "title": "Add one real research signal",
            "detail": (
                f"Prioritize named programs like {top_programs} instead of generic competitions or random certificates."
                if top_programs
                else "Prioritize a named research program with a real output, not another generic extracurricular."
            ),
        },
        {
            "title": "Build one flagship major-aligned artifact",
            "detail": "Ship one serious project, paper, or technical build that can carry the application narrative for this major.",
        },
        {
            "title": "Protect the funding story",
            "detail": (
                "Keep this school only if the international full-funding route still checks out on the current official page."
                if university.full_ride_possible
                else "Treat funding as a blocker, not a footnote. If full funding is not realistic, move the school out of the core list."
            ),
        },
    ]


def build_report_advisor_snapshot(
    *,
    university: University,
    profile: StudentProfile | None,
    user_country: str | None,
    report_note: str,
) -> dict[str, Any]:
    major = (profile.intended_major if profile and profile.intended_major else None) or (
        university.major_strengths[0] if university.major_strengths else None
    ) or "your target major"
    programs = _programs_for(university, major)

    return {
        "title": f"{university.name} advisor",
        "subtitle": f"Focused on {major} and the funding reality for an international applicant.",
        "target_major": major,
        "report_note": report_note,
        "focus_areas": _focus_areas(university, major, profile),
        "research_programs": programs,
        "funding_plan": _funding_plan(university, user_country),
        "action_plan": _action_plan(university, major, programs),
    }
