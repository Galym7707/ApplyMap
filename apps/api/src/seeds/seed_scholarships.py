"""Seed a starter set of scholarships for international applicants.

The data here is sourced from the public landing pages of each program at
the time of writing (2025-2026 cycle). Amounts and deadlines change
year-over-year - the `last_verified_at` field tracks when each entry was
last reviewed manually. Run this seed periodically.

This is a *foundation* dataset - extending to several hundred named
programs is tracked as a follow-up PR.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.scholarship import FundingCoverage, Scholarship, ScholarshipScope


@dataclass
class ScholarshipSeed:
    slug: str
    name: str
    sponsor: str
    scope: ScholarshipScope
    coverage: FundingCoverage
    eligible_countries: list[str]
    eligible_levels: list[str]
    eligibility_criteria: str
    application_url: str
    source_url: str
    source_title: str
    last_verified_at: date
    estimated_amount_note: str | None = None
    estimated_amount_usd: int | None = None
    intended_majors: list[str] | None = None
    minimum_test_scores: dict[str, Any] | None = None
    requires_essay: bool = True
    requires_recommendation: bool = True
    requires_interview: bool = False
    notes: str | None = None


VERIFIED_AT = date(2025, 12, 1)


SCHOLARSHIPS: list[ScholarshipSeed] = [
    ScholarshipSeed(
        slug="chevening-uk",
        name="Chevening Scholarships",
        sponsor="UK Foreign, Commonwealth & Development Office",
        scope=ScholarshipScope.international,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["KZ", "RU", "UA", "BY", "TR", "IN", "BR", "ZA"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Open to applicants from over 160 countries for one-year master's degrees "
            "in the UK. Requires two years of work experience and demonstrated leadership."
        ),
        estimated_amount_note="Full tuition + monthly stipend + travel + visa",
        application_url="https://www.chevening.org/scholarships/who-can-apply/",
        source_url="https://www.chevening.org/",
        source_title="Chevening Scholarships home",
        last_verified_at=VERIFIED_AT,
        notes="Two years of post-undergrad work experience required.",
    ),
    ScholarshipSeed(
        slug="erasmus-mundus-joint-masters",
        name="Erasmus Mundus Joint Masters",
        sponsor="European Commission",
        scope=ScholarshipScope.international,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Two-year master's programmes delivered by consortia of European universities. "
            "Bachelor's-level qualification required at time of application."
        ),
        estimated_amount_note="EUR 1,400/month stipend + tuition + travel",
        application_url="https://www.eacea.ec.europa.eu/scholarships/erasmus-mundus-catalogue_en",
        source_url="https://erasmus-plus.ec.europa.eu/opportunities/individuals/students/erasmus-mundus-joint-masters-scholarships",
        source_title="Erasmus Mundus Joint Masters - European Commission",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="fulbright-foreign-student",
        name="Fulbright Foreign Student Program",
        sponsor="U.S. Department of State",
        scope=ScholarshipScope.international,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Graduate study at U.S. universities. Country-specific eligibility and "
            "deadlines administered by each U.S. embassy."
        ),
        estimated_amount_note="Tuition + monthly stipend + health + travel",
        application_url="https://foreign.fulbrightonline.org/",
        source_url="https://foreign.fulbrightonline.org/",
        source_title="Fulbright Foreign Student Program",
        last_verified_at=VERIFIED_AT,
        requires_interview=True,
    ),
    ScholarshipSeed(
        slug="rhodes-scholarships",
        name="Rhodes Scholarships",
        sponsor="Rhodes Trust",
        scope=ScholarshipScope.international,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Postgraduate study at the University of Oxford. Constituency-based "
            "selection (e.g. Global, India, US, Kenya, etc.). Age limit 18-24."
        ),
        estimated_amount_note="Full tuition + GBP 18k+ stipend + visa + travel",
        application_url="https://www.rhodeshouse.ox.ac.uk/scholarships/",
        source_url="https://www.rhodeshouse.ox.ac.uk/",
        source_title="Rhodes House",
        last_verified_at=VERIFIED_AT,
        requires_interview=True,
    ),
    ScholarshipSeed(
        slug="schwarzman-scholars",
        name="Schwarzman Scholars",
        sponsor="Schwarzman Scholars Program (Tsinghua University)",
        scope=ScholarshipScope.international,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "One-year master's in Global Affairs at Tsinghua University in Beijing. "
            "Age 18-28, English-taught."
        ),
        estimated_amount_note="Full tuition + travel + stipend + study trips",
        application_url="https://www.schwarzmanscholars.org/admissions/",
        source_url="https://www.schwarzmanscholars.org/",
        source_title="Schwarzman Scholars",
        last_verified_at=VERIFIED_AT,
        requires_interview=True,
    ),
    ScholarshipSeed(
        slug="knight-hennessy-stanford",
        name="Knight-Hennessy Scholars",
        sponsor="Stanford University",
        scope=ScholarshipScope.institution,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Up to three years of full funding for any Stanford graduate degree "
            "(MBA, JD, MD, PhD, MA, MS, etc.)."
        ),
        estimated_amount_note="Tuition + GSB stipend + travel + leadership programming",
        application_url="https://knight-hennessy.stanford.edu/admission",
        source_url="https://knight-hennessy.stanford.edu/",
        source_title="Knight-Hennessy Scholars - Stanford",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="gates-cambridge",
        name="Gates Cambridge Scholarships",
        sponsor="Bill & Melinda Gates Foundation / University of Cambridge",
        scope=ScholarshipScope.institution,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Postgraduate study at Cambridge for outstanding applicants from outside "
            "the UK with a commitment to improving the lives of others."
        ),
        estimated_amount_note="Tuition + maintenance + family + travel allowance",
        application_url="https://www.gatescambridge.org/apply/",
        source_url="https://www.gatescambridge.org/",
        source_title="Gates Cambridge",
        last_verified_at=VERIFIED_AT,
        requires_interview=True,
    ),
    ScholarshipSeed(
        slug="yenching-academy-peking",
        name="Yenching Academy Scholarship",
        sponsor="Peking University",
        scope=ScholarshipScope.institution,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Two-year master's in China Studies. English-taught with intensive Chinese."
        ),
        estimated_amount_note="Tuition + accommodation + RMB stipend + travel",
        application_url="https://yenchingacademy.pku.edu.cn/ADMISSIONS.htm",
        source_url="https://yenchingacademy.pku.edu.cn/",
        source_title="Yenching Academy of Peking University",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="daad-germany",
        name="DAAD Scholarship Programmes",
        sponsor="German Academic Exchange Service",
        scope=ScholarshipScope.country,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["undergraduate", "graduate"],
        eligibility_criteria=(
            "Multiple programmes for study and research in Germany. Specific "
            "programmes target each country and field."
        ),
        estimated_amount_note="Monthly stipend + tuition + insurance + travel (varies)",
        application_url="https://www.daad.de/en/study-and-research-in-germany/scholarships/",
        source_url="https://www.daad.de/",
        source_title="DAAD - German Academic Exchange Service",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="kgsp-korean-government",
        name="Global Korea Scholarship (KGSP/GKS)",
        sponsor="National Institute for International Education (NIIED), South Korea",
        scope=ScholarshipScope.country,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["undergraduate", "graduate"],
        eligibility_criteria=(
            "Undergraduate (4 years + 1 year language) or graduate study at "
            "designated Korean universities."
        ),
        estimated_amount_note="Tuition + airfare + monthly KRW 900k-1.0M stipend + Korean language training",
        application_url="https://www.studyinkorea.go.kr/en/sub/gks/allnew_invite.do",
        source_url="https://www.studyinkorea.go.kr/",
        source_title="Study in Korea (NIIED)",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="mext-japan",
        name="MEXT Scholarship",
        sponsor="Ministry of Education, Culture, Sports, Science and Technology (Japan)",
        scope=ScholarshipScope.country,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["undergraduate", "graduate"],
        eligibility_criteria=(
            "Embassy-recommended and university-recommended tracks for full-time "
            "study at Japanese universities."
        ),
        estimated_amount_note="Tuition + monthly JPY ~117k-148k stipend + airfare",
        application_url="https://www.studyinjapan.go.jp/en/planning/scholarship/scholarship.html",
        source_url="https://www.studyinjapan.go.jp/",
        source_title="Study in Japan - MEXT",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="bolashak-kazakhstan",
        name="Bolashak International Scholarship",
        sponsor="Government of Kazakhstan",
        scope=ScholarshipScope.country,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["KZ"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Kazakhstani citizens for graduate study at top-ranked universities "
            "abroad. Must commit to working in Kazakhstan for at least 5 years "
            "after graduation."
        ),
        estimated_amount_note="Full tuition + accommodation + stipend + insurance + travel",
        application_url="https://bolashak.gov.kz/en/",
        source_url="https://bolashak.gov.kz/en/",
        source_title="Bolashak Center for International Programs",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="hkust-jockey-club",
        name="HKUST Jockey Club Connect for International Students",
        sponsor="The Hong Kong University of Science and Technology",
        scope=ScholarshipScope.institution,
        coverage=FundingCoverage.full_tuition,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["undergraduate"],
        eligibility_criteria=(
            "Outstanding international undergraduate applicants. No separate "
            "scholarship application - admitted students are automatically considered."
        ),
        estimated_amount_note="Up to full tuition + accommodation + living allowance",
        application_url="https://join.hkust.edu.hk/admissions/international-students",
        source_url="https://join.hkust.edu.hk/admissions/international-students/scholarships",
        source_title="HKUST Scholarships for International Students",
        last_verified_at=VERIFIED_AT,
        requires_essay=False,
        requires_recommendation=False,
    ),
    ScholarshipSeed(
        slug="kaist-international-undergrad",
        name="KAIST International Undergraduate Admission Scholarships",
        sponsor="Korea Advanced Institute of Science and Technology",
        scope=ScholarshipScope.institution,
        coverage=FundingCoverage.full_tuition,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["undergraduate"],
        eligibility_criteria=(
            "International undergraduate applicants admitted to KAIST. Awarded "
            "automatically based on admission decision."
        ),
        estimated_amount_note="Full tuition + KRW 350k/month for 8 semesters",
        application_url="https://admission.kaist.ac.kr/intl-undergraduate/",
        source_url="https://admission.kaist.ac.kr/intl-undergraduate/scholarships/",
        source_title="KAIST International Admissions - Scholarships",
        last_verified_at=VERIFIED_AT,
        requires_essay=False,
        requires_recommendation=False,
        notes="Maintain semester GPA >= 2.7 to renew.",
    ),
    ScholarshipSeed(
        slug="nyu-shanghai-international",
        name="NYU Shanghai International Student Scholarships",
        sponsor="NYU Shanghai",
        scope=ScholarshipScope.institution,
        coverage=FundingCoverage.partial_tuition,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["undergraduate"],
        eligibility_criteria=(
            "Need-aware merit aid for international undergraduates. Some recipients "
            "receive full-need packages."
        ),
        estimated_amount_note="Up to USD 60k/year + full need met",
        application_url="https://shanghai.nyu.edu/admissions/international/financial-aid",
        source_url="https://shanghai.nyu.edu/",
        source_title="NYU Shanghai Financial Aid for International Students",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="csc-china-scholarship",
        name="Chinese Government Scholarship (CSC)",
        sponsor="China Scholarship Council",
        scope=ScholarshipScope.country,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["undergraduate", "graduate"],
        eligibility_criteria=(
            "Multiple tracks (Type A bilateral, Type B university, Type C local). "
            "Chinese-medium and English-medium programmes."
        ),
        estimated_amount_note="Tuition + accommodation + monthly CNY 2,500-3,500 stipend + insurance",
        application_url="https://studyinchina.csc.edu.cn/",
        source_url="https://www.campuschina.org/",
        source_title="Campus China - Chinese Government Scholarship",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="orange-tulip-netherlands",
        name="Orange Tulip Scholarship (Netherlands)",
        sponsor="Nuffic Neso (with partner Dutch institutions)",
        scope=ScholarshipScope.country,
        coverage=FundingCoverage.partial_tuition,
        eligible_countries=["BR", "CN", "ID", "IN", "MX", "RU", "TH", "TR", "VN"],
        eligible_levels=["undergraduate", "graduate"],
        eligibility_criteria=(
            "Partial-to-full tuition coverage for non-EU nationals studying at "
            "participating Dutch universities. Country-specific lists."
        ),
        estimated_amount_note="EUR 5k - full tuition (varies by partner institution)",
        application_url="https://www.studyinnl.org/finances/orange-tulip-scholarship",
        source_url="https://www.nuffic.nl/",
        source_title="Nuffic - Orange Tulip Scholarship",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="kaad-germany",
        name="KAAD Scholarships",
        sponsor="Catholic Academic Exchange Service (KAAD)",
        scope=ScholarshipScope.country,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Graduate study or research in Germany for applicants from developing "
            "countries with a Christian background or strong dialogue partners."
        ),
        estimated_amount_note="EUR 1,200-1,500/month + travel + insurance",
        application_url="https://kaad.de/en/scholarships/",
        source_url="https://kaad.de/",
        source_title="KAAD",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="commonwealth-scholarship",
        name="Commonwealth Scholarships (UK)",
        sponsor="Commonwealth Scholarship Commission UK",
        scope=ScholarshipScope.international,
        coverage=FundingCoverage.full_ride,
        eligible_countries=[
            "AU", "BD", "BB", "BS", "BZ", "BW", "CA", "CY", "DM", "FJ", "GH",
            "GD", "GY", "IN", "JM", "KE", "KI", "LS", "MW", "MY", "MV", "MT",
            "MU", "MZ", "NA", "NR", "NZ", "NG", "PK", "PG", "RW", "WS", "SC",
            "SL", "SG", "SB", "ZA", "LK", "SZ", "TZ", "TT", "TO", "UG", "VU",
            "ZM",
        ],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Master's and PhD study in the UK for citizens of low/middle-income "
            "Commonwealth countries."
        ),
        estimated_amount_note="Tuition + stipend + travel + family/study allowances",
        application_url="https://cscuk.fcdo.gov.uk/scholarships/",
        source_url="https://cscuk.fcdo.gov.uk/",
        source_title="Commonwealth Scholarship Commission UK",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="endeavour-australia",
        name="Australia Awards Scholarships",
        sponsor="Government of Australia (DFAT)",
        scope=ScholarshipScope.country,
        coverage=FundingCoverage.full_ride,
        eligible_countries=[
            "BD", "FJ", "ID", "KE", "MM", "NP", "PG", "PH", "SB", "VN", "TZ",
            "VU", "WS", "TL", "ZW",
        ],
        eligible_levels=["undergraduate", "graduate"],
        eligibility_criteria=(
            "Long-term development scholarships providing opportunities for people "
            "from developing countries to study in Australia."
        ),
        estimated_amount_note="Full tuition + airfare + establishment allowance + monthly stipend",
        application_url="https://www.dfat.gov.au/people-to-people/australia-awards/Scholarships/Pages/australia-awards-scholarships",
        source_url="https://www.dfat.gov.au/people-to-people/australia-awards",
        source_title="DFAT - Australia Awards",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="sciences-po-emile-boutmy",
        name="Emile Boutmy Scholarship",
        sponsor="Sciences Po (Paris)",
        scope=ScholarshipScope.institution,
        coverage=FundingCoverage.partial_tuition,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["undergraduate", "graduate"],
        eligibility_criteria=(
            "Outstanding non-EU international students applying for the bachelor's "
            "or master's programme at Sciences Po. Need-based."
        ),
        estimated_amount_note="EUR 6k - 14.7k/year (bachelor's), EUR 5k - 19k/year (master's)",
        application_url="https://www.sciencespo.fr/students/en/finance-stay/scholarships-financial-aid/emile-boutmy.html",
        source_url="https://www.sciencespo.fr/",
        source_title="Sciences Po - Emile Boutmy Scholarship",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="agakhan-foundation",
        name="Aga Khan Foundation International Scholarship Programme",
        sponsor="Aga Khan Foundation",
        scope=ScholarshipScope.international,
        coverage=FundingCoverage.partial_tuition,
        eligible_countries=[
            "BD", "EG", "IN", "KE", "KG", "MZ", "PK", "SY", "TJ", "TZ", "UG",
            "AF", "MG", "FR", "PT", "GB", "US", "CA",
        ],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Postgraduate studies for outstanding students from developing countries "
            "with no other source of funding. 50% loan / 50% grant structure."
        ),
        estimated_amount_note="Tuition + living + travel (50/50 grant/loan)",
        application_url="https://the.akdn/en/how-we-work/our-agencies/aga-khan-foundation/international-scholarship-programme",
        source_url="https://the.akdn/",
        source_title="Aga Khan Foundation Scholarships",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="vanier-canada",
        name="Vanier Canada Graduate Scholarships",
        sponsor="Government of Canada",
        scope=ScholarshipScope.country,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Doctoral students at Canadian universities. Nominated by the host "
            "institution."
        ),
        estimated_amount_note="CAD 50k/year for up to three years",
        application_url="https://vanier.gc.ca/en/home-accueil.html",
        source_url="https://vanier.gc.ca/",
        source_title="Vanier Canada Graduate Scholarships",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="trudeau-foundation",
        name="Trudeau Foundation Doctoral Scholarships",
        sponsor="Pierre Elliott Trudeau Foundation",
        scope=ScholarshipScope.international,
        coverage=FundingCoverage.full_ride,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Outstanding PhD students in the social sciences and humanities, with "
            "research linked to one of the Foundation's themes."
        ),
        estimated_amount_note="CAD 60k/year + travel allowance for up to four years",
        application_url="https://www.trudeaufoundation.ca/scholarships",
        source_url="https://www.trudeaufoundation.ca/",
        source_title="Trudeau Foundation Scholarships",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="mastercard-foundation-scholars",
        name="Mastercard Foundation Scholars Program",
        sponsor="Mastercard Foundation (with partner universities)",
        scope=ScholarshipScope.international,
        coverage=FundingCoverage.full_ride,
        eligible_countries=[
            "GH", "KE", "NG", "RW", "TZ", "UG", "ZA", "ZW", "EG", "MZ", "SN",
        ],
        eligible_levels=["undergraduate", "graduate"],
        eligibility_criteria=(
            "Talented yet economically disadvantaged students from sub-Saharan "
            "Africa for degrees at partner universities worldwide."
        ),
        estimated_amount_note="Tuition + accommodation + travel + stipend + leadership programming",
        application_url="https://mastercardfdn.org/all/scholars/",
        source_url="https://mastercardfdn.org/",
        source_title="Mastercard Foundation Scholars Program",
        last_verified_at=VERIFIED_AT,
    ),
    ScholarshipSeed(
        slug="open-society-civil-society",
        name="Civil Society Scholar Awards",
        sponsor="Open Society University Network / Open Society Foundations",
        scope=ScholarshipScope.international,
        coverage=FundingCoverage.partial_tuition,
        eligible_countries=["WORLDWIDE"],
        eligible_levels=["graduate"],
        eligibility_criteria=(
            "Doctoral students and faculty for short-term research in defined "
            "OSF priority countries."
        ),
        estimated_amount_note="Up to USD 15,000 per award",
        application_url="https://www.opensocietyfoundations.org/grants/civil-society-scholar-awards",
        source_url="https://www.opensocietyfoundations.org/",
        source_title="OSF Civil Society Scholar Awards",
        last_verified_at=VERIFIED_AT,
    ),
]


def _to_dict(seed: ScholarshipSeed) -> dict:
    return {
        "slug": seed.slug,
        "name": seed.name,
        "sponsor": seed.sponsor,
        "scope": seed.scope,
        "coverage": seed.coverage,
        "eligible_countries": seed.eligible_countries,
        "eligible_levels": seed.eligible_levels,
        "intended_majors": seed.intended_majors,
        "minimum_test_scores": seed.minimum_test_scores,
        "eligibility_criteria": seed.eligibility_criteria,
        "estimated_amount_usd": seed.estimated_amount_usd,
        "estimated_amount_note": seed.estimated_amount_note,
        "application_url": seed.application_url,
        "source_url": seed.source_url,
        "source_title": seed.source_title,
        "last_verified_at": seed.last_verified_at,
        "requires_essay": seed.requires_essay,
        "requires_recommendation": seed.requires_recommendation,
        "requires_interview": seed.requires_interview,
        "notes": seed.notes,
        "is_active": True,
    }


def seed_scholarships(db: Session | None = None) -> int:
    """Upsert the starter scholarships into the database.

    Returns the number of records created or updated.
    """
    own_session = db is None
    session = db or SessionLocal()
    try:
        touched = 0
        for seed in SCHOLARSHIPS:
            payload = _to_dict(seed)
            existing = (
                session.query(Scholarship).filter(Scholarship.slug == seed.slug).first()
            )
            if existing:
                for field_name, value in payload.items():
                    setattr(existing, field_name, value)
            else:
                session.add(Scholarship(**payload))
            touched += 1
        session.commit()
        return touched
    finally:
        if own_session:
            session.close()


if __name__ == "__main__":
    count = seed_scholarships()
    print(f"Seeded/updated {count} scholarships at {datetime.utcnow().isoformat()} UTC")
