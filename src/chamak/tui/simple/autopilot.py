"""Simple-mode interactive demo autopilot.

A scripted walk through:
  1. Welcome
  2. Quiz (auto-picks 'balanced / steady / fair')
  3. Home
  4. Stock card carousel (auto-flips through 3 cards)
  5. Vibe check (auto-plays 3 rounds)
  6. Flowchart reveal

Designed for screen recording. Captions appear over each step.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from chamak.demo.seeder import seed
from chamak.storage.repositories import mindmaps as mm_repo

log = logging.getLogger("chamak.tui.simple.autopilot")


@dataclass
class _Step:
    label: str
    caption: str
    delay: float
    action: str           # "show_welcome" | "quiz_pick" | "show_home" | "show_picks" | "next_card" | "show_vibe" | "vibe_pick" | "show_flow" | "done"
    arg: str | int | None = None


_QUIZ_PICKS = ["balanced", "steady", "fair"]


def _steps() -> list[_Step]:
    return [
        _Step("1 / 8", "Meet Chamak. We'll find stocks that fit how you think.",
              3.5, "show_welcome"),
        _Step("2 / 8", "Three quick questions. No financial jargon.",
              2.5, "show_quiz"),
        _Step("3 / 8", "Pick 1: Balanced — some ups and downs are fine.",
              2.2, "quiz_pick", 1),
        _Step("3 / 8", "Pick 2: A steady, boring, profitable business.",
              2.2, "quiz_pick", 0),
        _Step("3 / 8", "Pick 3: Fair price for fair quality.",
              2.2, "quiz_pick", 1),
        _Step("4 / 8", "Done. Chamak built your style and loaded sample stocks.",
              3.5, "show_home"),
        _Step("5 / 8", "Here are stocks that fit you, ranked. With real candle charts.",
              5.0, "show_picks"),
        _Step("5 / 8", "Each card explains in plain English why it fits you.",
              4.0, "next_card"),
        _Step("5 / 8", "And the next one. Notice the star rating.",
              4.0, "next_card"),
        _Step("6 / 8", "Now a quick game: which would you rather own?",
              3.5, "show_vibe"),
        _Step("6 / 8", "Pick the left one. Chamak checks if that matches your style.",
              2.5, "vibe_pick", "left"),
        _Step("6 / 8", "And again. This time, the right one.",
              2.5, "vibe_pick", "right"),
        _Step("7 / 8", "Now let's see WHAT Chamak learned about you — as a flowchart.",
              5.0, "show_flow"),
        _Step("8 / 8", "That's it. Press q to exit, or play around yourself.",
              2.5, "done"),
    ]


class SimpleAutopilotScreen(Screen):
    BINDINGS = [
        Binding("space", "toggle_pause", "Pause/Resume"),
        Binding("right", "advance_now", "Skip step"),
        Binding("q", "stop", "Stop", priority=True),
        Binding("escape", "stop", "Stop"),
    ]

    DEFAULT_CSS = """
    SimpleAutopilotScreen { background: #0a0a0d; }
    #wrap { padding: 1 4; height: 1fr; align: center middle; }
    #brand { color: #88c0d0; text-style: bold; }
    #step { color: #5e81ac; text-style: bold; padding-top: 1; }
    #caption { color: #e8e8e8; padding: 1 2; text-align: center; }
    #help { color: #5a5a5a; padding-top: 2; text-align: center; }
    """

    def __init__(self) -> None:
        super().__init__()
        self.idx = -1
        self.steps = _steps()
        self.paused = False
        self.mindmap_id: str | None = None
        self.quiz_answers: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="wrap"):
            with Center():
                yield Static("CHAMAK · interactive demo", id="brand")
            with Center():
                yield Static("", id="step")
            with Center():
                yield Static("", id="caption")
            with Center():
                yield Static(
                    "space pause/resume   →  skip step   q  quit",
                    id="help",
                )
        yield Footer()

    def on_mount(self) -> None:
        # Make sure demo data exists (don't duplicate, seed is idempotent)
        seed(self.app.conn)  # type: ignore[attr-defined]
        self._advance()

    def _show(self) -> None:
        if self.idx >= len(self.steps):
            return
        s = self.steps[self.idx]
        self.query_one("#step", Static).update(s.label)
        self.query_one("#caption", Static).update(s.caption)

    def _advance(self) -> None:
        if self.paused:
            return
        # Clean any child screen pushed by previous step
        while len(self.app.screen_stack) > 1 and self.app.screen is not self:
            self.app.pop_screen()
        self.idx += 1
        if self.idx >= len(self.steps):
            self.notify("Demo complete.", severity="information")
            self.app.pop_screen()
            return
        self._show()
        self._run_step()

    def _run_step(self) -> None:
        if self.idx >= len(self.steps):
            return
        s = self.steps[self.idx]
        try:
            self._perform(s)
        except Exception as e:  # noqa: BLE001
            log.exception("autopilot step failed: %s", s.action)
            self.notify(f"Step failed: {e}", severity="error")
        self.app.set_timer(s.delay, self._advance)

    def _perform(self, s: _Step) -> None:
        if s.action == "show_welcome":
            from chamak.tui.simple.welcome import SimpleWelcomeScreen
            self.app.push_screen(SimpleWelcomeScreen())
        elif s.action == "show_quiz":
            from chamak.tui.simple.quiz import SimpleQuizScreen
            scr = SimpleQuizScreen()
            self.app.push_screen(scr)
        elif s.action == "quiz_pick":
            from chamak.tui.simple.quiz import SimpleQuizScreen
            # The current screen should be the quiz
            scr = self.app.screen
            if isinstance(scr, SimpleQuizScreen):
                scr._pick(int(s.arg))  # type: ignore[arg-type]
                if scr.idx >= 3:
                    # quiz finished, grab the mindmap_id from the new screen
                    pass
        elif s.action == "show_home":
            from chamak.tui.simple.home import SimpleHomeScreen
            # Pick the most recent style
            mms = mm_repo.list_all(self.app.conn)  # type: ignore[attr-defined]
            mm = next((m for m in mms if m.name.startswith("My Style")), None)
            if mm is None and mms:
                mm = mms[0]
            if mm:
                self.mindmap_id = mm.id
                # Pop the quiz first if it's still on top
                while len(self.app.screen_stack) > 1 and self.app.screen is not self:
                    self.app.pop_screen()
                self.app.push_screen(SimpleHomeScreen(mindmap_id=mm.id))
        elif s.action == "show_picks":
            from chamak.tui.simple.stock_card import SimpleStockCardScreen
            if self.mindmap_id:
                self.app.push_screen(SimpleStockCardScreen(mindmap_id=self.mindmap_id))
        elif s.action == "next_card":
            from chamak.tui.simple.stock_card import SimpleStockCardScreen
            scr = self.app.screen
            if isinstance(scr, SimpleStockCardScreen):
                scr.action_next()
        elif s.action == "show_vibe":
            from chamak.tui.simple.vibe_check import VibeCheckScreen
            # Pop the stock-card screen
            while len(self.app.screen_stack) > 1 and self.app.screen is not self:
                self.app.pop_screen()
            if self.mindmap_id:
                self.app.push_screen(VibeCheckScreen(mindmap_id=self.mindmap_id))
        elif s.action == "vibe_pick":
            from chamak.tui.simple.vibe_check import VibeCheckScreen
            scr = self.app.screen
            if isinstance(scr, VibeCheckScreen):
                if s.arg == "left":
                    scr.action_pick_left()
                else:
                    scr.action_pick_right()
        elif s.action == "show_flow":
            from chamak.tui.screens.flowchart_view import FlowchartViewScreen
            while len(self.app.screen_stack) > 1 and self.app.screen is not self:
                self.app.pop_screen()
            if self.mindmap_id:
                self.app.push_screen(FlowchartViewScreen(mindmap_id=self.mindmap_id))
        elif s.action == "done":
            while len(self.app.screen_stack) > 1 and self.app.screen is not self:
                self.app.pop_screen()

    def action_toggle_pause(self) -> None:
        self.paused = not self.paused
        if not self.paused:
            self._advance()
        else:
            self.notify("Paused.", severity="information")

    def action_advance_now(self) -> None:
        self._advance()

    def action_stop(self) -> None:
        while len(self.app.screen_stack) > 1 and self.app.screen is not self:
            self.app.pop_screen()
        self.app.pop_screen()
