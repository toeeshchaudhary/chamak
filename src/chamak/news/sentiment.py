"""Heuristic multi-label sentiment for news headlines.

Pattern-based first pass that runs offline. LLM-backed classifier can swap
in behind the same `SentimentClassifier` protocol without changing callers.
Labels match `chamak.news.base.SentimentLabel`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from chamak.news.base import NewsItem, SentimentTag


@dataclass(frozen=True)
class _Rule:
    label: str
    patterns: list[re.Pattern[str]]
    base_confidence: float = 0.6


def _r(label: str, *terms: str, conf: float = 0.6) -> _Rule:
    return _Rule(label, [re.compile(rf"\b{t}\b", re.I) for t in terms], conf)


_RULES: list[_Rule] = [
    _r("bullish", "beats", "record", "surge", "rally", "outperforms", "upgrade",
       "ten-year deal", "all-time high", "bags.*deal", "ARPU climbs", conf=0.7),
    _r("bearish", "misses", "downgrade", "slips", "plunges", "weakness", "compression",
       "losses persist", "warning", "scrutiny", "below estimates", "loses share", conf=0.7),
    _r("growth_signal", "growth", "expansion", "specialty.*inflects", "record monthly",
       "above plan", "outpacing", "tailwind", conf=0.65),
    _r("debt_concern", "debt", "AGR dues", "interest", "leverage", "borrowing", conf=0.7),
    _r("management_concern", "restructuring", "CFO exit", "CEO exit", "guidance cut",
       "Q3 NIM", "compression", conf=0.55),
    _r("regulatory_risk", "DoT", "SEBI", "RBI", "regulatory", "scrutiny", "AGR",
       "regulator", conf=0.7),
    _r("innovation_signal", "launch", "demerger", "new product", "specialty", "5G",
       "EV", "Ilumya", conf=0.6),
    _r("macro_risk", "monsoon", "inflation", "recession", "rate hike", conf=0.55),
    _r("sector_tailwind", "tailwind", "pricing discipline", "demand surge", conf=0.6),
    _r("sector_headwind", "headwind", "neutral", "challenging", "outlook revised",
       conf=0.6),
    _r("governance_risk", "pledged", "promoter sale", "audit", "irregularities",
       "scrutiny", conf=0.75),
    _r("supply_chain_risk", "supply", "shortage", "chip", "logistics", conf=0.55),
    _r("competitive_advantage", "moat", "leadership", "ARPU climbs", "premiumisation",
       conf=0.55),
    _r("competitive_threat", "loses share", "competition", "Birla Opus",
       "competitor", conf=0.7),
]


def classify_text(text: str) -> list[SentimentTag]:
    out: list[SentimentTag] = []
    seen: set[str] = set()
    for rule in _RULES:
        for pat in rule.patterns:
            if pat.search(text):
                if rule.label in seen:
                    continue
                seen.add(rule.label)
                out.append(SentimentTag(label=rule.label, confidence=rule.base_confidence))  # type: ignore[arg-type]
                break
    return out


class HeuristicClassifier:
    def classify(self, item: NewsItem) -> list[SentimentTag]:
        text = " ".join(filter(None, [item.title, item.body]))
        return classify_text(text)
