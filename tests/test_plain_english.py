from __future__ import annotations

from chamak.explain.verdict import for_score
from chamak.rules.parser import parse
from chamak.rules.plain import translate_ast, translate_rule


def test_simple_less_than_translates():
    ast = parse("debt_to_equity < 0.5")
    s = translate_rule(ast)
    assert "owes" in s.lower() or "debt" in s.lower()
    assert "0.5" in s


def test_simple_greater_than_translates():
    ast = parse("roe > 15")
    s = translate_rule(ast)
    assert "earns" in s.lower() or "roe" in s.lower()
    assert "15" in s


def test_and_translates_to_natural_clause():
    ast = parse("debt_to_equity < 0.5 AND roe > 15")
    s = translate_rule(ast)
    assert ", and " in s


def test_or_translates_to_natural_clause():
    ast = parse("pe < 20 OR pb < 3")
    s = translate_rule(ast)
    assert ", or " in s


def test_avoid_polarity_prepends_avoid():
    ast = parse("pe > 40")
    s = translate_rule(ast, polarity="avoid")
    assert s.lower().startswith("avoid")


def test_verdict_strong_for_high_score():
    v = for_score(0.85)
    assert v.tier == "strong"
    assert v.label == "STRONG FIT"


def test_verdict_poor_for_low_score():
    v = for_score(0.2)
    assert v.tier == "poor"


def test_verdict_hard_failure_overrides_high_score():
    v = for_score(0.9, hard_failures=True)
    assert v.tier == "poor"
    assert "deal-breaker" in v.headline.lower() or "rule" in v.headline.lower()
