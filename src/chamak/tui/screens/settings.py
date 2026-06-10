from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from chamak.config import openrouter_key, paths


class SettingsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold]Settings[/]", classes="title")
        p = paths()
        body = (
            f"[bold]Paths[/]\n"
            f"  db:           {p.db}\n"
            f"  cache:        {p.cache}\n"
            f"  logs:         {p.logs}\n\n"
            f"[bold]LLM[/]\n"
            f"  OPENROUTER_API_KEY: {'set' if openrouter_key() else '[red]not set[/]'}\n"
            f"  default model:      openai/gpt-4o-mini (via OpenRouter)\n\n"
            f"[bold]Caching[/]\n"
            f"  fundamentals TTL:   7 days\n"
            f"  OHLCV TTL:          24 hours\n\n"
            f"[dim]To edit settings, set environment variables. The TUI does not "
            f"persist credentials. Logs are written to {p.logs}/chamak.log.[/]"
        )
        yield Static(body, classes="panel")
        yield Footer()
