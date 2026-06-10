from __future__ import annotations

from chamak.core.models import Edge, MindMap, MindMapSnapshot, Node, NodeType
from chamak.graph.diff import diff
from chamak.graph.mindmap import MindMapGraph


def _snap(name: str, *nodes, edges=None, rules=None):
    return MindMapSnapshot(
        mindmap=MindMap(name=name),
        nodes=list(nodes),
        edges=list(edges or []),
        rules=list(rules or []),
    )


def test_diff_added_and_removed_nodes():
    a = Node(type=NodeType.BELIEF, label="A")
    b = Node(type=NodeType.BELIEF, label="B")
    c = Node(type=NodeType.BELIEF, label="C")
    old = _snap("m", a, b)
    new = _snap("m", a, c)
    d = diff(old, new)
    assert [n.label for n in d.added_nodes] == ["C"]
    assert [n.label for n in d.removed_nodes] == ["B"]


def test_diff_modified_node():
    a = Node(type=NodeType.BELIEF, label="A")
    old = _snap("m", a)
    a2 = a.model_copy(update={"weight": 2.0})
    new = _snap("m", a2)
    d = diff(old, new)
    assert d.modified_nodes


def test_round_trip_graph():
    a = Node(type=NodeType.BELIEF, label="A")
    b = Node(type=NodeType.METRIC, label="B")
    e = Edge(source=a.id, target=b.id)
    snap = _snap("m", a, b, edges=[e])
    g = MindMapGraph.from_snapshot(snap)
    assert {n.id for n in g.nodes} == {a.id, b.id}
    assert len(g.edges) == 1
