"""Vibe Check mini-game.

Show two stocks side-by-side with mini candlestick charts. Player picks
which they'd rather own. After 5 rounds, reveal which one their saved
style actually preferred — a fun A/B alignment check.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from chamak.demo.prices import history_for
from chamak.explain.verdict import for_score
from chamak.recommendation.engine import rank_from_db
from chamak.scoring.engine import score
from chamak.storage.repositories import stocks as stocks_repo, versions as ver_repo
from chamak.tui.simple.explain_friendly import stars
from chamak.tui.widgets.candle import render_candles


@dataclass
class _Round:
    left: str
    right: str
    left_score: float
    right_score: float
    user_pick: str | None = None  # "left" | "right"

    @property
    def style_winner(self) -> str:
        return "left" if self.left_score >= self.right_score else "right"


class VibeCheckScreen(Screen):
    """Tinder-style preference game vs the saved style."""

    BINDINGS = [
        Binding("left", "pick_left", "Left"),
        Binding("h", "pick_left", "Left"),
        Binding("right", "pick_right", "Right"),
        Binding("l", "pick_right", "Right"),
        Binding("escape", "back", "Quit"),
        Binding("q", "back", "Quit"),
        Binding("space", "next", "Next"),
    ]

    DEFAULT_CSS = """
    VibeCheckScreen { background: #0a0a0d; }
    #wrap { padding: 1 3; }
    #q { color: #ffffff; text-style: bold; text-align: center; padding: 0 0 1 0; }
    #progress { color: #5a5a5a; text-align: center; padding: 0 0 1 0; }
    #row { height: auto; align: center middle; }
    .vs-card {
        width: 45;
        border: round #2a2a2c;
        background: #14141a;
        padding: 1 2;
        margin: 0 1;
    }
    .vs-title { text-style: bold; color: #ffffff; padding-bottom: 1; }
    .vs-sub { color: #909090; padding-bottom: 1; }
    .vs-key { color: #5e81ac; text-style: bold; padding-top: 1; text-align: center; }
    #verdict { padding: 1 0; }
    #hint { color: #5a5a5a; text-align: center; padding-top: 1; }
    """

    def __init__(self, mindmap_id: str) -> None:
        super().__init__()
        self.mindmap_id = mindmap_id
        self.rounds: list[_Round] = []
        self.idx = 0
        self.results_mode = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="wrap"):
            yield Static("Which would you rather own?", id="q")
            yield Static("", id="progress")
            row = Horizontal(id="row")
            yield row
            self._row = row
            yield Static("", id="verdict")
            yield Static(
                "[dim]←/h for left   →/l for right   Esc to quit[/]",
                id="hint",
            )
        yield Footer()

    def on_mount(self) -> None:
        self._setup_rounds()
        if not self.rounds:
            self.query_one("#q", Static).update("No stocks to compare yet.")
            return
        self._render_round()

    def _setup_rounds(self) -> None:
        conn = self.app.conn  # type: ignore[attr-defined]
        snap = ver_repo.load_latest(conn, self.mindmap_id)
        if not snap:
            return
        self.snap = snap

        # Score every cached stock; pick pairs with meaningful score difference.
        recs = rank_from_db(conn, snap, top_k=None)
        if len(recs) < 4:
            return
        # Buckets: top, middle, bottom
        top = recs[: len(recs) // 3]
        mid = recs[len(recs) // 3 : 2 * len(recs) // 3]
        bot = recs[2 * len(recs) // 3 :]
        rng = random.Random(42)

        def pair_from(bucket_a, bucket_b):
            a = rng.choice(bucket_a)
            b = rng.choice(bucket_b)
            return _Round(
                left=a.ticker, right=b.ticker,
                left_score=a.score, right_score=b.score,
            )

        seen: set[tuple[str, str]] = set()
        for src_a, src_b in [(top, bot), (top, mid), (mid, bot), (top, mid), (top, bot)]:
            for _ in range(5):
                r = pair_from(src_a, src_b)
                # randomize side
                if rng.random() < 0.5:
                    r = _Round(left=r.right, right=r.left,
                               left_score=r.right_score, right_score=r.left_score)
                key = tuple(sorted([r.left, r.right]))
                if key in seen or r.left == r.right:
                    continue
                seen.add(key)
                self.rounds.append(r)
                break

    def _card(self, ticker: str, key_label: str, *, classes: str = "vs-card") -> Vertical:
        conn = self.app.conn  # type: ignore[attr-defined]
        stock = stocks_repo.get_stock(conn, ticker)
        name = stock.name if stock else ticker
        sector = stock.sector if stock else ""
        hist = history_for(ticker, days=30)
        chart = render_candles(hist, rows=6, width=36) if hist else ""
        return Vertical(
            Static(f"[bold]{name}[/]", classes="vs-title"),
            Static(f"[dim]{sector}[/]", classes="vs-sub"),
            Static(chart),
            Static(f"[#5e81ac]Press {key_label}[/]", classes="vs-key"),
            classes=classes,
        )

    def _render_round(self) -> None:
        # Re-create the row
        for c in list(self._row.children):
            c.remove()
        if self.results_mode:
            self._render_results()
            return
        if self.idx >= len(self.rounds):
            self._render_results()
            return
        r = self.rounds[self.idx]
        self.query_one("#q", Static).update("Which would you rather own?")
        self.query_one("#progress", Static).update(
            f"Match {self.idx + 1} of {len(self.rounds)}"
        )
        self._row.mount(self._card(r.left, "←"))
        self._row.mount(self._card(r.right, "→"))
        self.query_one("#verdict", Static).update("")

    def action_pick_left(self) -> None: self._record("left")
    def action_pick_right(self) -> None: self._record("right")

    def _record(self, side: str) -> None:
        if self.results_mode or self.idx >= len(self.rounds):
            return
        r = self.rounds[self.idx]
        r.user_pick = side
        matched = side == r.style_winner
        emoji = "[#98c379]Match with your style.[/]" if matched else \
                "[#e5c07b]Your style would have leaned the other way.[/]"
        self.query_one("#verdict", Static).update(
            f"  {emoji}   [dim](press space for next)[/]"
        )
        # Advance after a beat so the user can read the verdict
        self.set_timer(1.2, self._advance)

    def _advance(self) -> None:
        if self.results_mode:
            return
        self.idx += 1
        if self.idx >= len(self.rounds):
            self.results_mode = True
        self._render_round()

    def action_next(self) -> None:
        if self.results_mode:
            self.action_back()
        else:
            self._advance()

    def _render_results(self) -> None:
        agreed = sum(1 for r in self.rounds if r.user_pick == r.style_winner)
        n = len(self.rounds)
        pct = agreed / max(n, 1)
        if pct >= 0.8:
            verdict = "You and your style are basically the same person."
        elif pct >= 0.6:
            verdict = "Your gut mostly agrees with your saved style."
        elif pct >= 0.4:
            verdict = "Mixed — your gut and your style disagree about as often as they agree."
        else:
            verdict = "Your gut leans differently than your saved style. Want to redo the quiz?"
        self.query_one("#q", Static).update("Vibe Check — Results")
        self.query_one("#progress", Static).update("")
        self.query_one("#verdict", Static).update(
            f"\n[bold]{agreed} of {n}[/] picks agreed with your style.\n\n"
            f"{verdict}\n\n"
            f"[dim]Press Esc to return home.[/]"
        )

    def action_back(self) -> None:
        self.app.pop_screen()
