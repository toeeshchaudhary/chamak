"""First-run onboarding — written for a regular investor, not an engineer."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, ListItem, ListView, Static

from chamak.tui.widgets.banner import Banner


_EXPLAINER = (
    "Chamak isn't a stock screener and it doesn't predict prices.\n"
    "\n"
    "It learns [bold]how you[/] decide what makes a good investment — your\n"
    "rules of thumb, what you avoid, what you care about — and then\n"
    "judges every stock through [italic]your[/] lens.\n"
    "\n"
    "Each set of rules is called an [bold]Investing Style[/]. You can have\n"
    "more than one (say, a careful one for retirement and a riskier\n"
    "one for play money), edit them anytime, and Chamak will show you\n"
    "which stocks match — and exactly why."
)


_OPTIONS = [
    ("demo",
     "[bold #98c379]Try it with sample data[/]   [dim](recommended)[/]",
     "Loads 30 Indian stocks and 3 ready-made styles "
     "(Cautious / Quality / Dividend). Best way to see how Chamak works."),
    ("interview",
     "[bold #88c0d0]Build my own style — 9 quick questions[/]",
     "Plain-English questions. We turn your answers into your first style."),
    ("skip",
     "[dim]I'll explore on my own[/]",
     "Drops you into an empty dashboard. You can come back here later."),
]


class WelcomeScreen(Screen):
    BINDINGS = [
        Binding("1", "pick_demo", "Demo"),
        Binding("2", "pick_interview", "Interview"),
        Binding("3", "pick_skip", "Skip"),
    ]

    DEFAULT_CSS = """
    WelcomeScreen { background: #0c0c0e; }
    #wrap { padding: 1 4; height: 1fr; }
    #explainer { padding: 1 0; color: #c0c0c0; }
    #options { padding: 1 0 0 0; }
    #tagline { color: #707070; padding: 0 0 1 0; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="wrap"):
            yield Banner()
            with Center():
                yield Static(_EXPLAINER, id="explainer", classes="panel")
            with Center():
                yield Static("How would you like to start?", id="tagline")
            with Center():
                self.lv = ListView(
                    *[
                        ListItem(
                            Static(f"{title}\n   [dim]{desc}[/]"),
                            id=f"opt-{key}",
                        )
                        for key, title, desc in _OPTIONS
                    ],
                    id="options",
                )
                yield self.lv
            with Center():
                yield Static(
                    "[dim]↑/↓ or j/k to move · Enter to choose · 1/2/3 quick-pick[/]"
                )
        yield Footer()

    def action_pick_demo(self) -> None: self._pick("demo")
    def action_pick_interview(self) -> None: self._pick("interview")
    def action_pick_skip(self) -> None: self._pick("skip")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        key = (event.item.id or "").removeprefix("opt-")
        self._pick(key)

    def _pick(self, key: str) -> None:
        if key == "interview":
            from chamak.tui.screens.interview import InterviewScreen
            self.app.switch_screen(InterviewScreen(name="My Style"))
            return
        if key == "demo":
            from chamak.demo.seeder import seed
            rep = seed(self.app.conn)  # type: ignore[attr-defined]
            self.notify(
                f"Loaded {rep.stocks} stocks · {rep.mindmaps} investing styles · "
                f"a sample portfolio · {rep.news} news stories.",
                severity="information",
            )
            from chamak.tui.screens.dashboard import DashboardScreen
            self.app.switch_screen(DashboardScreen())
            return
        from chamak.tui.screens.dashboard import DashboardScreen
        self.app.switch_screen(DashboardScreen())
