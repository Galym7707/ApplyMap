"""
Optimization engine for ranking and recommending achievements.
Uses weighted scoring based on university-specific weight presets.
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from uuid import UUID

from ..models.achievement import Achievement, AchievementType, ImpactScope, LeadershipLevel
from ..models.university import University, WeightPreset
from ..models.report import (
    OptimizationReport, ReportRecommendation, SourceReference,
    RecommendationType, ConfidenceLabel, SourceSection, ReportStatus
)


# Weight configurations per preset
WEIGHT_PRESETS: Dict[str, Dict[str, float]] = {
    WeightPreset.research_heavy: {
        "impact_scope": 0.15,
        "selectivity": 0.25,
        "leadership": 0.10,
        "continuity": 0.15,
        "major_relevance": 0.25,
        "distinctiveness": 0.10,
        "clarity": 0.05,
        "duplication_penalty": 2.0,
    },
    WeightPreset.leadership_heavy: {
        "impact_scope": 0.20,
        "selectivity": 0.10,
        "leadership": 0.30,
        "continuity": 0.15,
        "major_relevance": 0.10,
        "distinctiveness": 0.10,
        "clarity": 0.05,
        "duplication_penalty": 2.0,
    },
    WeightPreset.balanced_holistic: {
        "impact_scope": 0.20,
        "selectivity": 0.15,
        "leadership": 0.15,
        "continuity": 0.15,
        "major_relevance": 0.15,
        "distinctiveness": 0.15,
        "clarity": 0.05,
        "duplication_penalty": 2.0,
    },
    WeightPreset.community_service_heavy: {
        "impact_scope": 0.30,
        "selectivity": 0.10,
        "leadership": 0.15,
        "continuity": 0.20,
        "major_relevance": 0.10,
        "distinctiveness": 0.10,
        "clarity": 0.05,
        "duplication_penalty": 2.0,
    },
}

# Numeric mappings for enum values
IMPACT_SCOPE_MAP: Dict[str, float] = {
    ImpactScope.school: 3.0,
    ImpactScope.local: 4.0,
    ImpactScope.regional: 6.0,
    ImpactScope.national: 8.5,
    ImpactScope.international: 10.0,
    ImpactScope.family: 2.0,
    ImpactScope.personal: 1.0,
}

LEADERSHIP_MAP: Dict[str, float] = {
    LeadershipLevel.none: 1.0,
    LeadershipLevel.member: 4.0,
    LeadershipLevel.lead: 7.0,
    LeadershipLevel.captain: 8.5,
    LeadershipLevel.founder: 10.0,
}


@dataclass
class ScoredAchievement:
    achievement: Achievement
    raw_score: float
    breakdown: Dict[str, float]
    is_duplicate: bool
    duplicate_of: Optional[UUID]


def _get_impact_score(achievement: Achievement) -> float:
    if achievement.impact_scope:
        return IMPACT_SCOPE_MAP.get(achievement.impact_scope, 5.0)
    return 5.0  # default middle value


def _get_leadership_score(achievement: Achievement) -> float:
    if achievement.leadership_level:
        return LEADERSHIP_MAP.get(achievement.leadership_level, 4.0)
    return 4.0


def _get_clarity_score(achievement: Achievement) -> float:
    """Estimate clarity from description completeness."""
    score = 0.0
    if achievement.description_raw and len(achievement.description_raw) > 30:
        score += 4.0
    if achievement.role_title:
        score += 2.0
    if achievement.organization_name:
        score += 2.0
    if achievement.hours_per_week:
        score += 1.0
    if achievement.start_date:
        score += 1.0
    return min(score, 10.0)


def _detect_duplicates(achievements: List[Achievement]) -> Dict[UUID, Optional[UUID]]:
    """Detect duplicate achievements based on organization and overlapping titles."""
    duplicate_map: Dict[UUID, Optional[UUID]] = {}
    seen: List[Achievement] = []

    for ach in achievements:
        is_dup = False
        for prev in seen:
            # Same org and similar title suggests duplication
            if (
                ach.organization_name
                and prev.organization_name
                and ach.organization_name.lower().strip() == prev.organization_name.lower().strip()
            ):
                ach_words = set((ach.title or "").lower().split())
                prev_words = set((prev.title or "").lower().split())
                if ach_words and prev_words:
                    overlap = len(ach_words & prev_words) / max(len(ach_words), len(prev_words))
                    if overlap > 0.5:
                        duplicate_map[ach.id] = prev.id
                        is_dup = True
                        break
        if not is_dup:
            duplicate_map[ach.id] = None
            seen.append(ach)

    return duplicate_map


def score_achievement(
    achievement: Achievement,
    weights: Dict[str, float],
    is_duplicate: bool = False,
) -> Tuple[float, Dict[str, float]]:
    """Score a single achievement using the given weight configuration."""

    impact = _get_impact_score(achievement)
    selectivity = achievement.selectivity_score if achievement.selectivity_score is not None else 5.0
    leadership = _get_leadership_score(achievement)
    continuity = achievement.continuity_score if achievement.continuity_score is not None else 5.0
    major_relevance = achievement.major_relevance_score if achievement.major_relevance_score is not None else 5.0
    distinctiveness = achievement.distinctiveness_score if achievement.distinctiveness_score is not None else 5.0
    clarity = _get_clarity_score(achievement)

    breakdown = {
        "impact_scope": impact * weights["impact_scope"],
        "selectivity": selectivity * weights["selectivity"],
        "leadership": leadership * weights["leadership"],
        "continuity": continuity * weights["continuity"],
        "major_relevance": major_relevance * weights["major_relevance"],
        "distinctiveness": distinctiveness * weights["distinctiveness"],
        "clarity": clarity * weights["clarity"],
    }

    raw = sum(breakdown.values())

    if is_duplicate:
        raw -= weights["duplication_penalty"]

    return raw, breakdown


def _calculate_confidence(achievement: Achievement, score: float, all_scores: List[float]) -> ConfidenceLabel:
    """Determine confidence label based on data completeness and score spread."""
    filled_fields = sum([
        1 if achievement.impact_scope else 0,
        1 if achievement.selectivity_score is not None else 0,
        1 if achievement.leadership_level else 0,
        1 if achievement.continuity_score is not None else 0,
        1 if achievement.major_relevance_score is not None else 0,
        1 if achievement.distinctiveness_score is not None else 0,
        1 if achievement.description_raw else 0,
    ])

    if filled_fields >= 6:
        completeness = "high"
    elif filled_fields >= 3:
        completeness = "medium"
    else:
        completeness = "low"

    if len(all_scores) > 1:
        score_range = max(all_scores) - min(all_scores)
        if score_range < 1.0:
            spread = "low"
        elif score_range < 3.0:
            spread = "medium"
        else:
            spread = "high"
    else:
        spread = "medium"

    if completeness == "high" and spread in ("medium", "high"):
        return ConfidenceLabel.high
    elif completeness == "low" or spread == "low":
        return ConfidenceLabel.low
    else:
        return ConfidenceLabel.medium


def _generate_rationale(
    achievement: Achievement,
    recommendation_type: RecommendationType,
    rank: Optional[int],
    weights: Dict[str, float],
    breakdown: Dict[str, float],
    university: University,
) -> str:
    """Generate a human-readable rationale for the recommendation."""
    lines = []

    if recommendation_type == RecommendationType.keep:
        lines.append(f"Recommended for {university.name} (#{rank}) based on {university.weight_preset.replace('_', ' ')} criteria.")

        # Find top contributing factors
        sorted_factors = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
        top_factors = [f[0].replace("_", " ") for f in sorted_factors[:2]]
        lines.append(f"Strongest factors: {', '.join(top_factors)}.")

        if achievement.impact_scope in (ImpactScope.national, ImpactScope.international):
            lines.append(f"Noteworthy {achievement.impact_scope.value}-level impact.")

        if achievement.leadership_level in (LeadershipLevel.founder, LeadershipLevel.captain):
            lines.append(f"Leadership role ({achievement.leadership_level.value}) adds significant weight.")

    elif recommendation_type == RecommendationType.remove:
        lines.append(f"Not recommended for inclusion in your {university.name} application.")
        lines.append("Score falls below the threshold given your other achievements and this university's priorities.")
        if achievement.impact_scope in (ImpactScope.personal, ImpactScope.family):
            lines.append("Limited external impact scope reduces fit for this university profile.")

    elif recommendation_type == RecommendationType.rewrite:
        lines.append(f"Strong potential — keep for {university.name} but the description needs sharpening.")
        if not achievement.description_raw or len(achievement.description_raw) < 50:
            lines.append("Current description is too brief to convey full impact.")
        lines.append("Use the Rewrite Studio to tighten language and lead with impact.")

    elif recommendation_type == RecommendationType.merge:
        lines.append("Overlaps significantly with another entry. Consider merging to avoid duplication.")
        lines.append("Admissions readers notice repetition — a single strong entry outperforms two weak ones.")

    elif recommendation_type == RecommendationType.reorder:
        lines.append(f"Include at position #{rank}. Ordering here is important — earlier positions receive more attention.")

    return " ".join(lines)


def run_optimization(
    db: Session,
    report: OptimizationReport,
    achievements: List[Achievement],
    university: University,
) -> None:
    """
    Run the full optimization pipeline and populate the report with recommendations.
    """
    weights = WEIGHT_PRESETS.get(university.weight_preset, WEIGHT_PRESETS[WeightPreset.balanced_holistic])

    activities = [a for a in achievements if a.type == AchievementType.activity]
    honors = [a for a in achievements if a.type == AchievementType.honor]

    dup_map_activities = _detect_duplicates(activities)
    dup_map_honors = _detect_duplicates(honors)

    def score_list(items: List[Achievement], dup_map: dict) -> List[ScoredAchievement]:
        scored = []
        for ach in items:
            is_dup = dup_map.get(ach.id) is not None
            dup_of = dup_map.get(ach.id)
            raw, breakdown = score_achievement(ach, weights, is_duplicate=is_dup)
            scored.append(ScoredAchievement(
                achievement=ach,
                raw_score=raw,
                breakdown=breakdown,
                is_duplicate=is_dup,
                duplicate_of=dup_of,
            ))
        scored.sort(key=lambda x: x.raw_score, reverse=True)
        return scored

    scored_activities = score_list(activities, dup_map_activities)
    scored_honors = score_list(honors, dup_map_honors)

    all_activity_scores = [s.raw_score for s in scored_activities]
    all_honor_scores = [s.raw_score for s in scored_honors]

    recommendations = []

    # Process activities: top 10 keep, rest remove/merge
    for rank, scored in enumerate(scored_activities, start=1):
        ach = scored.achievement

        if scored.is_duplicate:
            rec_type = RecommendationType.merge
            suggested_rank = None
        elif rank <= 10:
            if not ach.description_raw or len(ach.description_raw or "") < 30:
                rec_type = RecommendationType.rewrite
            else:
                rec_type = RecommendationType.keep
            suggested_rank = rank
        else:
            rec_type = RecommendationType.remove
            suggested_rank = None

        confidence = _calculate_confidence(ach, scored.raw_score, all_activity_scores)
        rationale = _generate_rationale(ach, rec_type, suggested_rank, weights, scored.breakdown, university)

        rec = ReportRecommendation(
            report_id=report.id,
            achievement_id=ach.id,
            recommendation_type=rec_type,
            suggested_rank=suggested_rank,
            rationale=rationale,
            confidence_label=confidence,
        )
        recommendations.append(rec)

    # Process honors: top 5 keep, rest remove
    for rank, scored in enumerate(scored_honors, start=1):
        ach = scored.achievement

        if scored.is_duplicate:
            rec_type = RecommendationType.merge
            suggested_rank = None
        elif rank <= 5:
            if not ach.description_raw or len(ach.description_raw or "") < 30:
                rec_type = RecommendationType.rewrite
            else:
                rec_type = RecommendationType.keep
            suggested_rank = rank
        else:
            rec_type = RecommendationType.remove
            suggested_rank = None

        confidence = _calculate_confidence(ach, scored.raw_score, all_honor_scores)
        rationale = _generate_rationale(ach, rec_type, suggested_rank, weights, scored.breakdown, university)

        rec = ReportRecommendation(
            report_id=report.id,
            achievement_id=ach.id,
            recommendation_type=rec_type,
            suggested_rank=suggested_rank,
            rationale=rationale,
            confidence_label=confidence,
        )
        recommendations.append(rec)

    db.add_all(recommendations)

    # Add source references from university policy entries
    for entry in university.policy_entries:
        section = (
            SourceSection.official_guidance
            if entry.source_type.value == "official"
            else SourceSection.public_examples
        )
        source_ref = SourceReference(
            report_id=report.id,
            university_policy_entry_id=entry.id,
            section=section,
            note=f"Referenced for {university.name} application context.",
        )
        db.add(source_ref)

    # Build summary text
    kept_acts = sum(1 for r in recommendations if r.recommendation_type == RecommendationType.keep and r.achievement_id in {a.achievement.id for a in scored_activities})
    kept_honors = sum(1 for r in recommendations if r.recommendation_type == RecommendationType.keep and r.achievement_id in {a.achievement.id for a in scored_honors})

    report.summary_text = (
        f"Optimization complete for {university.name} ({university.weight_preset.replace('_', ' ')} profile). "
        f"Recommended: {kept_acts} activities and {kept_honors} honors. "
        f"Weight emphasis: {', '.join(k for k, v in weights.items() if isinstance(v, float) and v >= 0.20 and k != 'duplication_penalty')}."
    )
    report.status = ReportStatus.completed
    report.completed_at = __import__("datetime").datetime.utcnow()

    db.commit()
