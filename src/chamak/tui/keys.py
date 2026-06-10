"""Shared key bindings."""

from __future__ import annotations

from textual.binding import Binding

GLOBAL_BINDINGS = [
    Binding("q", "quit", "Quit", priority=True),
    Binding("?", "help", "Help"),
    Binding("escape", "back", "Back"),
    Binding(":", "command_palette", "Command"),
    Binding("/", "search", "Search"),
    Binding("g", "go_home", "Dashboard"),
    Binding("L", "go_library", "Library"),
    Binding("R", "go_recommendations", "Recs"),
    Binding("P", "go_portfolio", "Portfolios"),
    Binding("S", "go_scanner", "Scanner"),
    Binding("N", "go_news", "News"),
    Binding("I", "go_interview", "Interview"),
]
