from __future__ import annotations

from dataclasses import dataclass, field

from chamak.core.models import Edge, MindMapSnapshot, Node, Rule


@dataclass
class GraphDiff:
    added_nodes: list[Node] = field(default_factory=list)
    removed_nodes: list[Node] = field(default_factory=list)
    modified_nodes: list[tuple[Node, Node]] = field(default_factory=list)  # (old, new)

    added_edges: list[Edge] = field(default_factory=list)
    removed_edges: list[Edge] = field(default_factory=list)

    added_rules: list[Rule] = field(default_factory=list)
    removed_rules: list[Rule] = field(default_factory=list)
    modified_rules: list[tuple[Rule, Rule]] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not any(
            [
                self.added_nodes,
                self.removed_nodes,
                self.modified_nodes,
                self.added_edges,
                self.removed_edges,
                self.added_rules,
                self.removed_rules,
                self.modified_rules,
            ]
        )

    def summary(self) -> str:
        return (
            f"nodes +{len(self.added_nodes)}/-{len(self.removed_nodes)}/~{len(self.modified_nodes)}, "
            f"edges +{len(self.added_edges)}/-{len(self.removed_edges)}, "
            f"rules +{len(self.added_rules)}/-{len(self.removed_rules)}/~{len(self.modified_rules)}"
        )


def _node_changed(a: Node, b: Node) -> bool:
    return (
        a.type != b.type
        or a.label != b.label
        or a.description != b.description
        or a.weight != b.weight
        or a.confidence != b.confidence
        or a.payload != b.payload
    )


def _rule_changed(a: Rule, b: Rule) -> bool:
    return (
        a.text != b.text
        or a.ast_json != b.ast_json
        or a.hard != b.hard
        or a.weight != b.weight
        or a.confidence != b.confidence
        or a.polarity != b.polarity
        or a.node_id != b.node_id
    )


def diff(old: MindMapSnapshot, new: MindMapSnapshot) -> GraphDiff:
    d = GraphDiff()
    old_n = {n.id: n for n in old.nodes}
    new_n = {n.id: n for n in new.nodes}
    for nid, n in new_n.items():
        if nid not in old_n:
            d.added_nodes.append(n)
        elif _node_changed(old_n[nid], n):
            d.modified_nodes.append((old_n[nid], n))
    for nid, n in old_n.items():
        if nid not in new_n:
            d.removed_nodes.append(n)

    old_e = {e.id: e for e in old.edges}
    new_e = {e.id: e for e in new.edges}
    for eid, e in new_e.items():
        if eid not in old_e:
            d.added_edges.append(e)
    for eid, e in old_e.items():
        if eid not in new_e:
            d.removed_edges.append(e)

    old_r = {r.id: r for r in old.rules}
    new_r = {r.id: r for r in new.rules}
    for rid, r in new_r.items():
        if rid not in old_r:
            d.added_rules.append(r)
        elif _rule_changed(old_r[rid], r):
            d.modified_rules.append((old_r[rid], r))
    for rid, r in old_r.items():
        if rid not in new_r:
            d.removed_rules.append(r)
    return d
