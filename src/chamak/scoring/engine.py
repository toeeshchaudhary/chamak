"""Weighted-rule compatibility scoring.

Formula:

    score = Σ_r ( w_r · sat_r · conf_r ) / Σ_r ( w_r · conf_r )

over the *soft* rules. A hard-rule failure (sat < HARD_THRESHOLD) gates the
score to 0 and is reported in `hard_failures`. Missing metrics don't count
toward numerator or denominator.

Polarity:
- "prefer" rules contribute their satisfaction directly.
- "avoid" rules contribute (1 - satisfaction). The text "avoid X" should
  be encoded so satisfaction reads as "true match for the thing to avoid",
  and we invert in the score.

Confidence (overall):
    confidence = (Σ_r conf_r · w_r) / (Σ_r w_r)   over rules that evaluated
"""

from __future__ import annotations

from chamak.core.models import (
    MindMapSnapshot,
    RuleContribution,
    ScoreBreakdown,
    StockFundamentals,
)
from chamak.rules.evaluator import EvalResult, evaluate

HARD_THRESHOLD = 0.5  # below this, a hard rule is considered failed


def _polarity_adjust(sat: float, polarity: str) -> float:
    return 1.0 - sat if polarity == "avoid" else sat


def score(snap: MindMapSnapshot, fund: StockFundamentals) -> ScoreBreakdown:
    contribs: list[RuleContribution] = []
    ctx = dict(fund.metrics)
    hard_failures: list[str] = []
    missing: set[str] = set()
    gated = False
    notes: list[str] = []

    if not snap.rules:
        notes.append("Mind map has no rules — score reflects the empty model.")

    num = 0.0
    denom = 0.0
    conf_num = 0.0
    conf_denom = 0.0

    for r in snap.rules:
        result: EvalResult = evaluate(r.ast_json, ctx)
        if result.missing:
            missing.add(result.missing_metric or "unknown")
            contribs.append(
                RuleContribution(
                    rule_id=r.id,
                    rule_text=r.text,
                    node_id=r.node_id,
                    satisfaction=0.0,
                    weight=r.weight,
                    confidence=r.confidence,
                    hard=r.hard,
                    gated=False,
                    missing_metric=result.missing_metric,
                    contribution=0.0,
                )
            )
            continue

        adj = _polarity_adjust(result.value, r.polarity)

        if r.hard and adj < HARD_THRESHOLD:
            gated = True
            hard_failures.append(r.text)

        contribution = r.weight * adj * r.confidence
        num += contribution
        denom += r.weight * r.confidence
        conf_num += r.confidence * r.weight
        conf_denom += r.weight

        contribs.append(
            RuleContribution(
                rule_id=r.id,
                rule_text=r.text,
                node_id=r.node_id,
                satisfaction=adj,
                weight=r.weight,
                confidence=r.confidence,
                hard=r.hard,
                gated=r.hard and adj < HARD_THRESHOLD,
                contribution=contribution,
            )
        )

    raw_score = (num / denom) if denom > 0 else 0.0
    final_score = 0.0 if gated else raw_score
    overall_conf = (conf_num / conf_denom) if conf_denom > 0 else 0.0

    if missing:
        notes.append(
            f"{len(missing)} metric(s) missing from snapshot; those rules were skipped."
        )
    if gated:
        notes.append("A hard rule failed — score gated to 0.")

    return ScoreBreakdown(
        ticker=fund.ticker,
        mindmap_id=snap.mindmap.id,
        score=round(final_score, 4),
        confidence=round(overall_conf, 4),
        contributions=contribs,
        hard_failures=hard_failures,
        missing=sorted(missing),
        notes=notes,
    )
