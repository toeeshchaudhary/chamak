from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Static

from chamak.tui.widgets.banner import Banner


class SplashScreen(Screen):
    BINDINGS = []
    DEFAULT_CSS = """
    SplashScreen { background: #0c0c0e; }
    #tag { color: #6b6b6b; }
    """

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                yield Banner()
            with Center():
                yield Static("[#6b6b6b]press any key to continue · or wait[/]", id="tag")

    def on_mount(self) -> None:
        self.set_timer(1.4, self._go)

    def on_key(self, _event) -> None:
        self._go()

    def _go(self) -> None:
        from chamak.storage.repositories import mindmaps as mm_repo
        conn = self.app.conn  # type: ignore[attr-defined]
        # First-run check: no mindmaps → onboarding.
        if not mm_repo.list_all(conn, include_archived=True):
            from chamak.tui.screens.welcome import WelcomeScreen
            self.app.switch_screen(WelcomeScreen())
            return
        from chamak.tui.screens.dashboard import DashboardScreen
        self.app.switch_screen(DashboardScreen())
