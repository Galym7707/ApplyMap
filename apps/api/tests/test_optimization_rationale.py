"""Light-weight tests for the optimization engine's rationale generation.

The full ``run_optimization`` path requires a database. These tests target
the deterministic helper that surfaces ActivityRole into the rationale
text, which is a small but visible piece of the transparency story.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

from src.models.achievement import (
    AchievementType,
    ActivityRole,
    ImpactScope,
    LeadershipLevel,
)
from src.models.report import RecommendationType
from src.services.optimization_engine import _generate_rationale


def _university(name: str = "Test U", preset: str = "balanced_holistic"):
    return SimpleNamespace(name=name, weight_preset=preset)


def _achievement():
    return SimpleNamespace(
        id=uuid.uuid4(),
        type=AchievementType.activity,
        title="National research fellowship",
        description_raw="Two-year research project on climate models.",
        impact_scope=ImpactScope.national,
        leadership_level=LeadershipLevel.lead,
    )


def test_rationale_calls_out_anchor_role():
    text = _generate_rationale(
        achievement=_achievement(),
        recommendation_type=RecommendationType.keep,
        rank=1,
        weights={},
        breakdown={"selectivity": 8.0, "impact_scope": 7.5},
        university=_university(),
        role=ActivityRole.anchor,
    )
    assert "anchor" in text.lower()


def test_rationale_calls_out_supporting_role():
    text = _generate_rationale(
        achievement=_achievement(),
        recommendation_type=RecommendationType.keep,
        rank=2,
        weights={},
        breakdown={"selectivity": 7.0},
        university=_university(),
        role=ActivityRole.supporting,
    )
    assert "supports" in text.lower()


def test_rationale_calls_out_contextual_role():
    text = _generate_rationale(
        achievement=_achievement(),
        recommendation_type=RecommendationType.keep,
        rank=5,
        weights={},
        breakdown={"continuity": 6.0},
        university=_university(),
        role=ActivityRole.contextual,
    )
    assert "breadth" in text.lower()


def test_rationale_remains_neutral_without_role():
    text = _generate_rationale(
        achievement=_achievement(),
        recommendation_type=RecommendationType.keep,
        rank=3,
        weights={},
        breakdown={"distinctiveness": 6.0},
        university=_university(),
    )
    # Sanity: should not mention any of the role-specific phrases when role is None.
    assert "anchor" not in text.lower()
    assert "supports your strongest theme" not in text.lower()
    assert "adds breadth" not in text.lower()
