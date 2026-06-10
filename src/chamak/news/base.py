"""News + sentiment protocols.

Full ingestion pipeline (RSS, dedup, embed, multi-label classify) is
deferred. Stubs let the recommendation engine carry a 'news_modifier'
hook without forcing an implementation today."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol

SentimentLabel = Literal[
    "bullish",
    "bearish",
    "growth_signal",
    "debt_concern",
    "management_concern",
    "regulatory_risk",
    "innovation_signal",
    "macro_risk",
    "sector_tailwind",
    "sector_headwind",
    "governance_risk",
    "supply_chain_risk",
    "competitive_advantage",
    "competitive_threat",
]


@dataclass
class SentimentTag:
    label: SentimentLabel
    confidence: float


@dataclass
class NewsItem:
    id: str
    title: str
    url: str
    source: str
    published_at: datetime | None
    tickers: list[str] = field(default_factory=list)
    sectors: list[str] = field(default_factory=list)
    sentiment: list[SentimentTag] = field(default_factory=list)
    body: str = ""


class NewsProvider(Protocol):
    name: str

    def fetch(self, since: datetime | None = None) -> list[NewsItem]: ...


class SentimentClassifier(Protocol):
    def classify(self, item: NewsItem) -> list[SentimentTag]: ...
