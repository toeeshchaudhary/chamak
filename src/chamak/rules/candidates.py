"""Heuristic + LLM-assisted candidate rule extraction from narrative beliefs.

The heuristic layer catches common patterns ("low debt", "high ROE", "avoid
expensive stocks", "I want growing companies") with no model call. The LLM
path (when an OPENROUTER_API_KEY is configured) takes the same text and asks
for a structured JSON of candidates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class RuleCandidate:
    metric: str
    op: str             # "<", "<=", ">", ">="
    value: float
    polarity: str       # "prefer" | "avoid"
    rationale: str
    confidence: float
    source: str         # "heuristic" | "llm"


# Each entry: (regex, metric, op, default_value, polarity, rationale)
_PATTERNS: list[tuple[re.Pattern[str], str, str, float, str, str]] = [
    (re.compile(r"\b(low|less|low[-\s]?)?\s*debt\b", re.I),
     "debt_to_equity", "<", 0.5, "prefer", "Low debt preference"),
    (re.compile(r"\bdebt[-\s]free\b", re.I),
     "debt_to_equity", "<", 0.1, "prefer", "Debt-free companies"),
    (re.compile(r"\bhigh\s*(roe|return on equity)\b", re.I),
     "roe", ">", 15.0, "prefer", "High ROE preference"),
    (re.compile(r"\bhigh\s*(roce|return on capital)\b", re.I),
     "roce", ">", 15.0, "prefer", "High ROCE preference"),
    (re.compile(r"\bgrowing|growth\b", re.I),
     "revenue_growth", ">", 10.0, "prefer", "Revenue growth preference"),
    (re.compile(r"\b(cheap|low\s*pe|undervalued)\b", re.I),
     "pe", "<", 20.0, "prefer", "Inexpensive valuation"),
    (re.compile(r"\b(expensive|overvalued)\b", re.I),
     "pe", ">", 40.0, "avoid", "Avoid expensive valuations"),
    (re.compile(r"\bdividend\b", re.I),
     "dividend_yield", ">", 2.0, "prefer", "Dividend-paying companies"),
    (re.compile(r"\bquality\b", re.I),
     "roe", ">", 15.0, "prefer", "Quality proxy (high ROE)"),
    (re.compile(r"\bsurvived|long\s*track\s*record|cycles\b", re.I),
     "years_since_listing", ">", 10.0, "prefer", "Long operating history"),
    (re.compile(r"\bpledg(ed|ing)\b", re.I),
     "pledged_pct", "<", 5.0, "prefer", "Low pledged shares"),
    (re.compile(r"\bpromoter\b", re.I),
     "promoter_holding", ">", 50.0, "prefer", "Skin-in-the-game promoter holding"),
    (re.compile(r"\bsmall[-\s]?cap\b", re.I),
     "market_cap_cr", "<", 5000.0, "prefer", "Small-cap preference"),
    (re.compile(r"\b(large|big)[-\s]?cap\b", re.I),
     "market_cap_cr", ">", 50000.0, "prefer", "Large-cap preference"),
    (re.compile(r"\bmargin\b", re.I),
     "operating_margin", ">", 15.0, "prefer", "Margin preference"),
]


def heuristic_candidates(text: str) -> list[RuleCandidate]:
    out: list[RuleCandidate] = []
    seen: set[tuple[str, str, float]] = set()
    for pat, metric, op, value, polarity, rationale in _PATTERNS:
        if pat.search(text):
            key = (metric, op, value)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                RuleCandidate(
                    metric=metric, op=op, value=value, polarity=polarity,
                    rationale=rationale, confidence=0.55, source="heuristic",
                )
            )
    return out


def candidates(text: str, *, llm=None) -> list[RuleCandidate]:
    """Combined extraction. LLM path runs only when an llm client is provided
    and returns parseable structured output; otherwise heuristics only."""
    cands = heuristic_candidates(text)
    if llm is None:
        return cands
    try:
        llm_cands = llm.extract_rule_candidates(text)
    except Exception:
        return cands
    # merge, preferring higher confidence
    def key(c: RuleCandidate) -> tuple[str, str, float]:
        return (c.metric, c.op, round(c.value, 4))

    by_key: dict[tuple, RuleCandidate] = {key(c): c for c in cands}
    for c in llm_cands:
        k = key(c)
        if k not in by_key or c.confidence > by_key[k].confidence:
            by_key[k] = c
    return list(by_key.values())
