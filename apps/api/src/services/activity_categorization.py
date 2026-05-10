"""Deterministic categorization of achievements.

Derives an `ActivityCategory` and an `ActivityRole` (anchor / supporting /
contextual) for each achievement so the optimization report can show a
balanced narrative instead of stacking many entries from one bucket.

The logic is intentionally rule-based and explicit \u2014 no LLM \u2014 so it stays
reproducible and inspectable. The user-provided values on the Achievement
model (if any) always win; the helpers here only fill in gaps.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

from ..models.achievement import (
    Achievement,
    ActivityCategory,
    ActivityRole,
    AchievementType,
    ImpactScope,
    LeadershipLevel,
)


# Keyword tables. Order matters: more specific keywords are checked first.
# Each tuple is (category, lower-cased keyword fragment).
_CATEGORY_KEYWORDS: list[tuple[ActivityCategory, tuple[str, ...]]] = [
    (
        ActivityCategory.research,
        (
            "research", "lab", "laboratory", "publication", "journal",
            "co-author", "coauthor", "paper", "manuscript", "thesis",
            "научн", "иссл",  # ru
            "ғылыми", "зерт",  # kk
        ),
    ),
    (
        ActivityCategory.business,
        (
            "founder", "co-founder", "cofounder", "ceo", "startup", "start-up",
            "entrepreneur", "business", "revenue", "company", "enterprise",
            "предприн", "стартап", "бизнес",
            "кәсіпкер",
        ),
    ),
    (
        ActivityCategory.technical,
        (
            "software", "developer", "engineer", "engineering", "programming",
            "coding", "robotics", "hackathon", "ai ", "machine learning",
            "data science", "github", "open source", "open-source",
            "разработч", "программ", "робот",
            "бағдарла", "техник",
        ),
    ),
    (
        ActivityCategory.paid_work,
        (
            "intern", "internship", "part-time", "part time", "barista",
            "cashier", "tutor (paid)", "freelance", "freelancer",
            "стажир", "подработ", "официант",
            "тағылым",
        ),
    ),
    (
        ActivityCategory.family_responsibility,
        (
            "family responsibilit", "caretaker", "caregiver",
            "took care of", "looked after", "younger sibling",
            "семейн", "забота о",
            "отбасы", "бауыр",
        ),
    ),
    (
        ActivityCategory.volunteering,
        (
            "volunteer", "pro bono",
            "волонт", "доброволь",
            "ерікті",
        ),
    ),
    (
        ActivityCategory.community_initiative,
        (
            "community", "neighborhood", "village", "rural", "outreach",
            "founded a club", "initiative", "campaign", "advocacy",
            "сообщест", "инициатив", "акция",
            "қауымдас",
        ),
    ),
    (
        ActivityCategory.service,
        (
            "service", "charity", "ngo", "nonprofit", "non-profit",
            "благотвор", "помощь",
            "қайыр",
        ),
    ),
    (
        ActivityCategory.leadership,
        (
            "president", "captain", "team lead", "head of", "chairman",
            "chairperson", "director", "лидер", "капитан", "председат",
            "жетекш", "төраға",
        ),
    ),
    (
        ActivityCategory.athletics,
        (
            "athlete", "athletics", "sport", "team", "football", "soccer",
            "basketball", "volleyball", "swimming", "track", "marathon",
            "спорт", "команд",
            "спортшы",
        ),
    ),
    (
        ActivityCategory.arts,
        (
            "art ", "music", "orchestra", "band", "choir", "theater",
            "theatre", "drama", "painting", "design",
            "искусств", "музык", "театр",
            "өнер",
        ),
    ),
    (
        ActivityCategory.religious,
        (
            "religious", "church", "mosque", "temple",
            "религ", "церковь", "мечет",
            "мешіт",
        ),
    ),
    (
        ActivityCategory.academic,
        (
            "olympiad", "competition", "subject olympiad", "math olympiad",
            "science fair", "academic", "school project", "honors course",
            "олимпиад", "соревнован", "учебн",
            "пәндік олимпиада", "оқу",
        ),
    ),
]

# Categories generally treated as breadth markers (contextual) when they
# aren't the strongest theme. The optimizer still respects user overrides.
_BREADTH_CATEGORIES = frozenset({
    ActivityCategory.arts,
    ActivityCategory.athletics,
    ActivityCategory.religious,
    ActivityCategory.family_responsibility,
})


@dataclass
class CategorizedAchievement:
    achievement: Achievement
    category: ActivityCategory
    role: ActivityRole


def infer_category(achievement: Achievement) -> ActivityCategory:
    """Pick the best ActivityCategory using user input first, then keywords.

    Falls back to ActivityCategory.other if nothing matches.
    """
    if achievement.activity_category:
        return achievement.activity_category

    text = " ".join(
        part
        for part in (
            achievement.title,
            achievement.organization_name,
            achievement.role_title,
            achievement.description_raw,
            achievement.category,
        )
        if part
    ).lower()

    if not text.strip():
        return ActivityCategory.other

    for category, keywords in _CATEGORY_KEYWORDS:
        for keyword in keywords:
            if keyword in text:
                return category

    if achievement.type == AchievementType.honor:
        return ActivityCategory.academic

    return ActivityCategory.other


def _impact_weight(scope: ImpactScope | None) -> int:
    if scope is None:
        return 1
    return {
        ImpactScope.personal: 0,
        ImpactScope.family: 0,
        ImpactScope.school: 1,
        ImpactScope.local: 2,
        ImpactScope.regional: 3,
        ImpactScope.national: 4,
        ImpactScope.international: 5,
    }.get(scope, 1)


def _leadership_weight(level: LeadershipLevel | None) -> int:
    if level is None:
        return 1
    return {
        LeadershipLevel.none: 0,
        LeadershipLevel.member: 1,
        LeadershipLevel.lead: 3,
        LeadershipLevel.captain: 4,
        LeadershipLevel.founder: 5,
    }.get(level, 1)


def _signal_strength(achievement: Achievement) -> int:
    return _impact_weight(achievement.impact_scope) + _leadership_weight(
        achievement.leadership_level
    )


def categorize(
    achievements: Iterable[Achievement],
) -> list[CategorizedAchievement]:
    """Assign category + anchor/supporting/contextual roles.

    Heuristic:
    1. Bucket by inferred category.
    2. The category with the highest combined signal strength becomes the
       student's "spike". Top entry there is the anchor; the next two are
       supporting.
    3. Each other category contributes one contextual entry. Remaining
       entries fall back to supporting (their category) or contextual
       (breadth categories).
    User-supplied `activity_role` always overrides this assignment.
    """
    items = list(achievements)

    # First pass: derive categories.
    categorized: list[CategorizedAchievement] = []
    by_category: dict[ActivityCategory, list[CategorizedAchievement]] = defaultdict(list)
    for ach in items:
        category = infer_category(ach)
        categorized.append(
            CategorizedAchievement(achievement=ach, category=category, role=ActivityRole.contextual)
        )
        by_category[category].append(categorized[-1])

    # Sort each bucket by signal strength descending so anchors come first.
    for bucket in by_category.values():
        bucket.sort(
            key=lambda entry: _signal_strength(entry.achievement),
            reverse=True,
        )

    # Find the spike category: highest aggregate signal strength.
    spike_category: ActivityCategory | None = None
    spike_score = -1
    for category, bucket in by_category.items():
        if not bucket:
            continue
        score = sum(_signal_strength(item.achievement) for item in bucket)
        if score > spike_score:
            spike_score = score
            spike_category = category

    # Assign roles.
    anchor_count = 0
    supporting_count_in_spike = 0
    for entry in categorized:
        if entry.achievement.activity_role:
            entry.role = entry.achievement.activity_role
            continue

        if entry.category == spike_category:
            if anchor_count == 0:
                entry.role = ActivityRole.anchor
                anchor_count += 1
            elif supporting_count_in_spike < 2:
                entry.role = ActivityRole.supporting
                supporting_count_in_spike += 1
            else:
                entry.role = ActivityRole.supporting
        elif entry.category in _BREADTH_CATEGORIES:
            entry.role = ActivityRole.contextual
        else:
            # First entry in each non-spike bucket is contextual breadth;
            # subsequent ones are supporting within their own category.
            same_category = [
                e for e in categorized if e.category == entry.category and e.role != ActivityRole.contextual
            ]
            if not same_category:
                entry.role = ActivityRole.contextual
            else:
                entry.role = ActivityRole.supporting

    return categorized


def role_balance_summary(categorized: list[CategorizedAchievement]) -> str:
    """Human-readable one-liner describing the anchor/supporting/contextual mix."""
    if not categorized:
        return ""

    role_counts = Counter(item.role for item in categorized)
    category_counts = Counter(item.category for item in categorized)

    pieces: list[str] = []
    if role_counts.get(ActivityRole.anchor):
        anchor_categories = ", ".join(
            sorted({
                item.category.value
                for item in categorized
                if item.role == ActivityRole.anchor
            })
        )
        pieces.append(f"{role_counts[ActivityRole.anchor]} anchor ({anchor_categories})")
    if role_counts.get(ActivityRole.supporting):
        pieces.append(f"{role_counts[ActivityRole.supporting]} supporting")
    if role_counts.get(ActivityRole.contextual):
        pieces.append(f"{role_counts[ActivityRole.contextual]} contextual")

    breadth = sum(1 for cat in category_counts if cat in _BREADTH_CATEGORIES)
    if breadth:
        pieces.append(f"breadth in {breadth} domain(s)")

    return ", ".join(pieces)
