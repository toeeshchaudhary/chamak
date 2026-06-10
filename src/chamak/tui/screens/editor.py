from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

from chamak.core.errors import RuleParseError
from chamak.core.models import Edge, Node, NodeType, Rule
from chamak.graph.mindmap import MindMapGraph
from chamak.rules.compiler import compile_form, compile_text
from chamak.storage.repositories import mindmaps as mm_repo, versions as ver_repo
from chamak.tui.widgets.flowchart import render_flowchart


class _AddRuleModal(ModalScreen[Rule | None]):
    DEFAULT_CSS = """
    _AddRuleModal { align: center middle; }
    #box { background: #1a1a1c; padding: 1 2; border: tall #2a2a2c; width: 78; }
    """

    def __init__(self, node_id: str) -> None:
        super().__init__()
        self.node_id = node_id

    def compose(self) -> ComposeResult:
        with Vertical(id="box"):
            yield Static("[bold]Add a rule[/]", classes="panel-title")
            yield Label("Quick form — pick a thing, an operator, and a number.")
            with Horizontal():
                self.metric_in = Input(placeholder="metric (e.g. roe, debt_to_equity, pe)", id="metric")
                self.op_in = Input(placeholder="< or >", id="op", value="<")
                self.value_in = Input(placeholder="value", id="value")
                yield self.metric_in
                yield self.op_in
                yield self.value_in
            yield Label("[dim]Or write the rule yourself (advanced):[/]")
            self.dsl_in = Input(placeholder="debt_to_equity < 0.5 AND roe > 15")
            yield self.dsl_in
            with Horizontal():
                yield Button("Add", id="add", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        try:
            if self.metric_in.value.strip():
                rule = compile_form(
                    {
                        "metric": self.metric_in.value.strip(),
                        "op": self.op_in.value.strip() or "<",
                        "value": float(self.value_in.value.strip() or 0),
                    },
                    node_id=self.node_id,
                )
            else:
                rule = compile_text(self.dsl_in.value.strip(), node_id=self.node_id)
        except (RuleParseError, ValueError) as e:
            self.notify(f"Couldn't parse that rule: {e}", severity="error")
            return
        self.dismiss(rule)


class EditorScreen(Screen):
    BINDINGS = [
        Binding("s", "save", "Save"),
        Binding("i", "add_rule", "Add rule"),
        Binding("x", "delete_rule", "Delete rule"),
        Binding("h", "toggle_hard", "Make deal-breaker"),
        Binding("plus", "weight_up", "Weight +"),
        Binding("minus", "weight_down", "Weight -"),
        Binding("v", "versions", "Versions"),
        Binding("V", "fullscreen", "Fullscreen view"),
        Binding("n", "add_belief", "New belief"),
        Binding("j", "next_belief", "Next belief"),
        Binding("k", "prev_belief", "Prev belief"),
    ]

    DEFAULT_CSS = """
    EditorScreen { layout: vertical; }
    #title-bar { height: auto; padding: 0 2; }
    #chart-wrap { height: 50%; padding: 0 2; }
    #editor-row { height: 1fr; padding: 0 2; }
    #beliefs-col { width: 35; }
    #rules-col { width: 1fr; padding-left: 2; }
    """

    def __init__(self, mindmap_id: str) -> None:
        super().__init__()
        self.mindmap_id = mindmap_id
        self.graph = MindMapGraph()
        self.dirty = False
        self._selected_belief_id: str | None = None
        self._rule_ids: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="title-bar", classes="title")
        with VerticalScroll(id="chart-wrap"):
            self.chart = Static("[dim]Loading…[/]", id="chart")
            yield self.chart
        with Horizontal(id="editor-row"):
            with Vertical(id="beliefs-col"):
                yield Static("[bold]Beliefs[/]", classes="panel-title")
                self.belief_lv = ListView()
                yield self.belief_lv
                yield Static(
                    "[dim]j/k to move · [bold]n[/] new belief[/]",
                    classes="dim",
                )
            with Vertical(id="rules-col"):
                yield Static("[bold]Rules on selected belief[/]", classes="panel-title")
                self.rules_table = DataTable(cursor_type="row")
                self.rules_table.add_columns("In plain English", "Weight", "Hard?")
                yield self.rules_table
                yield Static(
                    "[dim][bold]i[/] add rule  · [bold]x[/] delete  · [bold]+/-[/] weight  ·"
                    " [bold]h[/] toggle deal-breaker  · [bold]s[/] save  · [bold]V[/] fullscreen[/]",
                    classes="dim",
                )
        yield Footer()

    def on_mount(self) -> None:
        snap = ver_repo.load_latest(self.app.conn, self.mindmap_id)  # type: ignore[attr-defined]
        title_widget = self.query_one("#title-bar", Static)
        if snap is None:
            mm = mm_repo.get(self.app.conn, self.mindmap_id)  # type: ignore[attr-defined]
            title_widget.update(
                f"[bold]{mm.name if mm else '?'}[/]  [dim](no saved version yet — press s to save)[/]"
            )
            return
        self.graph = MindMapGraph.from_snapshot(snap)
        title_widget.update(
            f"[bold]{snap.mindmap.name}[/]  ·  [dim]{snap.mindmap.archetype}  ·  v{snap.mindmap.current_version}[/]"
        )
        self._refresh_beliefs()
        if self.graph.nodes:
            beliefs = self._belief_nodes()
            if beliefs:
                self._selected_belief_id = beliefs[0].id
        self._refresh_chart()
        self._refresh_rules()

    # --- belief management -------------------------------------------------

    def _belief_nodes(self) -> list[Node]:
        incoming = {e.target for e in self.graph.edges}
        roots = [n for n in self.graph.nodes if n.id not in incoming]
        root_id = roots[0].id if roots else None
        return [
            n for n in self.graph.nodes
            if n.type != NodeType.PORTFOLIO_GOAL and n.id != root_id
        ]

    def _refresh_beliefs(self) -> None:
        # Rebuild the ListView with one row per belief.
        for child in list(self.belief_lv.children):
            child.remove()
        for b in self._belief_nodes():
            n_rules = sum(1 for r in self.graph.rules if r.node_id == b.id)
            label = f"{b.label}  [dim]({n_rules} rule{'s' if n_rules != 1 else ''})[/]"
            self.belief_lv.append(
                ListItem(Static(label), id=f"b-{b.id}")
            )
        # Restore highlight
        if self._selected_belief_id:
            for idx, item in enumerate(list(self.belief_lv.children)):
                if item.id == f"b-{self._selected_belief_id}":
                    self.belief_lv.index = idx
                    break

    def _refresh_rules(self) -> None:
        self.rules_table.clear()
        self._rule_ids = []
        if not self._selected_belief_id:
            return
        from chamak.rules.plain import translate_rule
        rules = [r for r in self.graph.rules if r.node_id == self._selected_belief_id]
        for r in rules:
            try:
                prose = translate_rule(r.ast_json, polarity=r.polarity)
            except Exception:  # noqa: BLE001
                prose = r.text
            self.rules_table.add_row(
                prose,
                f"{r.weight:.1f}",
                "YES" if r.hard else "",
            )
            self._rule_ids.append(r.id)

    def _refresh_chart(self) -> None:
        if not self.graph.nodes:
            self.chart.update("[dim]Empty style — press n to add a belief.[/]")
            return
        mm = mm_repo.get(self.app.conn, self.mindmap_id)  # type: ignore[attr-defined]
        if not mm:
            return
        width = max(100, (self.size.width or 120) - 6)
        self.chart.update(render_flowchart(self.graph.snapshot(mm), max_width=width))

    def _refresh_all(self) -> None:
        self._refresh_beliefs()
        self._refresh_rules()
        self._refresh_chart()

    # --- events ------------------------------------------------------------

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item and event.item.id and event.item.id.startswith("b-"):
            self._selected_belief_id = event.item.id[2:]
            self._refresh_rules()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item and event.item.id and event.item.id.startswith("b-"):
            self._selected_belief_id = event.item.id[2:]
            self._refresh_rules()

    def action_next_belief(self) -> None:
        items = list(self.belief_lv.children)
        if not items:
            return
        cur = self.belief_lv.index or 0
        self.belief_lv.index = min(len(items) - 1, cur + 1)

    def action_prev_belief(self) -> None:
        cur = self.belief_lv.index or 0
        self.belief_lv.index = max(0, cur - 1)

    # --- rule actions ------------------------------------------------------

    def _selected_rule_id(self) -> str | None:
        try:
            return self._rule_ids[self.rules_table.cursor_row]
        except (IndexError, AttributeError):
            return None

    async def action_add_rule(self) -> None:
        if not self._selected_belief_id:
            self.notify("Pick a belief first (j/k).", severity="warning")
            return
        rule = await self.app.push_screen(
            _AddRuleModal(self._selected_belief_id), wait_for_dismiss=True
        )
        if rule:
            self.graph.add_rule(rule)
            self.dirty = True
            self._refresh_all()

    def action_delete_rule(self) -> None:
        rid = self._selected_rule_id()
        if rid:
            self.graph.remove_rule(rid)
            self.dirty = True
            self._refresh_all()

    def action_toggle_hard(self) -> None:
        rid = self._selected_rule_id()
        if not rid:
            return
        for r in self.graph.rules:
            if r.id == rid:
                r.hard = not r.hard
                self.graph.upsert_rule(r)
                self.dirty = True
                self._refresh_all()
                return

    def _bump_weight(self, delta: float) -> None:
        rid = self._selected_rule_id()
        if not rid:
            return
        for r in self.graph.rules:
            if r.id == rid:
                r.weight = max(0.1, round(r.weight + delta, 2))
                self.graph.upsert_rule(r)
                self.dirty = True
                self._refresh_all()
                return

    def action_weight_up(self) -> None: self._bump_weight(+0.1)
    def action_weight_down(self) -> None: self._bump_weight(-0.1)

    def action_add_belief(self) -> None:
        n = Node(type=NodeType.BELIEF, label="New belief", description="")
        self.graph.add_node(n)
        # Link to the root if there is one
        incoming = {e.target for e in self.graph.edges}
        roots = [x for x in self.graph.nodes if x.id not in incoming and x.id != n.id]
        if roots:
            self.graph.add_edge(Edge(source=roots[0].id, target=n.id, kind="supports"))
        self._selected_belief_id = n.id
        self.dirty = True
        self._refresh_all()

    def action_versions(self) -> None:
        from chamak.tui.screens.history import HistoryScreen
        self.app.push_screen(HistoryScreen(mindmap_id=self.mindmap_id))

    def action_fullscreen(self) -> None:
        from chamak.tui.screens.flowchart_view import FlowchartViewScreen
        self.app.push_screen(FlowchartViewScreen(mindmap_id=self.mindmap_id))

    def action_save(self) -> None:
        conn = self.app.conn  # type: ignore[attr-defined]
        mm = mm_repo.get(conn, self.mindmap_id)
        if not mm:
            return
        snap = self.graph.snapshot(mm)
        version = ver_repo.save_snapshot(conn, snap, message="edit")
        mm_repo.replace_graph(conn, mm.id, self.graph.nodes, self.graph.edges, self.graph.rules)
        mm.current_version = version.version
        mm_repo.update_meta(conn, mm)
        self.dirty = False
        self.notify(f"Saved as v{version.version}.", severity="information")
        self._refresh_all()
