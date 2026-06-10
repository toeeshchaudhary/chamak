from __future__ import annotations

from typing import Iterator

import networkx as nx

from chamak.core.errors import GraphError
from chamak.core.models import Edge, MindMap, MindMapSnapshot, Node, Rule


class MindMapGraph:
    """In-memory mind map representation.

    Wraps a networkx.DiGraph for traversal, but the source-of-truth for
    serialization is the (nodes, edges, rules) lists. Snapshot round-trip:

        snap = graph.snapshot(mindmap)
        graph2 = MindMapGraph.from_snapshot(snap)
    """

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, Edge] = {}
        self._rules: dict[str, Rule] = {}
        self._g = nx.DiGraph()

    # --- mutation ---

    def add_node(self, n: Node) -> None:
        if n.id in self._nodes:
            raise GraphError(f"duplicate node id {n.id}")
        self._nodes[n.id] = n
        self._g.add_node(n.id, type=n.type.value, label=n.label)

    def upsert_node(self, n: Node) -> None:
        self._nodes[n.id] = n
        self._g.add_node(n.id, type=n.type.value, label=n.label)

    def remove_node(self, node_id: str) -> None:
        if node_id not in self._nodes:
            return
        del self._nodes[node_id]
        if self._g.has_node(node_id):
            self._g.remove_node(node_id)
        # cascade edges and rules
        for eid in [eid for eid, e in self._edges.items() if e.source == node_id or e.target == node_id]:
            del self._edges[eid]
        for rid in [rid for rid, r in self._rules.items() if r.node_id == node_id]:
            del self._rules[rid]

    def add_edge(self, e: Edge) -> None:
        if e.source not in self._nodes or e.target not in self._nodes:
            raise GraphError(f"edge {e.id} references missing node")
        self._edges[e.id] = e
        self._g.add_edge(e.source, e.target, key=e.id, kind=e.kind, weight=e.weight)

    def remove_edge(self, edge_id: str) -> None:
        e = self._edges.pop(edge_id, None)
        if e and self._g.has_edge(e.source, e.target):
            self._g.remove_edge(e.source, e.target)

    def add_rule(self, r: Rule) -> None:
        if r.node_id not in self._nodes:
            raise GraphError(f"rule {r.id} references missing node {r.node_id}")
        self._rules[r.id] = r

    def upsert_rule(self, r: Rule) -> None:
        self._rules[r.id] = r

    def remove_rule(self, rule_id: str) -> None:
        self._rules.pop(rule_id, None)

    # --- read ---

    @property
    def nodes(self) -> list[Node]:
        return list(self._nodes.values())

    @property
    def edges(self) -> list[Edge]:
        return list(self._edges.values())

    @property
    def rules(self) -> list[Rule]:
        return list(self._rules.values())

    def get_node(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def rules_for_node(self, node_id: str) -> list[Rule]:
        return [r for r in self._rules.values() if r.node_id == node_id]

    def hard_rules(self) -> Iterator[Rule]:
        return (r for r in self._rules.values() if r.hard)

    def soft_rules(self) -> Iterator[Rule]:
        return (r for r in self._rules.values() if not r.hard)

    # --- (de)serialization ---

    def snapshot(self, mm: MindMap) -> MindMapSnapshot:
        return MindMapSnapshot(
            mindmap=mm,
            nodes=self.nodes,
            edges=self.edges,
            rules=self.rules,
        )

    @classmethod
    def from_snapshot(cls, snap: MindMapSnapshot) -> "MindMapGraph":
        g = cls()
        for n in snap.nodes:
            g.add_node(n)
        for e in snap.edges:
            # ignore edges that reference missing nodes (defensive vs hand edits)
            if e.source in g._nodes and e.target in g._nodes:
                g.add_edge(e)
        for r in snap.rules:
            if r.node_id in g._nodes:
                g.add_rule(r)
        return g
