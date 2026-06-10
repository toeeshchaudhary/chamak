from __future__ import annotations

from chamak.core.models import MindMap, MindMapSnapshot, Node, NodeType, StockFundamentals
from chamak.rules.compiler import compile_form, compile_text
from chamak.scoring.engine import score


def _mm(rules: list) -> MindMapSnapshot:
    mm = MindMap(name="T")
    n = Node(type=NodeType.BELIEF, label="b")
    nodes = [n]
    for r in rules:
        r.node_id = n.id
    return MindMapSnapshot(mindmap=mm, nodes=nodes, edges=[], rules=rules)


def test_empty_mindmap_returns_zero():
    snap = MindMapSnapshot(mindmap=MindMap(name="T"), nodes=[], edges=[], rules=[])
    f = StockFundamentals(ticker="X", metrics={"pe": 10})
    b = score(snap, f)
    assert b.score == 0.0
    assert "no rules" in " ".join(b.notes).lower()


def test_all_rules_satisfied():
    rules = [
        compile_text("debt_to_equity < 0.5", node_id="x"),
        compile_text("roe > 15", node_id="x"),
    ]
    snap = _mm(rules)
    f = StockFundamentals(ticker="X", metrics={"debt_to_equity": 0.1, "roe": 30})
    b = score(snap, f)
    assert b.score > 0.85


def test_hard_rule_gates_score_to_zero():
    rules = [
        compile_form({"metric": "debt_to_equity", "op": "<", "value": 0.5, "hard": True}, node_id="x"),
        compile_form({"metric": "roe", "op": ">", "value": 15}, node_id="x"),
    ]
    snap = _mm(rules)
    f = StockFundamentals(ticker="X", metrics={"debt_to_equity": 2.0, "roe": 30})
    b = score(snap, f)
    assert b.score == 0.0
    assert b.hard_failures
    # at least one gated contribution
    assert any(c.gated for c in b.contributions)


def test_missing_metric_does_not_count():
    rules = [
        compile_text("pe < 20", node_id="x"),
        compile_text("roe > 15", node_id="x"),
    ]
    snap = _mm(rules)
    f = StockFundamentals(ticker="X", metrics={"roe": 30})  # pe missing
    b = score(snap, f)
    assert "pe" in b.missing
    assert b.score > 0.8  # only roe contributed and it passes


def test_avoid_polarity_inverts():
    rule = compile_form({"metric": "pe", "op": ">", "value": 40, "polarity": "avoid"}, node_id="x")
    snap = _mm([rule])
    # pe of 10 -> rule satisfaction (pe > 40) is low -> avoid polarity makes contribution high
    f = StockFundamentals(ticker="X", metrics={"pe": 10})
    b = score(snap, f)
    assert b.score > 0.85
