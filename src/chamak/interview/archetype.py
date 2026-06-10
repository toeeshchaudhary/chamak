"""Map an answer dict to a human-readable investor archetype."""

from __future__ import annotations


ARCHETYPES = {
    "value":   "Value Investor",
    "garp":    "GARP Investor",
    "growth":  "Growth Investor",
    "income":  "Income / Dividend Investor",
    "quality": "Quality Compounder",
    "owner":   "Owner-Operator Mindset",
    "unknown": "Generalist",
}


def classify(answers: dict) -> str:
    val = (answers.get("valuation") or "").lower()
    horizon = (answers.get("horizon") or "").lower()
    risk = (answers.get("risk") or "").lower()
    quality = answers.get("quality") or []
    if isinstance(quality, str):
        quality = [quality]

    if val == "agnostic" or "high_roe" in quality or "high_margin" in quality:
        if horizon in ("long", "forever"):
            return ARCHETYPES["quality"]
    if val == "value":
        return ARCHETYPES["value"]
    if val == "growth":
        return ARCHETYPES["growth"]
    if val == "garp":
        return ARCHETYPES["garp"]
    if horizon == "forever" and risk in ("medium", "low"):
        return ARCHETYPES["owner"]
    return ARCHETYPES["unknown"]
