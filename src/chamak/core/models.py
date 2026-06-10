from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from chamak.core.ids import new_id


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NodeType(str, Enum):
    BELIEF = "belief"
    METRIC = "metric"
    SECTOR = "sector"
    RISK = "risk"
    VALUATION = "valuation"
    GROWTH = "growth"
    INDUSTRY = "industry"
    BUSINESS_QUALITY = "business_quality"
    PORTFOLIO_GOAL = "portfolio_goal"
    MACRO_THEME = "macro_theme"
    NEWS_THEME = "news_theme"
    SENTIMENT_THEME = "sentiment_theme"
    RULE = "rule"
    METRIC_THRESHOLD = "metric_threshold"


EdgeKind = Literal[
    "supports", "contradicts", "requires", "strengthens", "weakens", "depends_on"
]


class MindMapType(str, Enum):
    RULE = "rule"
    NARRATIVE = "narrative"
    HYBRID = "hybrid"


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    type: NodeType
    label: str
    description: str = ""
    weight: float = 1.0
    confidence: float = 1.0
    payload: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    source: str
    target: str
    kind: EdgeKind = "supports"
    weight: float = 1.0


class Rule(BaseModel):
    """A compiled, evaluable rule. The `ast_json` is the canonical representation;
    `text` is the user-facing surface form. Bound to the belief node that birthed it."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    node_id: str
    text: str
    ast_json: dict[str, Any]
    hard: bool = False
    weight: float = 1.0
    confidence: float = 1.0
    polarity: Literal["prefer", "avoid"] = "prefer"


class MindMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    name: str
    type: MindMapType = MindMapType.HYBRID
    archetype: str = ""
    description: str = ""
    archived: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    current_version: int = 0


class MindMapSnapshot(BaseModel):
    """Full serialized graph at a point in time. Stored per version."""

    model_config = ConfigDict(extra="forbid")

    mindmap: MindMap
    nodes: list[Node]
    edges: list[Edge]
    rules: list[Rule]


class MindMapVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    mindmap_id: str
    version: int
    message: str = ""
    snapshot: MindMapSnapshot
    created_at: datetime = Field(default_factory=utcnow)


class StockFundamentals(BaseModel):
    """A point-in-time snapshot of metrics for one stock."""

    model_config = ConfigDict(extra="allow")

    ticker: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    metrics: dict[str, float] = Field(default_factory=dict)
    as_of: datetime = Field(default_factory=utcnow)


class Stock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str
    name: str = ""
    exchange: Literal["NSE", "BSE"] = "NSE"
    sector: str = ""
    industry: str = ""


class RuleContribution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    rule_text: str
    node_id: str
    satisfaction: float  # 0..1
    weight: float
    confidence: float
    hard: bool
    gated: bool = False  # True iff a hard rule failed and forced score to 0
    missing_metric: str | None = None
    contribution: float  # weighted contribution to numerator


class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticker: str
    mindmap_id: str
    score: float  # 0..1 compatibility
    confidence: float  # 0..1
    contributions: list[RuleContribution]
    hard_failures: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    mindmap_id: str
    mindmap_version: int
    ticker: str
    score: float
    confidence: float
    breakdown: ScoreBreakdown
    created_at: datetime = Field(default_factory=utcnow)


class Portfolio(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    name: str
    mindmap_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class Holding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=new_id)
    portfolio_id: str
    ticker: str
    quantity: float
    avg_cost: float = 0.0
