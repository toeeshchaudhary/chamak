"""Render a MindMap snapshot as an actual ASCII flowchart.

Layout is hierarchical: goal at top, beliefs branching out beneath, and
each belief's rules listed in plain English directly under its box. Lines
connect parent to children with real box-drawing characters.

Example output (compressed for the docstring):

                          ╭─────────────────────╮
                          │   Value Investor    │
                          ╰──────────┬──────────╯
       ┌─────────────────────────────┼─────────────────────────────┐
       │                             │                             │
  ╭────┴────╮                  ╭─────┴─────╮                ╭──────┴──────╮
  │ Low Debt│                  │  Margin   │                │  Earn on    │
  │         │                  │ of Safety │                │   Capital   │
  ╰─────────╯                  ╰───────────╯                ╰─────────────╯
  • Owes less than            • Priced under                • Earns at
    0.5× net worth              20× earnings                  least 12% on
                              • Priced under                  shareholder
                                3× book value                 equity
"""

from __future__ import annotations

import re
import textwrap

from chamak.core.models import MindMapSnapshot
from chamak.rules.plain import translate_rule


# Colors used in flowchart rendering
COLOR_ROOT = "#88c0d0"
COLOR_BELIEF = "#e0e0e0"
COLOR_RULE_DEFAULT = "#a0a0a0"
COLOR_RULE_MATCH = "#98c379"      # green for matched rules
COLOR_RULE_FAIL = "#e06c75"       # red for failed rules
COLOR_RULE_MISSING = "#5a5a5a"    # very dim for missing-data
COLOR_RULE_HARD = "#e5c07b"       # amber for hard rules
COLOR_EDGE = "#5e81ac"


