from __future__ import annotations

import pytest

from chamak.core.errors import RuleParseError
from chamak.rules.compiler import compile_form, compile_text
from chamak.rules.evaluator import evaluate
from chamak.rules.parser import parse, to_text


def test_simple_cmp():
    rule = compile_text("debt_to_equity < 0.5", node_id="n1")
    assert rule.ast_json["t"] == "cmp"
    assert rule.ast_json["op"] == "lt"


def test_and_or_precedence():
    a = parse("pe < 20 AND roe > 15 OR debt_to_equity < 0.3")
    # OR is at the top, AND nested
    assert a["t"] == "or"
    assert a["xs"][0]["t"] == "and"


def test_between():
    a = parse("pe BETWEEN 5 AND 20")
    assert a["t"] == "btw"


def test_not():
    a = parse("NOT debt_to_equity > 1")
    assert a["t"] == "not"


def test_paren_grouping():
    a = parse("(pe < 20 OR pb < 3) AND revenue_growth > 10")
    assert a["t"] == "and"


def test_unknown_metric_rejected():
    with pytest.raises(RuleParseError):
        compile_text("zzz < 1", node_id="n1")


def test_form_compile():
    r = compile_form({"metric": "roe", "op": ">", "value": 15}, node_id="n1")
    assert r.ast_json == {
        "t": "cmp", "op": "gt",
        "l": {"t": "ref", "k": "roe"},
        "r": {"t": "lit", "v": 15.0},
    }


def test_evaluate_satisfaction_passes():
    rule = compile_text("debt_to_equity < 0.5", node_id="n1")
    r = evaluate(rule.ast_json, {"debt_to_equity": 0.1})
    assert r.value > 0.9


def test_evaluate_satisfaction_fails():
    rule = compile_text("debt_to_equity < 0.5", node_id="n1")
    r = evaluate(rule.ast_json, {"debt_to_equity": 2.0})
    assert r.value < 0.1


def test_evaluate_at_threshold_is_middle():
    rule = compile_text("debt_to_equity < 0.5", node_id="n1")
    r = evaluate(rule.ast_json, {"debt_to_equity": 0.5})
    assert 0.4 < r.value < 0.6


def test_evaluate_missing_metric():
    rule = compile_text("pe < 20", node_id="n1")
    r = evaluate(rule.ast_json, {"roe": 15})
    assert r.missing is True
    assert r.missing_metric == "pe"


def test_to_text_roundtrip():
    src = "pe < 20 AND roe > 15"
    a = parse(src)
    txt = to_text(a)
    assert "<" in txt and ">" in txt and "AND" in txt


def test_or_with_some_missing_picks_max_present():
    rule = compile_text("pe < 20 OR roe > 15", node_id="n1")
    # only roe present, satisfied
    r = evaluate(rule.ast_json, {"roe": 30})
    assert r.value > 0.8


def test_polarity_round_trip_via_form():
    rule = compile_form(
        {"metric": "pe", "op": ">", "value": 40, "polarity": "avoid"}, node_id="n1"
    )
    assert rule.polarity == "avoid"
