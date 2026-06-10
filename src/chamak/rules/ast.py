"""Closed AST for the rule language.

Nodes are plain dicts so they serialize trivially. Use the constructor
helpers below — never build dicts by hand from the parser.

Schema:
    {"t": "lit",  "v": <float | str>}
    {"t": "ref",  "k": "<metric_key>"}
    {"t": "cmp",  "op": "<lt|le|gt|ge|eq|ne>", "l": <node>, "r": <node>}
    {"t": "btw",  "x": <node>, "lo": <node>, "hi": <node>}
    {"t": "and",  "xs": [<node>, ...]}
    {"t": "or",   "xs": [<node>, ...]}
    {"t": "not",  "x": <node>}
"""

from __future__ import annotations

from typing import Literal

CmpOp = Literal["lt", "le", "gt", "ge", "eq", "ne"]


def lit(v: float | str) -> dict:
    return {"t": "lit", "v": v}


def ref(key: str) -> dict:
    return {"t": "ref", "k": key.lower()}


def cmp(op: CmpOp, l: dict, r: dict) -> dict:
    return {"t": "cmp", "op": op, "l": l, "r": r}


def between(x: dict, lo: dict, hi: dict) -> dict:
    return {"t": "btw", "x": x, "lo": lo, "hi": hi}


def and_(*xs: dict) -> dict:
    return {"t": "and", "xs": list(xs)}


def or_(*xs: dict) -> dict:
    return {"t": "or", "xs": list(xs)}


def not_(x: dict) -> dict:
    return {"t": "not", "x": x}


def metric_refs(node: dict) -> set[str]:
    """Collect every metric key referenced in an AST."""
    out: set[str] = set()

    def walk(n: dict) -> None:
        t = n.get("t")
        if t == "ref":
            out.add(n["k"])
        elif t == "cmp":
            walk(n["l"])
            walk(n["r"])
        elif t == "btw":
            walk(n["x"])
            walk(n["lo"])
            walk(n["hi"])
        elif t in ("and", "or"):
            for c in n["xs"]:
                walk(c)
        elif t == "not":
            walk(n["x"])

    walk(node)
    return out


def primary_threshold(node: dict) -> tuple[str | None, str | None, float | None]:
    """Best-effort extraction of (metric_key, op, threshold) for a simple cmp.

    Used by the editor to show a 'threshold' input on simple rules.
    Returns (None, None, None) if the rule is compound."""
    if node.get("t") != "cmp":
        return (None, None, None)
    l, r = node["l"], node["r"]
    if l.get("t") == "ref" and r.get("t") == "lit" and isinstance(r["v"], (int, float)):
        return (l["k"], node["op"], float(r["v"]))
    if r.get("t") == "ref" and l.get("t") == "lit" and isinstance(l["v"], (int, float)):
        # flip: 0.5 > debt_to_equity  ==  debt_to_equity < 0.5
        flip = {"lt": "gt", "le": "ge", "gt": "lt", "ge": "le", "eq": "eq", "ne": "ne"}
        return (r["k"], flip[node["op"]], float(l["v"]))
    return (None, None, None)
