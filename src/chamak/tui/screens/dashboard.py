from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, ListItem, ListView, Static

from chamak.config import openrouter_key, paths
from chamak.storage.repositories import mindmaps as mm_repo, portfolios as port_repo, stocks as stocks_repo
from chamak.tui.widgets.banner import Banner


_ITEMS = [
    ("L", "View my investing styles",   "library"),
    ("I", "Build a new style (interview)", "interview"),
    ("R", "See stocks that match my style", "recs"),
    ("S", "Scan a different universe",  "scanner"),
    ("P", "Check my portfolio",         "portfolio"),
    ("N", "Read news, by sentiment",    "news"),
    ("D", "Demo / autopilot tour",      "demo"),
    ("M", "Settings",                   "settings"),
    ("?", "Help & keyboard reference",  "help"),
]


class DashboardScreen(Screen):
    DEFAULT_CSS = """
    DashboardScreen { layout: vertical; }
    #dash { padding: 1 3; }
    #header-row { height: auto; }
    #banner-col { width: 60%; }
    #stats-col { width: 1fr; padding-left: 2; }
    #menu { width: 1fr; }
    .stat-line { padding: 0 0 0 0; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="dash"):
            with Horizontal(id="header-row"):
                with Vertical(id="banner-col"):
                    yield Banner()
                with Vertical(id="stats-col", classes="panel"):
                    yield Static("[bold]At a glance[/]", classes="panel-title")
                    yield Static(self._stats(), id="stats")
            yield Static("[bold]Where to go next[/]", classes="panel-title")
            yield ListView(
                *[
                    ListItem(
                        Static(f"  [kbd]{k}[/]   {label}"),
                        id=tag,
                    )
                    for k, label, tag in _ITEMS
                ],
                id="menu",
            )
            yield Static(
                "  [dim]j/k navigate · Enter open · [bold]?[/] help · "
                "[bold]:[/] palette · [bold]/[/] search[/]",
                id="kbd-hint",
            )
        yield Footer()

    def _stats(self) -> str:
        conn = self.app.conn  # type: ignore[attr-defined]
        n_mm = len(mm_repo.list_all(conn))
        n_arc = len(mm_repo.list_all(conn, include_archived=True)) - n_mm
        n_pf = len(port_repo.list_all(conn))
        n_st = len(stocks_repo.list_stocks(conn))
        llm = "[ok]enabled[/]" if openrouter_key() else "[dim]disabled[/]"
        return (
            f"styles      {n_mm:>3}  [dim]active[/]   {n_arc:>2}  [dim]archived[/]\n"
            f"portfolios  {n_pf:>3}\n"
            f"stocks      {n_st:>3}  [dim]cached[/]\n"
            f"LLM helper  {llm}\n"
            f"data        [dim]{paths().db}[/]"
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._open(event.item.id)

    def _open(self, tag: str | None) -> None:
        from chamak.tui.screens.help import HelpScreen
        from chamak.tui.screens.interview import InterviewScreen
        from chamak.tui.screens.library import LibraryScreen
        from chamak.tui.screens.news_center import NewsScreen
        from chamak.tui.screens.portfolio import PortfolioScreen
        from chamak.tui.screens.recommendations import RecommendationsScreen
        from chamak.tui.screens.scanner import ScannerScreen
        from chamak.tui.screens.settings import SettingsScreen
        from chamak.tui.screens.demo_pilot import DemoPilotLauncherScreen

        target = {
            "interview": lambda: InterviewScreen(name="My Mind Map"),
            "library": LibraryScreen,
            "recs": RecommendationsScreen,
            "scanner": ScannerScreen,
            "portfolio": PortfolioScreen,
            "news": NewsScreen,
            "settings": SettingsScreen,
            "demo": DemoPilotLauncherScreen,
            "help": HelpScreen,
        }.get(tag or "")
        if target:
            self.app.push_screen(target())
