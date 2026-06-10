"""Convert a ScoreBreakdown into ultra-friendly card-ready text.

Goal: a regular person — even a child — should read it and get it.
"""

from __future__ import annotations

from chamak.core.models import MindMapSnapshot, ScoreBreakdown
from chamak.rules.plain import translate_rule


def stars(score: float) -> str:
    """5-star rating string with empty/filled glyphs."""
    if score >= 0.75:
        return "★ ★ ★ ★ ★"
    if score >= 0.60:
        return "★ ★ ★ ★ ☆"
    if score >= 0.45:
        return "★ ★ ★ ☆ ☆"
    if score >= 0.25:
        return "★ ★ ☆ ☆ ☆"
    return "★ ☆ ☆ ☆ ☆"


def friendly_reasons(b: ScoreBreakdown, snap: MindMapSnapshot, *, limit: int = 3) -> list[str]:
    """Top reasons it fits, in everyday English."""
    ast_by_id = {r.id: (r.ast_json, r.polarity) for r in snap.rules}
    matched = sorted(
        (c for c in b.contributions
         if not c.missing_metric and c.satisfaction >= 0.5),
        key=lambda c: c.contribution,
        reverse=True,
    )
    out: list[str] = []
    seen_metrics: set[str] = set()
    for c in matched:
        if len(out) >= limit:
            break
        ast_polarity = ast_by_id.get(c.rule_id)
        if not ast_polarity:
            continue
        ast, polarity = ast_polarity
        prose = translate_rule(ast, polarity=polarity)
        # dedupe by leading verb-phrase to avoid two near-identical reasons
        head = prose[:30]
        if head in seen_metrics:
            continue
        seen_metrics.add(head)
        out.append(prose)
    return out


def friendly_concerns(b: ScoreBreakdown, snap: MindMapSnapshot, *, limit: int = 2) -> list[str]:
    ast_by_id = {r.id: (r.ast_json, r.polarity) for r in snap.rules}
    failed = sorted(
        (c for c in b.contributions
         if not c.missing_metric and c.satisfaction < 0.5),
        key=lambda c: c.weight,
        reverse=True,
    )
    out: list[str] = []
    seen: set[str] = set()
    for c in failed:
        if len(out) >= limit:
            break
        ast_polarity = ast_by_id.get(c.rule_id)
        if not ast_polarity:
            continue
        ast, polarity = ast_polarity
        prose = translate_rule(ast, polarity=polarity)
        # Reframe as a concern: "doesn't ..."
        if prose.startswith("The company "):
            concern = "Doesn't quite — " + prose[len("The company ") :].lower()
        else:
            concern = prose
        head = concern[:30]
        if head in seen:
            continue
        seen.add(head)
        out.append(concern)
    return out


def headline_for(score: float, *, hard_fail: bool = False) -> str:
    if hard_fail:
        return "Probably not for you — breaks something you said matters."
    if score >= 0.75:
        return "Looks like a really strong fit for how you think."
    if score >= 0.60:
        return "A solid fit — most of what you care about lines up."
    if score >= 0.45:
        return "Mixed — some things you like, some you wouldn't."
    return "Doesn't really fit what you said you want."
