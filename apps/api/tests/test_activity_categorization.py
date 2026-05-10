"""Tests for the deterministic activity categorization service."""
from __future__ import annotations

import uuid
from types import SimpleNamespace

from src.models.achievement import (
    ActivityCategory,
    ActivityRole,
    AchievementType,
    ImpactScope,
    LeadershipLevel,
)
from src.services.activity_categorization import (
    categorize,
    infer_category,
    role_balance_summary,
)


def _make_achievement(**kwargs):
    """Build an Achievement-like object without hitting the database."""
    defaults = dict(
        id=uuid.uuid4(),
        type=AchievementType.activity,
        title="",
        organization_name=None,
        role_title=None,
        description_raw=None,
        category=None,
        impact_scope=None,
        leadership_level=None,
        activity_category=None,
        activity_role=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_infer_category_picks_research_keyword():
    ach = _make_achievement(title="Undergraduate research assistant", description_raw="lab work")
    assert infer_category(ach) == ActivityCategory.research


def test_infer_category_respects_user_override():
    ach = _make_achievement(
        title="Mathematics olympiad gold",
        activity_category=ActivityCategory.business,
    )
    assert infer_category(ach) == ActivityCategory.business


def test_infer_category_handles_russian_keywords():
    ach = _make_achievement(title="\u0412\u043e\u043b\u043e\u043d\u0442\u0435\u0440 \u0432 \u0431\u043e\u043b\u044c\u043d\u0438\u0446\u0435")  # "Volunteer at a hospital"
    assert infer_category(ach) == ActivityCategory.volunteering


def test_infer_category_falls_back_to_other_for_blank_text():
    ach = _make_achievement()
    assert infer_category(ach) == ActivityCategory.other


def test_infer_category_defaults_honor_to_academic():
    ach = _make_achievement(
        type=AchievementType.honor,
        title="Distinguished medal",
    )
    assert infer_category(ach) == ActivityCategory.academic


def test_categorize_marks_top_signal_as_anchor():
    research_anchor = _make_achievement(
        title="National science research project",
        impact_scope=ImpactScope.national,
        leadership_level=LeadershipLevel.lead,
    )
    research_supporting = _make_achievement(
        title="Lab assistant in chemistry research",
        impact_scope=ImpactScope.school,
        leadership_level=LeadershipLevel.member,
    )
    arts_breadth = _make_achievement(
        title="School orchestra violinist",
        impact_scope=ImpactScope.school,
        leadership_level=LeadershipLevel.member,
    )

    results = categorize([research_anchor, research_supporting, arts_breadth])
    by_id = {item.achievement.id: item for item in results}

    assert by_id[research_anchor.id].role == ActivityRole.anchor
    assert by_id[research_anchor.id].category == ActivityCategory.research
    assert by_id[research_supporting.id].role == ActivityRole.supporting
    assert by_id[arts_breadth.id].role == ActivityRole.contextual
    assert by_id[arts_breadth.id].category == ActivityCategory.arts


def test_categorize_respects_user_supplied_role():
    forced_anchor = _make_achievement(
        title="Family responsibility caring for younger siblings",
        impact_scope=ImpactScope.family,
        activity_role=ActivityRole.anchor,
    )
    research = _make_achievement(
        title="National research olympiad",
        impact_scope=ImpactScope.national,
        leadership_level=LeadershipLevel.founder,
    )

    results = categorize([forced_anchor, research])
    by_id = {item.achievement.id: item for item in results}

    # Even though research has higher signal, user-marked anchor stays.
    assert by_id[forced_anchor.id].role == ActivityRole.anchor


def test_role_balance_summary_includes_anchor_category_and_breadth():
    items = categorize([
        _make_achievement(
            title="National research project",
            impact_scope=ImpactScope.national,
            leadership_level=LeadershipLevel.lead,
        ),
        _make_achievement(
            title="School orchestra violinist",
            impact_scope=ImpactScope.school,
        ),
    ])
    summary = role_balance_summary(items)
    assert "anchor" in summary
    assert "research" in summary
    assert "breadth" in summary


def test_role_balance_summary_empty():
    assert role_balance_summary([]) == ""
