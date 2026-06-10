"""Drives the YAML interview and produces a starter MindMap."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from chamak.core.errors import InterviewError
from chamak.core.models import (
    Edge,
    MindMap,
    MindMapSnapshot,
    MindMapType,
    Node,
    NodeType,
)
from chamak.graph.mindmap import MindMapGraph
from chamak.interview.archetype import classify
from chamak.interview.assistant import InterviewAssistant, NullAssistant
from chamak.rules.compiler import compile_form


_OP_MAP_VALID = {"<", "<=", ">", ">=", "=", "==", "!="}


def _load_script() -> dict:
    # files() handles both source layout and installed wheel.
    res = files("chamak.interview").joinpath("script.yaml")
    text = res.read_text(encoding="utf-8") if hasattr(res, "read_text") else Path(str(res)).read_text()
    return yaml.safe_load(text)


class InterviewEngine:
    def __init__(self, assistant: InterviewAssistant | None = None) -> None:
        self.script = _load_script()
        self.questions: list[dict] = list(self.script["questions"])
        self.answers: dict[str, Any] = {}
        self.idx = 0
        self.assistant = assistant or NullAssistant()

    # --- iteration ---

    def current(self) -> dict | None:
        return self.questions[self.idx] if self.idx < len(self.questions) else None

    def answer(self, value: Any) -> None:
        q = self.current()
        if q is None:
            raise InterviewError("interview already complete")
        self.answers[q["id"]] = value
        self.idx += 1

    def skip(self) -> None:
        self.idx += 1

    def done(self) -> bool:
        return self.idx >= len(self.questions)

    def progress(self) -> tuple[int, int]:
        return self.idx, len(self.questions)

    # --- mind map construction ---

    def _belief_matches(self, belief: dict, value: Any) -> bool:
        if "when" in belief:
            target = belief["when"]
            if isinstance(value, list):
                return target in value
            return value == target
        if "when_min" in belief:
            try:
                return float(value) >= float(belief["when_min"])
            except (TypeError, ValueError):
                return False
        return False

    def build_snapshot(self, name: str) -> MindMapSnapshot:
        archetype = classify(self.answers)
        mm = MindMap(
            name=name,
            type=MindMapType.HYBRID,
            archetype=archetype,
            description=f"Starter mind map from interview ({archetype}).",
        )
        g = MindMapGraph()
        # root philosophy node
        root = Node(type=NodeType.PORTFOLIO_GOAL, label=archetype, description=mm.description, weight=1.0)
        g.add_node(root)

        for q in self.questions:
            ans = self.answers.get(q["id"])
            if ans is None:
                continue
            for belief in q.get("beliefs") or []:
                if not self._belief_matches(belief, ans):
                    continue
                bnode = Node(
                    type=NodeType.BELIEF,
                    label=belief["label"],
                    description=belief.get("description", ""),
                    weight=1.0,
                    confidence=0.85,
                    payload={"question": q["id"], "answer": ans},
                )
                g.add_node(bnode)
                g.add_edge(Edge(source=root.id, target=bnode.id, kind="supports"))
                for r in belief.get("rules") or []:
                    if r.get("op") not in _OP_MAP_VALID:
                        continue
                    try:
                        rule = compile_form(
                            {
                                "metric": r["metric"],
                                "op": r["op"],
                                "value": r["value"],
                                "hard": r.get("hard", False),
                                "weight": r.get("weight", 1.0),
                                "confidence": r.get("confidence", 0.85),
                                "polarity": r.get("polarity", "prefer"),
                            },
                            node_id=bnode.id,
                        )
                    except Exception:
                        continue
                    g.add_rule(rule)

        # narrative-derived candidates
        text_blobs = " ".join(
            str(self.answers.get(k, "")) for k in ("philosophy", "bad_experiences")
        )
        if text_blobs.strip():
            narr = Node(
                type=NodeType.BELIEF,
                label="Narrative",
                description=text_blobs[:280],
                weight=0.8,
                confidence=0.5,
            )
            g.add_node(narr)
            g.add_edge(Edge(source=root.id, target=narr.id, kind="supports"))
            try:
                cands = self.assistant.candidates_from_narrative(text_blobs)
            except Exception:
                cands = []
            for c in cands:
                try:
                    rule = compile_form(
                        {
                            "metric": c.metric,
                            "op": c.op,
                            "value": c.value,
                            "polarity": c.polarity,
                            "weight": 0.6,
                            "confidence": c.confidence,
                            "hard": False,
                        },
                        node_id=narr.id,
                    )
                except Exception:
                    continue
                g.add_rule(rule)

        return g.snapshot(mm)
