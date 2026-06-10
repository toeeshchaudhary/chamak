"""Translate compiled rules back into plain English.

Used everywhere a rule appears in the UI so investors see prose like
'the company owes less than 0.5× its net worth' instead of
'debt_to_equity < 0.5'.
"""

from __future__ import annotations

from chamak.rules import metrics as metrics_reg


def _fmt_value(value: float, unit: str) -> str:
    """Pretty-print a numeric threshold for use in prose."""
    if value == int(value):
        s = str(int(value))
    else:
        s = f"{value:g}"
    return s


def _translate_cmp(op: str, value: float, spec: metrics_reg.MetricSpec) -> str:
    """Render 'metric OP value' as English."""
    val = _fmt_value(value, spec.unit)
    if op in ("lt", "le"):
        phrase = spec.phrase_low or f"has {spec.plain.lower()} under"
        return f"{phrase} {val}{spec.unit_suffix}"
    if op in ("gt", "ge"):
        phrase = spec.phrase_high or f"has {spec.plain.lower()} of at least"
        return f"{phrase} {val}{spec.unit_suffix}"
    if op == "eq":
        return f"has {spec.plain.lower()} around {val}{spec.unit_suffix}"
    if op == "ne":
        return f"has {spec.plain.lower()} other than {val}{spec.unit_suffix}"
    return f"{spec.label} {op} {val}"


def translate_ast(node: dict, *, lead: str = "the company") -> str:
    """Translate an AST node into prose.

    The `lead` is what we use to start a sentence ("the company", "it",
    "this stock"). Compound nodes are joined naturally with "and"/"or".
    """
    t = node.get("t")

    if t == "cmp":
        # Identify the metric side
        if node["l"].get("t") == "ref" and node["r"].get("t") == "lit":
            spec = metrics_reg.get(node["l"]["k"])
            value = float(node["r"]["v"])
            if spec is None:
                return f"{lead} {node['l']['k']} {node['op']} {value}"
            return f"{lead} {_translate_cmp(node['op'], value, spec)}"
        if node["r"].get("t") == "ref" and node["l"].get("t") == "lit":
            # value OP metric → flip
            spec = metrics_reg.get(node["r"]["k"])
            value = float(node["l"]["v"])
            flip = {"lt": "gt", "le": "ge", "gt": "lt", "ge": "le", "eq": "eq", "ne": "ne"}
            if spec is None:
                return f"{lead} {node['r']['k']} {flip[node['op']]} {value}"
            return f"{lead} {_translate_cmp(flip[node['op']], value, spec)}"
        return "(complex comparison)"

    if t == "btw":
        if node["x"].get("t") == "ref":
            spec = metrics_reg.get(node["x"]["k"])
            lo = float(node["lo"]["v"])
            hi = float(node["hi"]["v"])
            if spec is None:
                return f"{lead} {node['x']['k']} between {lo} and {hi}"
            return (
                f"{lead}'s {spec.plain.lower()} is between {_fmt_value(lo, spec.unit)}"
                f" and {_fmt_value(hi, spec.unit)}{spec.unit_suffix}"
            )
        return "(complex between)"

    if t == "and":
        parts = [translate_ast(c, lead=lead) for c in node["xs"]]
        # Trim repeated leads so it reads naturally
        out = parts[0]
        for p in parts[1:]:
            if p.startswith(lead + " "):
                p = p[len(lead) + 1 :]
            out += f", and {p}"
        return out

    if t == "or":
        parts = [translate_ast(c, lead=lead) for c in node["xs"]]
        out = parts[0]
        for p in parts[1:]:
            if p.startswith(lead + " "):
                p = p[len(lead) + 1 :]
            out += f", or {p}"
        return out

    if t == "not":
        return "it is NOT the case that " + translate_ast(node["x"], lead=lead)

    return "(unknown rule)"


def translate_rule(rule_ast: dict, polarity: str = "prefer") -> str:
    """Top-level prose for a rule. Capitalises and applies polarity."""
    sentence = translate_ast(rule_ast)
    sentence = sentence[0].upper() + sentence[1:]
    if polarity == "avoid":
        sentence = "Avoid stocks where " + sentence[0].lower() + sentence[1:]
    return sentence
