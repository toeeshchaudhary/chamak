from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from chamak.explain.verdict import for_score
from chamak.news.repository import for_ticker
from chamak.rules import metrics as metrics_reg
from chamak.scoring.engine import score
from chamak.storage.repositories import stocks as stocks_repo, versions as ver_repo
from chamak.tui.widgets.flowchart import render_flowchart
from chamak.tui.widgets.score_bar import render_bar


class StockDetailScreen(Screen):
    BINDINGS = [Binding("v", "back", "Back")]

    DEFAULT_CSS = """
    StockDetailScreen { layout: vertical; }
    #title-bar { height: auto; padding: 0 2; }
    #verdict-bar { height: auto; padding: 0 2; }
    #chart-wrap { height: 55%; padding: 0 2; }
    #lower { height: 1fr; padding: 0 2; }
    #fund { width: 50%; }
    #news { width: 1fr; padding-left: 2; }
    """

    def __init__(self, ticker: str, mindmap_id: str) -> None:
        super().__init__()
        self.ticker = ticker
        self.mindmap_id = mindmap_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="title-bar", classes="title")
        yield Static("", id="verdict-bar")
        with VerticalScroll(id="chart-wrap"):
            self.chart = Static("[dim]Loading…[/]", id="chart")
            yield self.chart
        with Horizontal(id="lower"):
            with Vertical(id="fund"):
                yield Static("[bold]Numbers we used[/]", classes="panel-title")
                self.fund_table = DataTable(cursor_type="row")
                self.fund_table.add_columns("What it measures", "Value")
                yield self.fund_table
            with Vertical(id="news"):
                yield Static("[bold]Recent news[/]", classes="panel-title")
                with VerticalScroll():
                    self.news_panel = Static("", classes="panel")
                    yield self.news_panel
        yield Footer()

    def on_mount(self) -> None:
        conn = self.app.conn  # type: ignore[attr-defined]
        f = stocks_repo.latest_fundamentals(conn, self.ticker)
        s = stocks_repo.get_stock(conn, self.ticker)
        snap = ver_repo.load_latest(conn, self.mindmap_id)

        if s:
            self.query_one("#title-bar", Static).update(
                f"[bold]{s.ticker}[/]  {s.name}  [dim]{s.sector} / {s.industry}[/]"
            )

        # Fundamentals table: use plain-English column "What it measures"
        if f:
            for k in sorted(f.metrics.keys()):
                spec = metrics_reg.get(k)
                value = f.metrics[k]
                unit = spec.unit_suffix if (spec and spec.unit_suffix) else ""
                shown = f"{value:.3g}{unit}".strip() or f"{value:.3g}"
                self.fund_table.add_row(spec.plain if spec else k, shown)

        if not snap:
            self.chart.update("[dim]This style has no saved version.[/]")
            self.query_one("#verdict-bar", Static).update("")
        elif f is None:
            self.chart.update(render_flowchart(snap, max_width=max(100, (self.size.width or 120) - 6)))
            self.query_one("#verdict-bar", Static).update(
                "[dim]No data for this stock — score not computed.[/]"
            )
        else:
            b = score(snap, f)
            v = for_score(b.score, hard_failures=bool(b.hard_failures))
            # Verdict bar
            self.query_one("#verdict-bar", Static).update(
                f"[bold {v.color}]{v.label}[/]   "
                f"{render_bar(b.score, width=24)}  "
                f"[{v.color}]{b.score:.0%}[/]  "
                f"[dim]· {v.headline}[/]"
            )
            # Color the flowchart: green for matched, red for failed, dim for missing
            rule_status: dict[str, str] = {}
            for c in b.contributions:
                if c.missing_metric:
                    rule_status[c.rule_id] = "missing"
                elif c.satisfaction >= 0.5:
                    rule_status[c.rule_id] = "match"
                else:
                    rule_status[c.rule_id] = "fail"
            width = max(100, (self.size.width or 120) - 6)
            self.chart.update(render_flowchart(snap, rule_status=rule_status, max_width=width))

        news = for_ticker(conn, self.ticker, limit=5)
        if news:
            lines = []
            for nws in news:
                tags = ", ".join(
                    t.get("label", "") for t in nws["sentiment"][:3]
                )
                lines.append(f"  · {nws['title']}")
                lines.append(f"    [dim]{nws['source']}{(' · ' + tags) if tags else ''}[/]")
            self.news_panel.update("\n".join(lines))
        else:
            self.news_panel.update("[dim]No news for this ticker.[/]")

    def action_back(self) -> None:
        self.app.pop_screen()
