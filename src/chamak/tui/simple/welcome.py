"""Simple-mode welcome screen.

Friendly, one-paragraph intro. Big single button to start. No options to
distract.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


_LOGO = r"""
    ▄▄▄▄  ▄  ▄  ▄▄▄  ▄   ▄  ▄▄▄  ▄  ▄
   █     █▄▄█ █▄▄█ ██▄█▄█ █▄▄█ █▄▄█
   █▄▄▄█ █  █ █  █ █     █ █  █ █  █
"""


class SimpleWelcomeScreen(Screen):
    BINDINGS = [
        Binding("enter", "start", "Let's go"),
        Binding("space", "start", "Let's go"),
        Binding("a", "advanced", "Advanced mode"),
    ]

    DEFAULT_CSS = """
    SimpleWelcomeScreen { background: #0a0a0d; }
    #wrap { padding: 2 4; height: 1fr; align: center middle; }
    #logo { color: #88c0d0; text-style: bold; padding: 0 0 1 0; }
    #pitch {
        color: #e8e8e8;
        padding: 1 4;
        text-align: center;
        max-width: 80;
    }
    #cta {
        background: #2c2c34;
        color: #ffffff;
        border: tall #5e81ac;
        padding: 1 4;
        margin-top: 2;
        text-style: bold;
    }
    #tiny {
        color: #5a5a5a;
        padding-top: 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="wrap"):
            with Center():
                yield Static(_LOGO, id="logo")
            with Center():
                yield Static(
                    "[bold #e8e8e8]Hi! I'll help you find stocks that fit how you think.[/]\n\n"
                    "Three quick questions. No jargon. No predictions.\n"
                    "Just stocks that match what [italic]you[/] care about.",
                    id="pitch",
                )
            with Center():
                yield Static("  Press [bold]Enter[/] to begin  ", id="cta")
            with Center():
                yield Static(
                    "[dim]A press [bold]a[/] for Advanced mode  ·  Q to quit[/]",
                    id="tiny",
                )
        yield Footer()

    def action_start(self) -> None:
        from chamak.tui.simple.quiz import SimpleQuizScreen
        self.app.switch_screen(SimpleQuizScreen())

    def action_advanced(self) -> None:
        from chamak.config import set_mode
        set_mode("advanced")
        from chamak.tui.screens.welcome import WelcomeScreen
        self.app.switch_screen(WelcomeScreen())
