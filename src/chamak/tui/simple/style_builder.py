"""Convert simple-quiz answers into a real MindMap snapshot."""

from __future__ import annotations

from chamak.core.models import Edge, MindMap, MindMapSnapshot, MindMapType, Node, NodeType
from chamak.graph.mindmap import MindMapGraph
from chamak.rules.compiler import compile_form
from chamak.tui.simple.quiz_data import Choice, QUESTIONS


def archetype_for(answers: dict[str, str]) -> str:
    vibe = answers.get("vibe", "")
    like = answers.get("like", "")
    price = answers.get("price", "")
    if like == "income":
        return "Income Lover"
    if vibe == "cautious" and price == "cheap":
        return "Cautious Value"
    if like == "fast" or vibe == "bold":
        return "Growth Seeker"
    if price == "quality" or like == "steady":
        return "Quality Compounder"
    return "Balanced Investor"


def name_for(archetype: str) -> str:
    return f"My Style — {archetype}"


def build_snapshot(answers: dict[str, str]) -> MindMapSnapshot:
    """Turn quiz answers into a saveable starter style."""
    archetype = archetype_for(answers)
    mm = MindMap(
        name=name_for(archetype),
        type=MindMapType.HYBRID,
        archetype=archetype,
        description=f"Built from your quiz answers. Profile: {archetype}.",
    )
    g = MindMapGraph()
    root = Node(type=NodeType.PORTFOLIO_GOAL, label=archetype, description=mm.description)
    g.add_node(root)

    chosen: list[Choice] = []
    for q in QUESTIONS:
        ans = answers.get(q.id)
        if ans is None:
            continue
        for c in q.choices:
            if c.key == ans:
                chosen.append(c)
                break

    for c in chosen:
        belief = Node(
            type=NodeType.BELIEF,
            label=c.belief_label,
            description=c.belief_description,
            weight=1.0,
            confidence=0.9,
            payload={"quiz_choice": c.key, "icon": c.icon},
        )
        g.add_node(belief)
        g.add_edge(Edge(source=root.id, target=belief.id, kind="supports"))
        for r in c.rules:
            rule = compile_form(
                {
                    "metric": r.metric, "op": r.op, "value": r.value,
                    "weight": r.weight, "polarity": r.polarity,
                    "confidence": 0.9, "hard": False,
                },
                node_id=belief.id,
            )
            g.add_rule(rule)

    return g.snapshot(mm)
