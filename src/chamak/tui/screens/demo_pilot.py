"""Demo autopilot: scripted walk through screens with on-screen annotation.

Designed for screen recording. Each "scene" is (screen, dwell_seconds,
caption). The overlay surfaces what's happening so a viewer (or editor)
can follow along without narration.

Controls:
  Space     pause / resume
  →  / l    advance to next scene now
  ←  / h    restart current scene
  q        quit autopilot, drop back to dashboard
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Static

from chamak.demo.seeder import seed
from chamak.storage.repositories import mindmaps as mm_repo

log = logging.getLogger("chamak.tui.demo")


@dataclass
class _Scene:
    label: str
    description: str
    dwell: float
    make_screen: Callable[[str], Screen]  # takes mindmap_id


def _scenes() -> list[_Scene]:
    from chamak.tui.screens.dashboard import DashboardScreen
    from chamak.tui.screens.editor import EditorScreen
    from chamak.tui.screens.history import HistoryScreen
    from chamak.tui.screens.library import LibraryScreen
    from chamak.tui.screens.news_center import NewsScreen
    from chamak.tui.screens.portfolio import PortfolioScreen
    from chamak.tui.screens.recommendations import RecommendationsScreen
    from chamak.tui.screens.scanner import ScannerScreen
    from chamak.tui.screens.stock_detail import StockDetailScreen

    from chamak.tui.screens.flowchart_view import FlowchartViewScreen

    return [
        _Scene(
            "1 · Dashboard",
            "Your investing styles, your portfolios, your cached stocks — all in one place.",
            3.0, lambda _mm: DashboardScreen(),
        ),
        _Scene(
            "2 · Your investing styles",
            "Three ready-made styles: Value Investor, Quality Compounder, Dividend Income.",
            3.5, lambda _mm: LibraryScreen(),
        ),
        _Scene(
            "3 · Style as a flowchart",
            "This is how Chamak sees your thinking — goal at top, beliefs branching out, rules in plain English.",
            6.0, lambda mm: FlowchartViewScreen(mindmap_id=mm),
        ),
        _Scene(
            "4 · Edit a style",
            "Pick a belief, tweak its rules. Every save is a new version you can roll back to.",
            5.0, lambda mm: EditorScreen(mindmap_id=mm),
        ),
        _Scene(
            "5 · Version history",
            "Every save is a snapshot. See exactly what changed; restore any version.",
            3.5, lambda mm: HistoryScreen(mindmap_id=mm),
        ),
        _Scene(
            "6 · Best matches first",
            "Stocks scored by how well they fit your style — STRONG FIT / GOOD FIT / MIXED / POOR.",
            5.0, lambda _mm: RecommendationsScreen(),
        ),
        _Scene(
            "7 · Why this stock fits",
            "The same flowchart, but each rule is colored: green = match, red = doesn't match.",
            6.0, lambda mm: StockDetailScreen(ticker="HDFCBANK", mindmap_id=mm),
        ),
        _Scene(
            "8 · Market scanner",
            "Run a style against any universe of stocks. Same engine, broader sweep.",
            3.5, lambda _mm: ScannerScreen(),
        ),
        _Scene(
            "9 · Portfolio check",
            "Catches contradictions: 'you said low debt but you own these levered names'.",
            5.0, lambda _mm: PortfolioScreen(),
        ),
        _Scene(
            "10 · News with sentiment",
            "Headlines tagged: bullish, bearish, debt-concern, governance-risk, sector-tailwind…",
            4.0, lambda _mm: NewsScreen(),
        ),
        _Scene(
            "11 · Back to dashboard",
            "That's Chamak. Press q to exit autopilot, ? for help, or just play.",
            2.0, lambda _mm: DashboardScreen(),
        ),
    ]


class DemoPilotLauncherScreen(Screen):
    """Splash launcher offering to seed + start the autopilot."""

    BINDINGS = [
        Binding("s", "seed_only", "Seed only"),
        Binding("p", "start", "Start autopilot"),
        Binding("enter", "start", "Start"),
    ]

    DEFAULT_CSS = """
    DemoPilotLauncherScreen Vertical { padding: 2 4; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("[bold]Demo / Autopilot[/]", classes="title")
            yield Static(
                "Loads the demo dataset (3 mind maps, 30 Indian stocks, demo "
                "portfolio, 15 news items) and walks through every screen with "
                "captions. Built for screen recording.\n\n"
                "  [kbd]p[/] · [bold]Start autopilot[/]  (seeds first if needed)\n"
                "  [kbd]s[/] · Seed demo data only, no autopilot\n"
                "  [kbd]Esc[/] · Back\n\n"
                "[dim]During the demo: space to pause, → for next scene, ← to "
                "restart current scene, q to quit autopilot.[/]",
                classes="panel",
            )
        yield Footer()

    def action_seed_only(self) -> None:
        rep = seed(self.app.conn)  # type: ignore[attr-defined]
        self.notify(
            f"Seeded {rep.stocks} stocks · {rep.mindmaps} mind maps · "
            f"{rep.portfolios} portfolio · {rep.news} news items.",
            severity="information",
        )

    def action_start(self) -> None:
        rep = seed(self.app.conn)  # type: ignore[attr-defined]
        if rep.stocks or rep.mindmaps:
            self.notify("Demo data ready.", severity="information")
        # Find the Value Investor mind map to anchor screens that need an id.
        mm_id = None
        for m in mm_repo.list_all(self.app.conn):  # type: ignore[attr-defined]
            if m.name == "Value Investor":
                mm_id = m.id
                break
        if not mm_id:
            mms = mm_repo.list_all(self.app.conn)  # type: ignore[attr-defined]
            if not mms:
                self.notify("No mind maps to demo with.", severity="warning")
                return
            mm_id = mms[0].id
        self.app.push_screen(DemoPilotScreen(mindmap_id=mm_id))


class DemoPilotScreen(Screen):
    """The autopilot itself. Switches the *child* screen on a timer, while
    keeping a caption overlay docked at the top.

    Implementation note: rather than fighting Textual's screen stack to keep
    an overlay on top of multiple screens, we push the target screens onto
    the app and manage our overlay as a notification banner via `notify`
    plus a persistent docked Static on each scene transition.
    """

    BINDINGS = [
        Binding("space", "toggle_pause", "Pause/Resume"),
        Binding("right", "next_now", "Next"),
        Binding("l", "next_now", "Next"),
        Binding("left", "restart_scene", "Restart scene"),
        Binding("h", "restart_scene", "Restart scene"),
        Binding("q", "stop", "Stop autopilot", priority=True),
    ]

    DEFAULT_CSS = """
    DemoPilotScreen { background: #0c0c0e; }
    #demo-frame { padding: 2 4; }
    #demo-step { color: #88c0d0; text-style: bold; }
    #demo-desc { color: #d0d0d0; }
    #demo-progress { color: #707070; }
    #demo-help { color: #5a5a5a; padding: 1 0 0 0; }
    """

    def __init__(self, mindmap_id: str) -> None:
        super().__init__()
        self.mindmap_id = mindmap_id
        self.scenes = _scenes()
        self.idx = -1
        self.paused = False
        self._timer = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="demo-frame"):
            yield Static("[bold]Chamak · Demo Autopilot[/]", classes="title")
            yield Static("starting…", id="demo-step")
            yield Static("", id="demo-desc")
            yield Static("", id="demo-progress")
            yield Static(
                "[kbd]space[/] pause/resume    [kbd]→[/] next    "
                "[kbd]←[/] restart current scene    [kbd]q[/] quit autopilot",
                id="demo-help",
            )
        yield Footer()

    def on_mount(self) -> None:
        self._advance()

    def _show_scene(self, scene: _Scene) -> None:
        self.query_one("#demo-step", Static).update(f"[bold #88c0d0]{scene.label}[/]")
        self.query_one("#demo-desc", Static).update(scene.description)
        self.query_one("#demo-progress", Static).update(
            f"[dim]scene {self.idx + 1} of {len(self.scenes)} · "
            f"{'paused' if self.paused else f'{scene.dwell:.1f}s'}[/]"
        )

    def _advance(self) -> None:
        self.idx += 1
        if self.idx >= len(self.scenes):
            self.notify("Demo finished.", severity="information")
            self.app.pop_screen()
            return
        scene = self.scenes[self.idx]
        self._show_scene(scene)
        # Push the target screen; overlay stays beneath the new screen,
        # so we update our own state first then transition.
        try:
            target = scene.make_screen(self.mindmap_id)
            self.app.push_screen(target)
            # Schedule the timer for advancing — runs while the child screen
            # is mounted; when it fires we pop back to the autopilot, which
            # immediately pushes the next scene.
            self._timer = self.app.set_timer(scene.dwell, self._scene_done)
        except Exception as e:
            log.exception("autopilot scene %d failed", self.idx)
            self.notify(f"Scene failed: {e}", severity="error")
            self._timer = self.app.set_timer(1.0, self._scene_done)

    def _scene_done(self) -> None:
        if self.paused:
            return
        # Pop the child screen if it's on top of us
        while len(self.app.screen_stack) > 1 and self.app.screen is not self:
            self.app.pop_screen()
        self._advance()

    def action_toggle_pause(self) -> None:
        self.paused = not self.paused
        scene = self.scenes[self.idx] if 0 <= self.idx < len(self.scenes) else None
        if scene:
            self._show_scene(scene)
        if self.paused:
            self.notify("Paused.", severity="information")
        else:
            self.notify("Resumed.", severity="information")
            # restart the timer for the remaining dwell
            if scene:
                self._timer = self.app.set_timer(scene.dwell, self._scene_done)

    def action_next_now(self) -> None:
        self._scene_done()

    def action_restart_scene(self) -> None:
        self.idx -= 1
        self._scene_done()

    def action_stop(self) -> None:
        # Pop everything above us, then ourselves.
        while len(self.app.screen_stack) > 1 and self.app.screen is not self:
            self.app.pop_screen()
        self.app.pop_screen()
