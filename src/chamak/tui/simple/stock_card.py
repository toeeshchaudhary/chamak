"""Simple-mode stock card carousel — one stock at a time, big and friendly."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class SimpleStockCardScreen(Screen):
    BINDINGS = [
        Binding("right", "next", "Next"),
        Binding("l", "next", "Next"),
        Binding("n", "next", "Next"),
        Binding("space", "next", "Next"),
        Binding("left", "prev", "Prev"),
        Binding("h", "prev", "Prev"),
        Binding("p", "prev", "Prev"),
        Binding("escape", "back", "Home"),
        Binding("q", "back", "Home"),
    ]

    DEFAULT_CSS = """
    SimpleStockCardScreen { background: #0a0a0d; }
    #card { padding: 1 3; }
    #counter { color: #5a5a5a; text-align: center; }
    """

    def __init__(self, mindmap_id: str) -> None:
        super().__init__()
        self.mindmap_id = mindmap_id
        self.idx = 0
        self.recs = []

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Static("Loading...", id="card")
            yield Static(" ", id="counter")
        yield Footer()

    def on_mount(self) -> None:
        from chamak.recommendation.engine import rank_from_db
        from chamak.storage.repositories import versions as ver_repo
        conn = self.app.conn  # type: ignore[attr-defined]
        snap = ver_repo.load_latest(conn, self.mindmap_id)
        if not snap:
            self.query_one("#card", Static).update("No saved style.")
            return
        self.snap = snap
        self.recs = rank_from_db(conn, snap, top_k=12)
        if not self.recs:
            self.query_one("#card", Static).update(
                "No stocks to score - load demo data first."
            )
            return
        self._refresh_card()

    def _refresh_card(self) -> None:
        if not self.recs:
            return
        from chamak.demo.prices import history_for
        from chamak.explain.verdict import for_score
        from chamak.scoring.engine import score
        from chamak.storage.repositories import stocks as stocks_repo
        from chamak.tui.simple.explain_friendly import (
            friendly_concerns,
            friendly_reasons,
            headline_for,
            stars,
        )
        from chamak.tui.widgets.candle import render_candles

        r = self.recs[self.idx]
        conn = self.app.conn  # type: ignore[attr-defined]
        stock = stocks_repo.get_stock(conn, r.ticker)
        f = stocks_repo.latest_fundamentals(conn, r.ticker)
        if f is None or stock is None:
            return
        b = score(self.snap, f)
        v = for_score(b.score, hard_failures=bool(b.hard_failures))

        size_text = ""
        if "market_cap_cr" in f.metrics:
            cap = f.metrics["market_cap_cr"]
            if cap >= 100000:
                size_text = f" - Rs.{cap/100000:.1f} lakh cr"
            elif cap >= 1000:
                size_text = f" - Rs.{cap/1000:.1f}k cr"
            else:
                size_text = f" - Rs.{cap:.0f} cr"

        hist = history_for(r.ticker, days=20)
        chart = render_candles(hist, rows=6, width=30, show_axis=False) if hist else ""

        reasons = friendly_reasons(b, self.snap, limit=3)
        concerns = friendly_concerns(b, self.snap, limit=2)

        parts: list[str] = []
        parts.append(f"[{v.color}]{stars(b.score)}   {v.label}[/]")
        parts.append("")
        parts.append(f"[bold #ffffff]{stock.name}[/]")
        parts.append(f"[#909090]{stock.sector or 'Stock'}{size_text}[/]")
        parts.append("")
        parts.append(headline_for(b.score, hard_fail=bool(b.hard_failures)))
        if chart:
            parts.append("")
            parts.append(chart)
        if reasons:
            parts.append("")
            parts.append("[bold #98c379]Why this fits you[/]")
            for reason in reasons:
                parts.append(f"  [#c8c8c8]+ {reason}[/]")
        if concerns:
            parts.append("")
            parts.append("[bold #e5c07b]Things to keep in mind[/]")
            for concern in concerns:
                parts.append(f"  [#c8c8c8]! {concern}[/]")

        self.query_one("#card", Static).update("\n".join(parts))
        self.query_one("#counter", Static).update(
            f"Stock {self.idx + 1} of {len(self.recs)}    [dim](use n/p or arrow keys, q to go back)[/]"
        )

    def action_next(self) -> None:
        if not self.recs:
            return
        self.idx = (self.idx + 1) % len(self.recs)
        self._refresh_card()

    def action_prev(self) -> None:
        if not self.recs:
            return
        self.idx = (self.idx - 1) % len(self.recs)
        self._refresh_card()

    def action_back(self) -> None:
        self.app.pop_screen()
