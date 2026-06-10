"""Pre-built demo mind maps so users can jump straight in.

Each blueprint becomes a real saved mind map with a real version snapshot.
The structure mirrors what the interview engine would produce.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from chamak.core.models import Edge, MindMap, MindMapSnapshot, MindMapType, Node, NodeType
from chamak.graph.mindmap import MindMapGraph
from chamak.rules.compiler import compile_form


@dataclass
class _BeliefSpec:
    label: str
    description: str
    weight: float = 1.0
    confidence: float = 0.9
    rules: list[dict] = field(default_factory=list)


@dataclass
class _MindMapBlueprint:
    name: str
    archetype: str
    description: str
    beliefs: list[_BeliefSpec]


VALUE = _MindMapBlueprint(
    name="Value Investor",
    archetype="Value Investor",
    description="Buy at a discount; demand a margin of safety; reject leverage.",
    beliefs=[
        _BeliefSpec("Margin of safety on price", "P/E reflects the price; P/B reflects the floor.", 1.4, 0.9, [
            {"metric": "pe", "op": "<", "value": 20, "weight": 1.4, "polarity": "prefer"},
            {"metric": "pb", "op": "<", "value": 3.0, "weight": 1.0, "polarity": "prefer"},
        ]),
        _BeliefSpec("Avoid leverage", "Debt to equity is the canary in the coal mine.", 1.5, 0.95, [
            {"metric": "debt_to_equity", "op": "<", "value": 0.5, "weight": 1.5, "polarity": "prefer", "hard": False},
        ]),
        _BeliefSpec("Earn on capital", "ROE / ROCE filter out cigar butts that won't earn out.", 1.2, 0.85, [
            {"metric": "roe", "op": ">", "value": 12, "weight": 1.0, "polarity": "prefer"},
            {"metric": "roce", "op": ">", "value": 12, "weight": 1.0, "polarity": "prefer"},
        ]),
        _BeliefSpec("Cash flow is real", "FCF separates earnings from accounting fiction.", 1.0, 0.85, [
            {"metric": "fcf_yield", "op": ">", "value": 2.0, "weight": 1.0, "polarity": "prefer"},
        ]),
        _BeliefSpec("Long-term operator", "Older companies have survived recessions.", 0.7, 0.7, [
            {"metric": "years_since_listing", "op": ">", "value": 10, "weight": 0.5, "polarity": "prefer"},
            {"metric": "pledged_pct", "op": "<", "value": 5, "weight": 1.0, "polarity": "prefer"},
        ]),
    ],
)


QUALITY = _MindMapBlueprint(
    name="Quality Compounder",
    archetype="Quality Compounder",
    description="Pay up for moats, return on capital, and reinvestment runway.",
    beliefs=[
        _BeliefSpec("Reinvestment economics", "High ROCE compounds capital.", 1.6, 0.95, [
            {"metric": "roce", "op": ">", "value": 20, "weight": 1.6, "polarity": "prefer"},
            {"metric": "roe", "op": ">", "value": 18, "weight": 1.2, "polarity": "prefer"},
        ]),
        _BeliefSpec("Pricing power", "Margins reveal moats.", 1.3, 0.9, [
            {"metric": "operating_margin", "op": ">", "value": 18, "weight": 1.2, "polarity": "prefer"},
            {"metric": "gross_margin", "op": ">", "value": 35, "weight": 0.8, "polarity": "prefer"},
        ]),
        _BeliefSpec("Top-line tailwind", "Compounding needs revenue, not just margins.", 1.1, 0.85, [
            {"metric": "revenue_cagr_3y", "op": ">", "value": 10, "weight": 1.1, "polarity": "prefer"},
        ]),
        _BeliefSpec("Conservative balance sheet", "A compounder shouldn't blow up.", 1.2, 0.9, [
            {"metric": "debt_to_equity", "op": "<", "value": 0.6, "weight": 1.2, "polarity": "prefer"},
            {"metric": "interest_coverage", "op": ">", "value": 8, "weight": 0.8, "polarity": "prefer"},
        ]),
        _BeliefSpec("Skin in the game", "Promoter holding without pledge = aligned.", 0.9, 0.8, [
            {"metric": "promoter_holding", "op": ">", "value": 40, "weight": 0.8, "polarity": "prefer"},
            {"metric": "pledged_pct", "op": "<", "value": 5, "weight": 1.2, "polarity": "prefer", "hard": False},
        ]),
    ],
)


DIVIDEND = _MindMapBlueprint(
    name="Dividend Income",
    archetype="Income / Dividend Investor",
    description="Cash in hand. Yield, payout, and a balance sheet that can sustain it.",
    beliefs=[
        _BeliefSpec("Above-average yield", "Yield is the whole point.", 1.7, 0.95, [
            {"metric": "dividend_yield", "op": ">", "value": 2.5, "weight": 1.7, "polarity": "prefer"},
        ]),
        _BeliefSpec("Cash to sustain dividends", "FCF must fund the dividend.", 1.3, 0.9, [
            {"metric": "fcf_yield", "op": ">", "value": 3.0, "weight": 1.3, "polarity": "prefer"},
        ]),
        _BeliefSpec("Not overpriced", "Yield trap protection.", 1.0, 0.85, [
            {"metric": "pe", "op": "<", "value": 25, "weight": 1.0, "polarity": "prefer"},
        ]),
        _BeliefSpec("Manageable leverage", "Levered names cut dividends first.", 1.1, 0.85, [
            {"metric": "debt_to_equity", "op": "<", "value": 1.0, "weight": 1.1, "polarity": "prefer"},
        ]),
        _BeliefSpec("Established business", "Capital return implies maturity.", 0.7, 0.8, [
            {"metric": "years_since_listing", "op": ">", "value": 10, "weight": 0.7, "polarity": "prefer"},
        ]),
    ],
)


BLUEPRINTS: list[_MindMapBlueprint] = [VALUE, QUALITY, DIVIDEND]


def build_snapshot(bp: _MindMapBlueprint) -> MindMapSnapshot:
    mm = MindMap(name=bp.name, type=MindMapType.HYBRID, archetype=bp.archetype,
                 description=bp.description)
    g = MindMapGraph()
    root = Node(type=NodeType.PORTFOLIO_GOAL, label=bp.archetype, description=bp.description)
    g.add_node(root)
    for belief in bp.beliefs:
        b = Node(
            type=NodeType.BELIEF, label=belief.label, description=belief.description,
            weight=belief.weight, confidence=belief.confidence,
        )
        g.add_node(b)
        g.add_edge(Edge(source=root.id, target=b.id, kind="supports"))
        for r in belief.rules:
            rule = compile_form(r, node_id=b.id)
            rule.hard = r.get("hard", False)
            g.add_rule(rule)
    return g.snapshot(mm)
