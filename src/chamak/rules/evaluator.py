"""Soft-threshold evaluator for compiled rules.

Evaluator returns a satisfaction value in [0, 1]:

- Boolean composers (and/or/not/between) combine using soft fuzzy logic:
    and := min, or := max, not := 1 - x.
- Leaf comparisons evaluate to a sigmoid around the threshold whose
  steepness comes from the metric's MetricSpec.k. This means that a
  stock that just misses the threshold scores ~0.4-0.5 instead of 0,
  while one that comfortably clears it approaches 1.

If a referenced metric is missing from the snapshot, the rule returns
EvalResult(missing=True, value=0.0) and the scoring engine treats this
specially (it neither counts as fail nor as pass).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from chamak.core.errors import RuleEvalError
from chamak.rules import metrics as metrics_reg


@dataclass
class EvalResult:
    value: float                          # 0..1 satisfaction
    missing: bool = False                 # True if a needed metric was absent
    missing_metric: str | None = None


def _sigmoid(x: float, k: float = 4.0) -> float:
    if x > 50:
        return 1.0
    if x < -50:
        return 0.0
    return 1.0 / (1.0 + math.exp(-k * x))


def _soft_lt(value: float, threshold: float, k: float) -> float:
    # high satisfaction when value < threshold by a meaningful margin
    if threshold == 0:
        norm = -value
    else:
        norm = (threshold - value) / max(abs(threshold), 1e-6)
    return _sigmoid(norm, k)


def _soft_gt(value: float, threshold: float, k: float) -> float:
    if threshold == 0:
        norm = value
    else:
        norm = (value - threshold) / max(abs(threshold), 1e-6)
    return _sigmoid(norm, k)


def _eval_cmp(op: str, value: float, threshold: float, k: float) -> float:
    if op in ("lt", "le"):
        return _soft_lt(value, threshold, k)
    if op in ("gt", "ge"):
        return _soft_gt(value, threshold, k)
    if op == "eq":
        # peaked sigmoid around threshold
        return max(0.0, 1.0 - min(1.0, abs(value - threshold) / max(abs(threshold), 1e-6)))
    if op == "ne":
        return 1.0 - _eval_cmp("eq", value, threshold, k)
    raise RuleEvalError(f"unknown op {op}")


def _resolve_ref(node: dict, ctx: dict[str, float]) -> tuple[float | None, str | None]:
    key = node["k"]
    if key in ctx:
        return ctx[key], None
    return None, key


def _eval_value(node: dict, ctx: dict[str, float]) -> tuple[float | None, str | None]:
    t = node["t"]
    if t == "lit":
        v = node["v"]
        if isinstance(v, (int, float)):
            return float(v), None
        raise RuleEvalError(f"non-numeric literal {v!r}")
    if t == "ref":
        return _resolve_ref(node, ctx)
    raise RuleEvalError(f"value-position node was {t}")


def evaluate(ast_node: dict, ctx: dict[str, float]) -> EvalResult:
    t = ast_node["t"]

    if t == "cmp":
        l_val, l_miss = _eval_value(ast_node["l"], ctx)
        r_val, r_miss = _eval_value(ast_node["r"], ctx)
        if l_miss is not None:
            return EvalResult(0.0, missing=True, missing_metric=l_miss)
        if r_miss is not None:
            return EvalResult(0.0, missing=True, missing_metric=r_miss)
        # decide which side is the metric for steepness lookup
        metric_key = None
        if ast_node["l"].get("t") == "ref":
            metric_key = ast_node["l"]["k"]
        elif ast_node["r"].get("t") == "ref":
            metric_key = ast_node["r"]["k"]
        spec = metrics_reg.get(metric_key) if metric_key else None
        k = spec.k if spec else 4.0
        # canonicalize: metric on left, literal on right
        if ast_node["l"].get("t") == "ref":
            sat = _eval_cmp(ast_node["op"], l_val, r_val, k)
        else:
            # value-position swap; invert op
            flip = {"lt": "gt", "le": "ge", "gt": "lt", "ge": "le", "eq": "eq", "ne": "ne"}
            sat = _eval_cmp(flip[ast_node["op"]], r_val, l_val, k)
        return EvalResult(sat)

    if t == "btw":
        x_val, x_miss = _eval_value(ast_node["x"], ctx)
        lo_val, _ = _eval_value(ast_node["lo"], ctx)
        hi_val, _ = _eval_value(ast_node["hi"], ctx)
        if x_miss is not None:
            return EvalResult(0.0, missing=True, missing_metric=x_miss)
        spec = metrics_reg.get(ast_node["x"]["k"]) if ast_node["x"].get("t") == "ref" else None
        k = spec.k if spec else 4.0
        lo_sat = _soft_gt(x_val, lo_val, k)
        hi_sat = _soft_lt(x_val, hi_val, k)
        return EvalResult(min(lo_sat, hi_sat))

    if t == "and":
        results = [evaluate(c, ctx) for c in ast_node["xs"]]
        miss = next((r for r in results if r.missing), None)
        if miss is not None:
            return miss
        return EvalResult(min(r.value for r in results))

    if t == "or":
        results = [evaluate(c, ctx) for c in ast_node["xs"]]
        non_missing = [r for r in results if not r.missing]
        if not non_missing:
            return results[0]
        return EvalResult(max(r.value for r in non_missing))

    if t == "not":
        inner = evaluate(ast_node["x"], ctx)
        if inner.missing:
            return inner
        return EvalResult(1.0 - inner.value)

    raise RuleEvalError(f"unknown node type {t}")
