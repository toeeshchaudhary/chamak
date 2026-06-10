from __future__ import annotations

from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from chamak.core.models import MindMapSnapshot, Node


class MindMapTree(Tree[str]):
    """Indented tree of belief/rule nodes rooted at portfolio_goal nodes."""

    def __init__(self) -> None:
        super().__init__("Mind Map")
        self.show_root = False
        self.guide_depth = 2

    def populate(self, snap: MindMapSnapshot) -> None:
        self.clear()
        self.root.expand()
        nodes_by_id: dict[str, Node] = {n.id: n for n in snap.nodes}
        children: dict[str, list[str]] = {}
        parents: dict[str, str] = {}
        for e in snap.edges:
            children.setdefault(e.source, []).append(e.target)
            parents[e.target] = e.source

        roots = [n for n in snap.nodes if n.id not in parents]
        if not roots and snap.nodes:
            roots = [snap.nodes[0]]

        rule_count_by_node: dict[str, int] = {}
        for r in snap.rules:
            rule_count_by_node[r.node_id] = rule_count_by_node.get(r.node_id, 0) + 1

        def add(node: Node, parent: TreeNode) -> None:
            rules_n = rule_count_by_node.get(node.id, 0)
            label = f"[bold]{node.label}[/]  [dim]{node.type.value}[/]"
            if rules_n:
                label += f"  [dim]({rules_n} rule{'s' if rules_n != 1 else ''})[/]"
            tn = parent.add(label, data=node.id, expand=True)
            for cid in children.get(node.id, []):
                child = nodes_by_id.get(cid)
                if child:
                    add(child, tn)

        for r in roots:
            add(r, self.root)
