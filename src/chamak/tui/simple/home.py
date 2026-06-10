"""Simple-mode home — big friendly buttons, no jargon."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, ListItem, ListView, Static

from chamak.storage.repositories import mindmaps as mm_repo


_ACTIONS = [
    ("picks",
     "Show me stocks I'd like",
     "Stocks ranked by how well they fit your style. One card at a time."),
    ("vibe",
     "Play Vibe Check",
     "We show you two stocks. You pick one. Repeat 5 times. We tell you what we learned."),
    ("style",
     "See what I learned about you",
     "Your investing style — visualised as a flowchart you can read."),
    ("redo",
     "Take the quiz again",
     "Three questions. Builds a fresh style. Old ones are kept."),
    ("advanced",
     "Switch to Advanced mode",
     "Full editor, scanner, portfolios, news, version history. For power users."),
]


class SimpleHomeScreen(Screen):
    BINDINGS = [
        Binding("1", "pick_0", "Picks"),
        Binding("2", "pick_1", "Vibe Check"),
        Binding("3", "pick_2", "Style"),
        Binding("4", "pick_3", "Redo Quiz"),
        Binding("5", "pick_4", "Advanced"),
    ]

    DEFAULT_CSS = """
    SimpleHomeScreen { background: #0a0a0d; }
    #wrap { padding: 1 4; }
    #hi { color: #ffffff; text-style: bold; padding: 1 0 0 0; }
    #archetype { color: #88c0d0; padding: 0 0 1 0; }
    #stats { color: #707070; padding-bottom: 1; }
    #menu { height: auto; }
    ListItem {
        background: #14141a;
        border: round #2a2a2c;
        padding: 1 2;
        margin: 0 0 1 0;
    }
    ListItem.--highlight {
        background: #1a1a24;
        border: round #5e81ac;
    }
    """

    def __init__(self, mindmap_id: str) -> None:
        super().__init__()
        self.mindmap_id = mindmap_id

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="wrap"):
            yield Static("", id="hi")
            yield Static("", id="archetype")
            yield Static("", id="stats")
            self.lv = ListView(
                *[
                    ListItem(
                        Static(f"[bold]{i + 1}.  {title}[/]\n   [dim]{blurb}[/]"),
                        id=f"act-{key}",
                    )
                    for i, (key, title, blurb) in enumerate(_ACTIONS)
                ],
                id="menu",
            )
            yield self.lv
        yield Footer()

    def on_mount(self) -> None:
        conn = self.app.conn  # type: ignore[attr-defined]
        mm = mm_repo.get(conn, self.mindmap_id)
        if mm:
            self.query_one("#hi", Static).update(
                f"Welcome back. Your style is saved."
            )
            self.query_one("#archetype", Static).update(
                f"Profile: [bold #88c0d0]{mm.archetype}[/]   ·   [dim]{mm.name}[/]"
            )
        # Count active styles for context
        all_mms = mm_repo.list_all(conn)
        if len(all_mms) > 1:
            self.query_one("#stats", Static).update(
                f"You have {len(all_mms)} styles saved."
            )

    def action_pick_0(self) -> None: self._pick("picks")
    def action_pick_1(self) -> None: self._pick("vibe")
    def action_pick_2(self) -> None: self._pick("style")
    def action_pick_3(self) -> None: self._pick("redo")
    def action_pick_4(self) -> None: self._pick("advanced")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        key = (event.item.id or "").removeprefix("act-")
        self._pick(key)

    def _pick(self, key: str) -> None:
        if key == "picks":
            from chamak.tui.simple.stock_card import SimpleStockCardScreen
            self.app.push_screen(SimpleStockCardScreen(mindmap_id=self.mindmap_id))
        elif key == "vibe":
            from chamak.tui.simple.vibe_check import VibeCheckScreen
            self.app.push_screen(VibeCheckScreen(mindmap_id=self.mindmap_id))
        elif key == "style":
            from chamak.tui.screens.flowchart_view import FlowchartViewScreen
            self.app.push_screen(FlowchartViewScreen(mindmap_id=self.mindmap_id))
        elif key == "redo":
            from chamak.tui.simple.quiz import SimpleQuizScreen
            self.app.push_screen(SimpleQuizScreen())
        elif key == "advanced":
            from chamak.config import set_mode
            set_mode("advanced")
            self.notify("Switched to Advanced mode. Press M anytime to return.",
                        severity="information")
            from chamak.tui.screens.dashboard import DashboardScreen
            self.app.switch_screen(DashboardScreen())
