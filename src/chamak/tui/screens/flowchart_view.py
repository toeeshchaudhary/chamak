"""Dedicated read-only flowchart view for an investing style."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from chamak.storage.repositories import mindmaps as mm_repo, versions as ver_repo
from chamak.tui.widgets.flowchart import render_flowchart


class FlowchartViewScreen(Screen):
    BINDINGS = [
        Binding("e", "edit", "Edit"),
        Binding("v", "back", "Back"),
    ]

    DEFAULT_CSS = """
    FlowchartViewScreen { background: #0c0c0e; }
    #title { padding: 1 2; }
    #chart-wrap { padding: 0 2 1 2; height: 1fr; }
    #legend { padding: 1 2; color: #707070; }
    """

    def __init__(self, mindmap_id: str) -> None:
        super().__init__()
        self.mindmap_id = mindmap_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="title", classes="title")
        with VerticalScroll(id="chart-wrap"):
            self.chart = Static("", id="chart")
            yield self.chart
        yield Static(
            "[dim]Legend:  ▲ deal-breaker rule   • normal rule   "
            "[/]   [bold]e[/] edit   [bold]v[/]/[bold]Esc[/] back",
            id="legend",
        )
        yield Footer()

    def on_mount(self) -> None:
        conn = self.app.conn  # type: ignore[attr-defined]
        mm = mm_repo.get(conn, self.mindmap_id)
        snap = ver_repo.load_latest(conn, self.mindmap_id)
        if mm:
            self.query_one("#title", Static).update(
                f"[bold]{mm.name}[/]  ·  [dim]{mm.archetype}  ·  v{mm.current_version}[/]"
            )
        if not snap:
            self.chart.update("[dim]No saved version yet.[/]")
            return
        # Make the chart wide enough for everything to fit comfortably.
        width = max(120, self.size.width - 8 or 120)
        self.chart.update(render_flowchart(snap, max_width=width))

    def action_edit(self) -> None:
        from chamak.tui.screens.editor import EditorScreen
        self.app.switch_screen(EditorScreen(mindmap_id=self.mindmap_id))

    def action_back(self) -> None:
        self.app.pop_screen()
