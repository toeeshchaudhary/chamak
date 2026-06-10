from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from chamak.core.models import Holding, Portfolio
from chamak.portfolio.analysis import analyze
from chamak.storage.repositories import (
    portfolios as port_repo,
    versions as ver_repo,
)


class _NewPortfolioModal(ModalScreen[Portfolio | None]):
    DEFAULT_CSS = "_NewPortfolioModal { align: center middle; } #box { background: #1a1a1c; padding:1 2; width:60; border: tall #2a2a2c; }"

    def compose(self) -> ComposeResult:
        with Vertical(id="box"):
            yield Static("[bold]New portfolio[/]", classes="panel-title")
            self.name_input = Input(placeholder="name")
            self.mm_input = Input(placeholder="mind map id (optional)")
            yield self.name_input
            yield self.mm_input
            with Horizontal():
                yield Button("Create", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, e: Button.Pressed) -> None:
        if e.button.id == "cancel":
            self.dismiss(None)
            return
        n = self.name_input.value.strip()
        if not n:
            self.notify("Name required.", severity="warning")
            return
        self.dismiss(Portfolio(name=n, mindmap_id=self.mm_input.value.strip() or None))


class _AddHoldingModal(ModalScreen[Holding | None]):
    DEFAULT_CSS = "_AddHoldingModal { align: center middle; } #box { background: #1a1a1c; padding:1 2; width:60; border: tall #2a2a2c; }"

    def __init__(self, portfolio_id: str) -> None:
        super().__init__()
        self.portfolio_id = portfolio_id

    def compose(self) -> ComposeResult:
        with Vertical(id="box"):
            yield Static("[bold]Add holding[/]", classes="panel-title")
            self.ticker = Input(placeholder="ticker")
            self.qty = Input(placeholder="quantity")
            self.avg = Input(placeholder="avg cost (optional)", value="0")
            yield self.ticker
            yield self.qty
            yield self.avg
            with Horizontal():
                yield Button("Add", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, e: Button.Pressed) -> None:
        if e.button.id == "cancel":
            self.dismiss(None)
            return
        try:
            h = Holding(
                portfolio_id=self.portfolio_id,
                ticker=self.ticker.value.strip().upper(),
                quantity=float(self.qty.value),
                avg_cost=float(self.avg.value or "0"),
            )
        except ValueError:
            self.notify("Bad numbers.", severity="warning")
            return
        self.dismiss(h)


class PortfolioScreen(Screen):
    BINDINGS = [
        Binding("n", "new_portfolio", "New"),
        Binding("a", "add_holding", "Add holding"),
        Binding("x", "delete_holding", "Delete holding"),
        Binding("r", "analyze", "Analyze"),
    ]

    DEFAULT_CSS = """
    #cols { height: 1fr; }
    #left { width: 35; }
    #right { width: 1fr; padding-left: 2; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold]Portfolios[/]", classes="title")
        with Horizontal(id="cols"):
            with Vertical(id="left"):
                yield Static("[bold]Your portfolios[/]", classes="panel-title")
                self.portfolio_table = DataTable(cursor_type="row")
                self.portfolio_table.add_columns("Name", "Mind Map")
                yield self.portfolio_table
                yield Static("[dim]n new, r analyze[/]", classes="dim")
            with Vertical(id="right"):
                yield Static("[bold]Holdings & analysis[/]", classes="panel-title")
                self.holding_table = DataTable(cursor_type="row")
                self.holding_table.add_columns("Ticker", "Qty", "Avg Cost")
                yield self.holding_table
                with VerticalScroll():
                    self.report = Static("Pick a portfolio; press r to analyze.", classes="panel")
                    yield self.report
        yield Footer()

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        self.portfolio_table.clear()
        self._pids: list[str] = []
        for p in port_repo.list_all(self.app.conn):  # type: ignore[attr-defined]
            self.portfolio_table.add_row(p.name, p.mindmap_id or "—")
            self._pids.append(p.id)
        self.holding_table.clear()
        self.report.update("")

    def _selected_portfolio_id(self) -> str | None:
        try:
            return self._pids[self.portfolio_table.cursor_row]
        except (IndexError, AttributeError):
            return None

    def on_data_table_row_highlighted(self, _e) -> None:
        self._refresh_holdings()

    def _refresh_holdings(self) -> None:
        pid = self._selected_portfolio_id()
        self.holding_table.clear()
        self._hids: list[str] = []
        if not pid:
            return
        for h in port_repo.holdings(self.app.conn, pid):  # type: ignore[attr-defined]
            self.holding_table.add_row(h.ticker, f"{h.quantity:g}", f"{h.avg_cost:g}")
            self._hids.append(h.id)

    async def action_new_portfolio(self) -> None:
        p = await self.app.push_screen(_NewPortfolioModal(), wait_for_dismiss=True)
        if not p:
            return
        port_repo.create(self.app.conn, p)  # type: ignore[attr-defined]
        self._refresh()

    async def action_add_holding(self) -> None:
        pid = self._selected_portfolio_id()
        if not pid:
            return
        h = await self.app.push_screen(_AddHoldingModal(pid), wait_for_dismiss=True)
        if h:
            port_repo.add_holding(self.app.conn, h)  # type: ignore[attr-defined]
            self._refresh_holdings()

    def action_delete_holding(self) -> None:
        try:
            hid = self._hids[self.holding_table.cursor_row]
        except (IndexError, AttributeError):
            return
        port_repo.remove_holding(self.app.conn, hid)  # type: ignore[attr-defined]
        self._refresh_holdings()

    def action_analyze(self) -> None:
        pid = self._selected_portfolio_id()
        if not pid:
            return
        p = port_repo.get(self.app.conn, pid)  # type: ignore[attr-defined]
        if not p or not p.mindmap_id:
            self.report.update("Portfolio has no linked mind map. Set mindmap_id in the DB or edit creation flow.")
            return
        snap = ver_repo.load_latest(self.app.conn, p.mindmap_id)  # type: ignore[attr-defined]
        if not snap:
            self.report.update("Linked mind map has no saved version.")
            return
        rep = analyze(self.app.conn, pid, snap)  # type: ignore[attr-defined]
        lines = [
            f"Holdings: {rep.n_holdings}   Scored: {rep.n_scored}   "
            f"Avg compatibility: {rep.avg_compatibility:.0%}",
            "",
        ]
        if rep.violations:
            lines.append("[bold]Top contradictions[/]")
            for v in rep.violations[:10]:
                lines.append(f"  {v.ticker}: {v.rule_text}  [dim]sat {v.satisfaction:.0%}[/]")
        if rep.sector_concentration:
            lines.append("")
            lines.append("[bold]Sector mix[/]")
            for sec, w in sorted(rep.sector_concentration.items(), key=lambda kv: -kv[1]):
                lines.append(f"  {sec:24s} {w:.0%}")
        for n in rep.notes:
            lines.append(f"· {n}")
        self.report.update("\n".join(lines) or "No analysis.")
