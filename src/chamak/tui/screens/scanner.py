from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, ListItem, ListView, Static

from chamak.market_data.universe import universe as resolve_universe
from chamak.recommendation.engine import rank_from_db
from chamak.storage.repositories import mindmaps as mm_repo, versions as ver_repo
from chamak.tui.widgets.score_bar import render_bar, render_pct


class ScannerScreen(Screen):
    BINDINGS = [Binding("r", "run", "Run")]
    DEFAULT_CSS = """
    #cols { height: 1fr; }
    #left { width: 32; }
    #right { width: 1fr; padding-left: 2; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold]Market Scanner[/]", classes="title")
        with Horizontal(id="cols"):
            with Vertical(id="left"):
                yield Static("[bold]Mind Map[/]", classes="panel-title")
                self.mm_lv = ListView()
                yield self.mm_lv
                yield Static("[bold]Universe[/]", classes="panel-title")
                self.u_lv = ListView(ListItem(Static("Nifty 50"), id="u-nifty50"))
                yield self.u_lv
                yield Static("[dim]r to run; only stocks with cached fundamentals score.[/]", classes="dim")
            with Vertical(id="right"):
                yield Static("[bold]Top matches[/]", classes="panel-title")
                self.table = DataTable(cursor_type="row")
                self.table.add_columns("Ticker", "Score", "Bar", "Conf")
                yield self.table
                self.status = Static("", classes="dim")
                yield self.status
        yield Footer()

    def on_mount(self) -> None:
        conn = self.app.conn  # type: ignore[attr-defined]
        self._mm_ids: list[str] = []
        for m in mm_repo.list_all(conn):
            self.mm_lv.append(ListItem(Static(f"{m.name}  [dim]{m.archetype}[/]"), id=f"mm-{m.id}"))
            self._mm_ids.append(m.id)

    def action_run(self) -> None:
        mm_item = self.mm_lv.highlighted_child
        u_item = self.u_lv.highlighted_child
        if not (mm_item and mm_item.id and u_item and u_item.id):
            self.status.update("Pick a mind map and a universe.")
            return
        mm_id = mm_item.id.removeprefix("mm-")
        u_name = u_item.id.removeprefix("u-")
        try:
            tickers = resolve_universe(u_name)
        except Exception as e:
            self.status.update(f"Universe error: {e}")
            return
        conn = self.app.conn  # type: ignore[attr-defined]
        snap = ver_repo.load_latest(conn, mm_id)
        if not snap:
            self.status.update("No saved version for selected mind map.")
            return
        recs = rank_from_db(conn, snap, tickers, top_k=50)
        self.table.clear()
        for r in recs:
            self.table.add_row(
                r.ticker, render_pct(r.score), render_bar(r.score), f"{r.confidence:.0%}"
            )
        self.status.update(f"Scanned {len(tickers)} ticker(s), scored {len(recs)}.")
