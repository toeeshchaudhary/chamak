from __future__ import annotations

import logging

from textual.app import App
from textual.binding import Binding
from textual.reactive import reactive

from chamak.config import get_mode, paths, set_mode, setup_logging
from chamak.storage.db import connect
from chamak.storage.migrator import migrate
from chamak.tui.theme import DEFAULT_CSS

log = logging.getLogger("chamak.tui")


class ChamakApp(App):
    CSS = DEFAULT_CSS
    TITLE = "Chamak"
    SUB_TITLE = "investor reasoning engine"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("question_mark", "help", "Help"),
        Binding("colon", "show_palette", "Command"),
        Binding("slash", "show_search", "Search"),
        Binding("ctrl+m", "toggle_mode", "Toggle mode", priority=True),
    ]

    current_mindmap_id: reactive[str | None] = reactive(None)

    def __init__(
        self,
        *,
        start_screen: str = "auto",
        interview_name: str | None = None,
        force_mode: str | None = None,
    ):
        super().__init__()
        self.start_screen = start_screen
        self.interview_name = interview_name or "My Style"
        self.force_mode = force_mode
        self.conn = connect()

    @property
    def mode(self) -> str:
        return self.force_mode or get_mode()

    def on_mount(self) -> None:
        if self.start_screen == "interview":
            from chamak.tui.screens.interview import InterviewScreen
            self.push_screen(InterviewScreen(name=self.interview_name))
            return
        if self.start_screen == "demo_pilot":
            self._boot_advanced_demo()
            return
        if self.start_screen == "simple_demo":
            from chamak.tui.simple.autopilot import SimpleAutopilotScreen
            self.push_screen(SimpleAutopilotScreen())
            return
        # auto: route by mode + state
        if self.mode == "advanced":
            from chamak.tui.screens.splash import SplashScreen
            self.push_screen(SplashScreen())
            return
        # simple mode
        self._boot_simple()

    def _boot_simple(self) -> None:
        from chamak.storage.repositories import mindmaps as mm_repo
        from chamak.tui.simple.home import SimpleHomeScreen
        from chamak.tui.simple.welcome import SimpleWelcomeScreen

        mms = mm_repo.list_all(self.conn)
        if not mms:
            self.push_screen(SimpleWelcomeScreen())
        else:
            self.push_screen(SimpleHomeScreen(mindmap_id=mms[0].id))

    def _boot_advanced_demo(self) -> None:
        from chamak.tui.screens.demo_pilot import (
            DemoPilotLauncherScreen,
            DemoPilotScreen,
        )
        from chamak.storage.repositories import mindmaps as mm_repo

        mms = mm_repo.list_all(self.conn)
        anchor = None
        for m in mms:
            if m.name == "Value Investor":
                anchor = m.id
                break
        if anchor is None and mms:
            anchor = mms[0].id
        if anchor:
            self.push_screen(DemoPilotScreen(mindmap_id=anchor))
        else:
            self.push_screen(DemoPilotLauncherScreen())

    # --- navigation actions (advanced-mode hot keys, registered globally) ---

    def action_go_dashboard(self) -> None:
        from chamak.tui.screens.dashboard import DashboardScreen
        self.push_screen(DashboardScreen())

    def action_go_library(self) -> None:
        from chamak.tui.screens.library import LibraryScreen
        self.push_screen(LibraryScreen())

    def action_go_recs(self) -> None:
        from chamak.tui.screens.recommendations import RecommendationsScreen
        self.push_screen(RecommendationsScreen())

    def action_go_portfolio(self) -> None:
        from chamak.tui.screens.portfolio import PortfolioScreen
        self.push_screen(PortfolioScreen())

    def action_go_scanner(self) -> None:
        from chamak.tui.screens.scanner import ScannerScreen
        self.push_screen(ScannerScreen())

    def action_go_news(self) -> None:
        from chamak.tui.screens.news_center import NewsScreen
        self.push_screen(NewsScreen())

    def action_go_interview(self) -> None:
        from chamak.tui.screens.interview import InterviewScreen
        self.push_screen(InterviewScreen(name="My Mind Map"))

    def action_go_settings(self) -> None:
        from chamak.tui.screens.settings import SettingsScreen
        self.push_screen(SettingsScreen())

    def action_help(self) -> None:
        from chamak.tui.screens.help import HelpScreen
        self.push_screen(HelpScreen())

    def action_back(self) -> None:
        if len(self.screen_stack) > 1:
            self.pop_screen()

    def action_show_palette(self) -> None:
        from chamak.tui.palette import open_palette
        open_palette(self)

    def action_show_search(self) -> None:
        from chamak.tui.search import open_search
        open_search(self)

    def action_toggle_mode(self) -> None:
        new_mode = "advanced" if self.mode == "simple" else "simple"
        set_mode(new_mode)
        self.force_mode = None  # respect persisted preference now
        self.notify(f"Switched to {new_mode.upper()} mode.", severity="information")
        # Reboot into the new mode's root screen
        while len(self.screen_stack) > 1:
            self.pop_screen()
        # Force the boot path now that we're back to a fresh stack
        if new_mode == "advanced":
            from chamak.tui.screens.dashboard import DashboardScreen
            self.push_screen(DashboardScreen())
        else:
            self._boot_simple()

    def on_unmount(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass


def run_app(
    *,
    start_screen: str = "auto",
    interview_name: str | None = None,
    force_mode: str | None = None,
) -> None:
    setup_logging()
    migrate()
    log.info("starting TUI; db=%s; mode=%s", paths().db, force_mode or get_mode())
    ChamakApp(
        start_screen=start_screen,
        interview_name=interview_name,
        force_mode=force_mode,
    ).run()
