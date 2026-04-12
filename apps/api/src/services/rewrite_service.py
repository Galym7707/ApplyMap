"""
Rewrite service for generating style variants of achievement descriptions.
Enforces Common App character limits without inventing facts.
"""
import re
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session

from ..models.achievement import Achievement
from ..models.report import OptimizationReport, RewriteVariant

# Common App limits
ACTIVITY_DESC_LIMIT = 150  # characters for activity description
ACTIVITY_NAME_LIMIT = 100  # characters for activity title/name


def _truncate_to_limit(text: str, limit: int) -> str:
    """Hard truncate text to character limit, breaking at word boundary."""
    if len(text) <= limit:
        return text
    truncated = text[:limit]
    last_space = truncated.rfind(" ")
    if last_space > limit - 20:
        truncated = truncated[:last_space]
    return truncated.rstrip(",.;:")


def _extract_key_facts(achievement: Achievement) -> Dict[str, str]:
    """Extract factual elements from the achievement for use in rewrites."""
    facts = {}
    if achievement.title:
        facts["title"] = achievement.title
    if achievement.organization_name:
        facts["org"] = achievement.organization_name
    if achievement.role_title:
        facts["role"] = achievement.role_title
    if achievement.description_raw:
        facts["description"] = achievement.description_raw
    if achievement.hours_per_week:
        facts["hours"] = f"{achievement.hours_per_week:.0f} hrs/wk"
    if achievement.weeks_per_year:
        facts["weeks"] = f"{achievement.weeks_per_year} wks/yr"
    if achievement.impact_scope:
        facts["scope"] = achievement.impact_scope.value
    if achievement.leadership_level and achievement.leadership_level.value != "none":
        facts["leadership"] = achievement.leadership_level.value
    return facts


def _style_factual(achievement: Achievement, facts: Dict[str, str]) -> str:
    """Factual style: clear, precise, chronological. State what you did."""
    parts = []
    if facts.get("role") and facts.get("org"):
        parts.append(f"{facts['role']} at {facts['org']}")
    elif facts.get("role"):
        parts.append(facts["role"])
    elif facts.get("org"):
        parts.append(f"Member of {facts['org']}")

    desc = facts.get("description", "")
    if desc:
        # Strip filler phrases, keep direct statements
        cleaned = re.sub(r"\b(I |we |our team |basically |really |very )\b", "", desc, flags=re.IGNORECASE).strip()
        parts.append(cleaned)

    commitment = []
    if facts.get("hours"):
        commitment.append(facts["hours"])
    if facts.get("weeks"):
        commitment.append(facts["weeks"])
    if commitment:
        parts.append(f"Commitment: {', '.join(commitment)}")

    text = ". ".join(p.rstrip(".") for p in parts if p).strip()
    if text and not text.endswith("."):
        text += "."

    return _truncate_to_limit(text, ACTIVITY_DESC_LIMIT)


def _style_impact_first(achievement: Achievement, facts: Dict[str, str]) -> str:
    """Impact-first style: lead with the outcome or scope, then explain role."""
    parts = []

    desc = facts.get("description", "")
    scope = facts.get("scope", "")
    leadership = facts.get("leadership", "")

    # Lead with impact scope if notable
    if scope in ("national", "international", "regional"):
        parts.append(f"{scope.capitalize()}-level engagement")
    elif desc:
        # Try to pull an impact sentence from description
        sentences = re.split(r"[.!?]", desc)
        for s in sentences:
            if any(word in s.lower() for word in ["led", "founded", "created", "built", "raised", "won", "achieved", "launched"]):
                parts.append(s.strip())
                break
        if not parts:
            parts.append(sentences[0].strip() if sentences else desc)

    # Add role/org context
    if facts.get("role") and facts.get("org"):
        parts.append(f"{facts['role']}, {facts['org']}")
    elif facts.get("leadership") and facts.get("org"):
        parts.append(f"{leadership.capitalize()} role at {facts['org']}")

    # Remaining description detail
    if desc and len(parts) < 3:
        remaining = desc
        for p in parts:
            remaining = remaining.replace(p, "").strip()
        if remaining and len(remaining) > 20:
            parts.append(remaining.rstrip("."))

    text = ". ".join(p.rstrip(".") for p in parts if p).strip()
    if text and not text.endswith("."):
        text += "."

    return _truncate_to_limit(text, ACTIVITY_DESC_LIMIT)


def _style_understated(achievement: Achievement, facts: Dict[str, str]) -> str:
    """Understated style: humble, precise, let the facts speak. No self-promotion language."""
    parts = []

    desc = facts.get("description", "")

    # Remove promotional language
    if desc:
        cleaned = re.sub(
            r"\b(passionate|dedicated|committed|driven|hardworking|exceptional|outstanding|incredible|amazing|impactful)\b",
            "",
            desc,
            flags=re.IGNORECASE,
        ).strip()
        # Compress whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        parts.append(cleaned)

    if facts.get("org"):
        org_note = f"via {facts['org']}"
        if org_note not in " ".join(parts):
            parts.append(org_note)

    commitment = []
    if facts.get("hours"):
        commitment.append(facts["hours"])
    if facts.get("weeks"):
        commitment.append(facts["weeks"])
    if commitment:
        parts.append(", ".join(commitment))

    text = "; ".join(p.rstrip(";.,") for p in parts if p).strip()
    if text and not text.endswith("."):
        text += "."

    return _truncate_to_limit(text, ACTIVITY_DESC_LIMIT)


def generate_rewrite_variants(
    db: Session,
    achievement: Achievement,
    report: OptimizationReport,
) -> List[RewriteVariant]:
    """
    Generate 3 style variants for an achievement.
    Returns RewriteVariant objects (not yet committed to DB).
    """
    facts = _extract_key_facts(achievement)

    styles: List[Tuple[str, str, bool, str]] = [
        (
            "factual",
            _style_factual(achievement, facts),
            False,
            "Clear, precise description stating what you did, where, and with what time commitment.",
        ),
        (
            "impact_first",
            _style_impact_first(achievement, facts),
            True,  # default recommended
            "Leads with the outcome or scope of impact before explaining your role.",
        ),
        (
            "understated",
            _style_understated(achievement, facts),
            False,
            "Humble, concise version — lets the facts speak without promotional language.",
        ),
    ]

    variants = []
    for style_mode, text, is_recommended, explanation in styles:
        if not text:
            text = _truncate_to_limit(
                achievement.description_raw or achievement.title or "",
                ACTIVITY_DESC_LIMIT,
            )
        variant = RewriteVariant(
            achievement_id=achievement.id,
            report_id=report.id,
            style_mode=style_mode,
            text=text,
            character_count=len(text),
            is_recommended=is_recommended,
            explanation=explanation,
        )
        variants.append(variant)

    return variants
