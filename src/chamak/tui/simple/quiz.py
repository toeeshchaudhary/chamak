"""Simple-mode quiz screen — 3 picture-card questions, plain English."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from chamak.tui.simple.quiz_data import QUESTIONS


class SimpleQuizScreen(Screen):
    BINDINGS = [
        Binding("1", "pick_0", "1"),
        Binding("2", "pick_1", "2"),
        Binding("3", "pick_2", "3"),
        Binding("escape", "back", "Back"),
    ]

    DEFAULT_CSS = """
    SimpleQuizScreen { background: #0a0a0d; }
    #wrap { padding: 1 4; }
    #progress { color: #5a5a5a; text-align: center; }
    #qtext {
        color: #ffffff;
        text-style: bold;
        text-align: center;
        padding: 1 0 2 0;
    }
    #cards-text { padding: 1 0; }
    #hint {
        color: #5a5a5a;
        text-align: center;
        padding: 2 0 0 0;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.idx = 0
        self.answers: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="wrap"):
            yield Static(" ", id="progress")
            yield Static(" ", id="qtext")
            yield Static(" ", id="cards-text")
            yield Static(
                "Press [bold]1[/], [bold]2[/], or [bold]3[/] to choose. Esc to go back.",
                id="hint",
            )
        yield Footer()

    def on_mount(self) -> None:
        self._render_q()

    def _render_q(self) -> None:
        if self.idx >= len(QUESTIONS):
            self._finish()
            return
        q = QUESTIONS[self.idx]
        self.query_one("#progress", Static).update(
            f"Question {self.idx + 1} of {len(QUESTIONS)}"
        )
        self.query_one("#qtext", Static).update(q.text)

        # Render the three "cards" as a single Static, side-by-side.
        # Building them as text panels gives us reliable layout in any
        # terminal width.
        lines: list[str] = []
        for i, choice in enumerate(q.choices):
            num = i + 1
            lines.append(
                f"  [bold #5e81ac]{num}.[/]  [bold #88c0d0]{choice.icon}[/]   "
                f"[bold]{choice.title}[/]"
            )
            lines.append(f"      [#a0a0a0]{choice.blurb}[/]")
            lines.append("")
        self.query_one("#cards-text", Static).update("\n".join(lines))

    def action_pick_0(self) -> None: self._pick(0)
    def action_pick_1(self) -> None: self._pick(1)
    def action_pick_2(self) -> None: self._pick(2)

    def _pick(self, i: int) -> None:
        if self.idx >= len(QUESTIONS):
            return
        q = QUESTIONS[self.idx]
        if not (0 <= i < len(q.choices)):
            return
        self.answers[q.id] = q.choices[i].key
        self.idx += 1
        self._render_q()

    def action_back(self) -> None:
        if self.idx == 0:
            from chamak.tui.simple.welcome import SimpleWelcomeScreen
            self.app.switch_screen(SimpleWelcomeScreen())
            return
        self.idx = max(0, self.idx - 1)
        self._render_q()

    def _finish(self) -> None:
        from chamak.demo.seeder import _seed_news, _seed_stocks
        from chamak.storage.repositories import mindmaps as mm_repo, stocks as stocks_repo, versions as ver_repo
        from chamak.tui.simple.style_builder import build_snapshot

        snap = build_snapshot(self.answers)
        conn = self.app.conn  # type: ignore[attr-defined]
        mm_repo.insert(conn, snap.mindmap)
        v = ver_repo.save_snapshot(conn, snap, message="from quick quiz")
        mm_repo.replace_graph(conn, snap.mindmap.id, snap.nodes, snap.edges, snap.rules)
        snap.mindmap.current_version = v.version
        mm_repo.update_meta(conn, snap.mindmap)

        if not stocks_repo.list_stocks(conn):
            _seed_stocks(conn)
            _seed_news(conn)

        from chamak.tui.simple.home import SimpleHomeScreen
        self.app.switch_screen(SimpleHomeScreen(mindmap_id=snap.mindmap.id))
