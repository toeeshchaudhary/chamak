from __future__ import annotations


from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, ListItem, ListView, Static

from chamak.core.models import MindMapSnapshot
from chamak.explain.verdict import for_score
from chamak.recommendation.engine import rank_from_db
from chamak.storage.repositories import mindmaps as mm_repo, stocks as stocks_repo, versions as ver_repo
from chamak.tui.widgets.score_bar import render_bar, render_pct


class RecommendationsScreen(Screen):
    BINDINGS = [
        Binding("r", "rerun", "Run"),
        Binding("enter", "open_stock", "Stock detail"),
    ]

    DEFAULT_CSS = """
    #cols { height: 1fr; }
    #left { width: 32; }
    #right { width: 1fr; padding-left: 2; }
    """

    def __init__(self) -> None:
        super().__init__()
        self.snap: MindMapSnapshot | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold]Stocks ranked by how well they fit your style[/]", classes="title")
        with Horizontal(id="cols"):
            with Vertical(id="left"):
                yield Static("[bold]Pick a style[/]", classes="panel-title")
                self.lv = ListView()
                yield self.lv
                yield Static(
                    "[dim]Enter to score every cached stock against the selected style.[/]",
                    classes="dim",
                )
            with Vertical(id="right"):
                yield Static("[bold]Best matches first[/]", classes="panel-title")
                self.table = DataTable(cursor_type="row")
                self.table.add_columns("Ticker", "Verdict", "Fit", "Sector")
                yield self.table
                self.status = Static("", classes="dim")
                yield self.status
        yield Footer()

    def on_mount(self) -> None:
        conn = self.app.conn  # type: ignore[attr-defined]
        self._mm_ids: list[str] = []
        for m in mm_repo.list_all(conn):
            self.lv.append(ListItem(Static(f"{m.name}  [dim]{m.archetype}[/]"), id=f"mm-{m.id}"))
            self._mm_ids.append(m.id)
        if not self._mm_ids:
            self.status.update("No mind maps yet — run the interview first (press I).")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        mm_id = event.item.id.removeprefix("mm-") if event.item.id else None
        if mm_id:
            self._run_for(mm_id)

    def action_rerun(self) -> None:
        if self.lv.highlighted_child and self.lv.highlighted_child.id:
            self._run_for(self.lv.highlighted_child.id.removeprefix("mm-"))

    def _run_for(self, mm_id: str) -> None:
        conn = self.app.conn  # type: ignore[attr-defined]
        snap = ver_repo.load_latest(conn, mm_id)
        if not snap:
            self.status.update("This mind map has no saved versions yet.")
            return
        self.snap = snap
        stocks = stocks_repo.list_stocks(conn)
        if not stocks:
            self.status.update("No cached stocks. Run `chamak ingest --universe nifty50` first.")
            return
        recs = rank_from_db(conn, snap, [s.ticker for s in stocks], top_k=50)
        self.table.clear()
        self._row_tickers: list[str] = []
        for r in recs:
            stock = stocks_repo.get_stock(conn, r.ticker)
            v = for_score(r.score, hard_failures=bool(r.breakdown.hard_failures))
            verdict_cell = f"[{v.color}]{v.label}[/]"
            fit_cell = f"{render_bar(r.score, width=14)} [{v.color}]{r.score:.0%}[/]"
            self.table.add_row(
                r.ticker,
                verdict_cell,
                fit_cell,
                stock.sector if stock else "",
            )
            self._row_tickers.append(r.ticker)
        self.status.update(f"Scored {len(recs)} stock(s) against '{snap.mindmap.name}' v{snap.mindmap.current_version}.")

    def action_open_stock(self) -> None:
        if not self.snap:
            return
        try:
            ticker = self._row_tickers[self.table.cursor_row]
        except (IndexError, AttributeError):
            return
        from chamak.tui.screens.stock_detail import StockDetailScreen
        self.app.push_screen(StockDetailScreen(ticker=ticker, mindmap_id=self.snap.mindmap.id))
