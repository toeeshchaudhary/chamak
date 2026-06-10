from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from chamak.news.repository import list_recent


class NewsScreen(Screen):
    BINDINGS = [Binding("r", "refresh", "Refresh")]

    DEFAULT_CSS = """
    NewsScreen Vertical { height: 1fr; }
    #cols { height: 1fr; }
    #left { width: 65%; }
    #right { width: 1fr; padding-left: 2; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold]News Intelligence Center[/]", classes="title")
        with Horizontal(id="cols"):
            with Vertical(id="left"):
                self.table = DataTable(cursor_type="row")
                self.table.add_columns("When", "Source", "Title", "Tickers")
                yield self.table
            with Vertical(id="right"):
                yield Static("[bold]Sentiment + body[/]", classes="panel-title")
                with VerticalScroll():
                    self.detail = Static(
                        "Pick a story on the left to see its sentiment tags.",
                        classes="panel",
                    )
                    yield self.detail
        yield Footer()

    def on_mount(self) -> None:
        self.action_refresh()

    def action_refresh(self) -> None:
        self.table.clear()
        self._items = list_recent(self.app.conn, limit=50)  # type: ignore[attr-defined]
        if not self._items:
            self.detail.update(
                "[dim]No news in the database yet. Run the demo (D on dashboard) "
                "to seed example headlines.[/]"
            )
        for it in self._items:
            when = it["published_at"].strftime("%Y-%m-%d") if it["published_at"] else "—"
            tickers = ", ".join(it["tickers"][:3])
            if len(it["tickers"]) > 3:
                tickers += "…"
            self.table.add_row(when, it["source"], it["title"], tickers)
        if self._items:
            self.table.move_cursor(row=0)
            self._render_detail(0)

    def on_data_table_row_highlighted(self, event) -> None:
        try:
            self._render_detail(int(event.cursor_row))
        except (ValueError, TypeError):
            pass

    def _render_detail(self, idx: int) -> None:
        if not (0 <= idx < len(self._items)):
            return
        it = self._items[idx]
        lines = [
            f"[bold]{it['title']}[/]",
            f"[dim]{it['source']}  ·  "
            f"{it['published_at'].strftime('%Y-%m-%d %H:%M') if it['published_at'] else ''}[/]",
            "",
        ]
        if it["tickers"]:
            lines.append(f"[bold]Tickers:[/] {', '.join(it['tickers'])}")
        if it["sectors"]:
            lines.append(f"[bold]Sectors:[/] {', '.join(it['sectors'])}")
        if it["sentiment"]:
            lines.append("")
            lines.append("[bold]Sentiment[/]")
            for tag in it["sentiment"]:
                label = tag.get("label", "")
                conf = float(tag.get("confidence", 0))
                color = _sentiment_color(label)
                lines.append(f"  [{color}]{label:24s}[/]  conf {conf:.0%}")
        if it["body"]:
            lines.append("")
            lines.append(it["body"])
        self.detail.update("\n".join(lines))


_BULL = "#98c379"
_BEAR = "#e06c75"
_NEUT = "#e5c07b"
_RISK = "#d19a66"

_SENT_COLORS = {
    "bullish": _BULL, "growth_signal": _BULL, "innovation_signal": _BULL,
    "sector_tailwind": _BULL, "competitive_advantage": _BULL,
    "bearish": _BEAR, "competitive_threat": _BEAR, "sector_headwind": _BEAR,
    "debt_concern": _RISK, "management_concern": _RISK,
    "regulatory_risk": _RISK, "governance_risk": _RISK, "macro_risk": _RISK,
    "supply_chain_risk": _RISK,
}


def _sentiment_color(label: str) -> str:
    return _SENT_COLORS.get(label, _NEUT)