def render_flowchart(
    snap: MindMapSnapshot,
    *,
    rule_status: dict[str, str] | None = None,  # rule_id -> "match"|"fail"|"missing"
    max_width: int = 120,
) -> str:
    """Build the flowchart as a Rich-markup string."""
    rule_status = rule_status or {}

    if not snap.nodes:
        return ("[dim]Your style is empty.[/]\n"
                "[dim]Add a belief with [bold]n[/]; add a rule with [bold]i[/].[/]")

    nodes_by_id = {n.id: n for n in snap.nodes}
    incoming = {e.target for e in snap.edges}
    roots = [n for n in snap.nodes if n.id not in incoming]
    if not roots:
        roots = [snap.nodes[0]]
    root = roots[0]

    # Direct belief-children of the root
    children_ids = [e.target for e in snap.edges if e.source == root.id]
    beliefs = [nodes_by_id[cid] for cid in children_ids if cid in nodes_by_id]

    # If no beliefs, just show the root box.
    if not beliefs:
        return _just_root(root.label)

    # Rules per belief
    rules_by_node: dict[str, list] = {}
    for r in snap.rules:
        rules_by_node.setdefault(r.node_id, []).append(r)

    n = len(beliefs)
    # Each column is just wide enough to fit both the box and the longest rule
    raw_col_width = max(18, min(38, max_width // n - 2))
    col_width = raw_col_width

    columns = [
        _build_column(belief, rules_by_node.get(belief.id, []), col_width, rule_status)
        for belief in beliefs
    ]

    # Pad columns vertically to same height
    h = max(len(c) for c in columns)
    for c in columns:
        while len(c) < h:
            c.append(_blank(col_width))

    # Stitch columns side-by-side, separated by a 2-space gap
    body_lines = []
    for row in range(h):
        body_lines.append("  ".join(c[row] for c in columns))

    body_width = col_width * n + 2 * (n - 1)

    # Column centers in the body coordinate system
    col_centers = [i * (col_width + 2) + col_width // 2 for i in range(n)]
    c_min, c_max = col_centers[0], col_centers[-1]
    root_center = (c_min + c_max) // 2

    # Root box, centered over the whole branch
    root_label_lines = _wrap(root.label, max(20, min(40, body_width // 2)))
    root_box_width = max(34, max(len(l) for l in root_label_lines) + 6)
    root_lines = _box(root_label_lines, root_box_width, color=COLOR_ROOT)
    root_offset = max(0, root_center - root_box_width // 2)
    rooted = [(" " * root_offset) + l for l in root_lines]

    # Connectors between root and beliefs
    connectors = _render_connectors(body_width, root_center, col_centers, n)

    return "\n".join(rooted + connectors + body_lines)


# --- helpers ---------------------------------------------------------------

def _build_column(
    belief, rules, width: int, rule_status: dict[str, str]
) -> list[str]:
    label_lines = _wrap(belief.label, width - 4)
    lines = _box(label_lines, width, color=COLOR_BELIEF)
    if not rules:
        lines.append(_pad_to(f"  [dim]• (no rules yet)[/]", width))
        return lines
    for rule in rules:
        try:
            prose = translate_rule(rule.ast_json, polarity=rule.polarity)
        except Exception:  # noqa: BLE001
            prose = rule.text
        status = rule_status.get(rule.id, "default")
        if status == "match":
            color, marker = COLOR_RULE_MATCH, "✓"
        elif status == "fail":
            color, marker = COLOR_RULE_FAIL, "✗"
        elif status == "missing":
            color, marker = COLOR_RULE_MISSING, "?"
        else:
            color = COLOR_RULE_HARD if rule.hard else COLOR_RULE_DEFAULT
            marker = "▲" if rule.hard else "•"
        # Wrap prose under the column
        wrapped = textwrap.wrap(prose, width=max(8, width - 4))
        if not wrapped:
            wrapped = [prose]
        # First line starts with marker
        first = f"  [{color}]{marker} {wrapped[0]}[/]"
        lines.append(_pad_to(first, width))
        for w in wrapped[1:]:
            line = f"    [{color}]{w}[/]"
            lines.append(_pad_to(line, width))
    return lines


def _render_connectors(
    body_width: int, root_center: int, col_centers: list[int], n: int
) -> list[str]:
    # Row 1: single │ under root
    row1 = list(" " * body_width)
    if 0 <= root_center < body_width:
        row1[root_center] = "│"

    if n == 1:
        # Just two vertical bars
        row2 = list(" " * body_width)
        if 0 <= col_centers[0] < body_width:
            row2[col_centers[0]] = "│"
        return [
            f"[{COLOR_EDGE}]" + "".join(row1) + "[/]",
            f"[{COLOR_EDGE}]" + "".join(row2) + "[/]",
        ]

    # Row 2: horizontal branch from c_min to c_max
    c_min, c_max = col_centers[0], col_centers[-1]
    branch = list(" " * body_width)
    for x in range(c_min, c_max + 1):
        branch[x] = "─"
    branch[c_min] = "┌"
    branch[c_max] = "┐"
    for cx in col_centers[1:-1]:
        branch[cx] = "┬"
    # Where root's drop meets the branch
    if c_min < root_center < c_max:
        if branch[root_center] == "─":
            branch[root_center] = "┴"
        else:
            branch[root_center] = "┼"

    # Row 3: │ under each child centre
    row3 = list(" " * body_width)
    for cx in col_centers:
        row3[cx] = "│"

    return [
        f"[{COLOR_EDGE}]" + "".join(row1) + "[/]",
        f"[{COLOR_EDGE}]" + "".join(branch) + "[/]",
        f"[{COLOR_EDGE}]" + "".join(row3) + "[/]",
    ]


def _just_root(label: str) -> str:
    lines = _wrap(label, 30)
    w = max(34, max(len(l) for l in lines) + 6)
    return "\n".join(_box(lines, w, color=COLOR_ROOT))


def _wrap(s: str, width: int) -> list[str]:
    return textwrap.wrap(s, width=max(4, width)) or [s]


def _box(label_lines: list[str], width: int, *, color: str) -> list[str]:
    inner = width - 4
    top = f"[{color}]╭{'─' * (width - 2)}╮[/]"
    bot = f"[{color}]╰{'─' * (width - 2)}╯[/]"
    body = []
    for label in label_lines:
        centered = label[:inner].center(inner)
        body.append(f"[{color}]│[/] {centered} [{color}]│[/]")
    return [top, *body, bot]


def _blank(width: int) -> str:
    return " " * width


_MARKUP = re.compile(r"\[/?[^\]]*\]")


def _visible_len(s: str) -> int:
    return len(_MARKUP.sub("", s))


def _pad_to(s: str, width: int) -> str:
    diff = width - _visible_len(s)
    if diff > 0:
        return s + " " * diff
    return s
