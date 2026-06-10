"""High-level rule construction.

Two entry points:

- compile_text(text):   parse a DSL string into a Rule (you supply node_id).
- compile_form(form):   build from a structured form-input dict (used by the
                        rule editor in the TUI). This bypasses the parser.
"""

from __future__ import annotations

from typing import Any

from chamak.core.errors import RuleParseError
from chamak.core.models import Rule
from chamak.rules import ast, metrics as metrics_reg
from chamak.rules.parser import parse


def _validate(node: dict) -> None:
    """Validate that every metric ref is in the registry."""
    t = node["t"]
    if t == "ref":
        if metrics_reg.get(node["k"]) is None:
            raise RuleParseError(f"unknown metric {node['k']!r}")
    elif t == "cmp":
        _validate(node["l"])
        _validate(node["r"])
    elif t == "btw":
        _validate(node["x"])
        _validate(node["lo"])
        _validate(node["hi"])
    elif t in ("and", "or"):
        for c in node["xs"]:
            _validate(c)
    elif t == "not":
        _validate(node["x"])
    elif t == "lit":
        return
    else:
        raise RuleParseError(f"unknown AST type {t}")


def compile_text(
    text: str,
    *,
    node_id: str,
    hard: bool = False,
    weight: float = 1.0,
    confidence: float = 1.0,
    polarity: str = "prefer",
) -> Rule:
    ast_node = parse(text)
    _validate(ast_node)
    return Rule(
        node_id=node_id,
        text=text,
        ast_json=ast_node,
        hard=hard,
        weight=weight,
        confidence=confidence,
        polarity=polarity,  # type: ignore[arg-type]
    )


def compile_form(form: dict[str, Any], *, node_id: str) -> Rule:
    """Compile a single-comparison rule from the structured rule editor.

    Form schema:
        {"metric": "debt_to_equity", "op": "<", "value": 0.5,
         "hard": false, "weight": 1.0, "confidence": 1.0, "polarity": "prefer"}
    """
    metric = form["metric"]
    if metrics_reg.get(metric) is None:
        raise RuleParseError(f"unknown metric {metric!r}")
    op = form.get("op", "<")
    op_map = {"<": "lt", "<=": "le", ">": "gt", ">=": "ge", "=": "eq", "==": "eq", "!=": "ne"}
    if op not in op_map:
        raise RuleParseError(f"bad op {op!r}")
    value = float(form["value"])
    text = f"{metric} {op} {value}"
    node = ast.cmp(op_map[op], ast.ref(metric), ast.lit(value))
    return Rule(
        node_id=node_id,
        text=text,
        ast_json=node,
        hard=bool(form.get("hard", False)),
        weight=float(form.get("weight", 1.0)),
        confidence=float(form.get("confidence", 1.0)),
        polarity=form.get("polarity", "prefer"),
    )
