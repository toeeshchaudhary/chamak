from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, ListItem, ListView, Static


_COMMANDS = [
    ("dashboard",      "Open Dashboard",              "go_dashboard"),
    ("library",        "Open Mind Map Library",       "go_library"),
    ("interview",      "Start interview",             "go_interview"),
    ("recs",           "Recommendation Center",       "go_recs"),
    ("scanner",        "Market Scanner",              "go_scanner"),
    ("portfolio",      "Portfolios",                  "go_portfolio"),
    ("news",           "News Intelligence Center",    "go_news"),
    ("settings",       "Settings",                    "go_settings"),
    ("help",           "Help",                        "help"),
    ("quit",           "Quit",                        "quit"),
]


class PaletteModal(ModalScreen[None]):
    DEFAULT_CSS = """
    PaletteModal { align: center middle; }
    #box { background: #1a1a1c; padding: 1; width: 60; height: auto; border: tall #2a2a2c; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="box"):
            yield Static("[bold]Command palette[/]", classes="panel-title")
            self.search_input = Input(placeholder="type a command…")
            yield self.search_input
            self.lv = ListView(
                *[
                    ListItem(Static(f"{key:12s}  [dim]{label}[/]"), id=f"cmd-{key}")
                    for key, label, _ in _COMMANDS
                ]
            )
            yield self.lv

    def on_input_changed(self, event: Input.Changed) -> None:
        q = event.value.lower()
        for item in list(self.lv.children):
            visible = q in (item.id or "")
            item.display = visible

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        key = (event.item.id or "").removeprefix("cmd-")
        match = next((c for c in _COMMANDS if c[0] == key), None)
        if not match:
            self.dismiss()
            return
        action = match[2]
        self.dismiss()
        self.app.action_help() if action == "help" else self.app.run_action(action)


def open_palette(app) -> None:
    app.push_screen(PaletteModal())
