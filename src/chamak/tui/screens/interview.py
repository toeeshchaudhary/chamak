from __future__ import annotations


from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, ListItem, ListView, Static

from chamak.interview.assistant import best_available
from chamak.interview.engine import InterviewEngine
from chamak.storage.repositories import mindmaps as mm_repo, versions as ver_repo


class InterviewScreen(Screen):
    BINDINGS = [
        Binding("enter", "submit", "Submit"),
        Binding("ctrl+s", "skip", "Skip"),
    ]

    DEFAULT_CSS = """
    InterviewScreen { layout: vertical; }
    #q { padding: 1 2; }
    #q-text { color: #e6e6e6; text-style: bold; }
    #progress { color: #707070; }
    #input-area { padding: 1 2; height: auto; }
    """

    def __init__(self, name: str) -> None:
        super().__init__()
        self.engine = InterviewEngine(assistant=best_available())
        self.mm_name = name

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="q"):
            yield Static("", id="progress")
            yield Static("", id="q-text")
            with VerticalScroll(id="input-area"):
                yield Static("", id="placeholder")
        with Horizontal():
            yield Button("Submit (Enter)", id="submit", variant="primary")
            yield Button("Skip", id="skip")
        yield Footer()

    def on_mount(self) -> None:
        self._render_question()

    def _render_question(self) -> None:
        area = self.query_one("#input-area", VerticalScroll)
        for w in list(area.children):
            w.remove()
        q = self.engine.current()
        if q is None:
            self._finish()
            return
        i, total = self.engine.progress()
        self.query_one("#progress", Static).update(f"Question {i+1} of {total}")
        self.query_one("#q-text", Static).update(q["text"])
        kind = q["kind"]
        if kind == "choice":
            self._lv = ListView(*[ListItem(Static(o["label"]), id=f"opt-{o['value']}") for o in q["options"]])
            area.mount(self._lv)
        elif kind == "multi":
            area.mount(Static("[dim]Enter comma-separated indices.[/]"))
            for i, o in enumerate(q["options"], 1):
                area.mount(Static(f"  {i}. {o['label']}"))
            self._input = Input(placeholder="e.g. 1,3")
            area.mount(self._input)
        elif kind == "scale":
            lo, hi = q["range"]
            self._input = Input(placeholder=f"Integer {lo}-{hi}")
            area.mount(self._input)
        elif kind == "number":
            self._input = Input(placeholder="Number")
            area.mount(self._input)
        else:  # text
            self._input = Input(placeholder="Type your answer (Enter to submit)")
            area.mount(self._input)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            self.action_submit()
        elif event.button.id == "skip":
            self.action_skip()

    def action_submit(self) -> None:
        q = self.engine.current()
        if q is None:
            self._finish()
            return
        kind = q["kind"]
        try:
            if kind == "choice":
                item = self._lv.highlighted_child
                if item is None:
                    return
                value = item.id.removeprefix("opt-") if item.id else None
                if value is None:
                    return
            elif kind == "multi":
                idxs = [int(x.strip()) - 1 for x in self._input.value.split(",") if x.strip()]
                value = [q["options"][i]["value"] for i in idxs]
            elif kind == "scale":
                value = int(self._input.value)
            elif kind == "number":
                value = float(self._input.value)
            else:
                value = self._input.value
        except (ValueError, IndexError, AttributeError):
            self.notify("Couldn't parse answer.", severity="warning")
            return
        self.engine.answer(value)
        if self.engine.done():
            self._finish()
        else:
            self._render_question()

    def action_skip(self) -> None:
        self.engine.skip()
        if self.engine.done():
            self._finish()
        else:
            self._render_question()

    def _finish(self) -> None:
        snap = self.engine.build_snapshot(self.mm_name)
        conn = self.app.conn  # type: ignore[attr-defined]
        mm_repo.insert(conn, snap.mindmap)
        version = ver_repo.save_snapshot(conn, snap, message="initial from interview")
        mm_repo.replace_graph(conn, snap.mindmap.id, snap.nodes, snap.edges, snap.rules)
        snap.mindmap.current_version = version.version
        mm_repo.update_meta(conn, snap.mindmap)
        self.notify(
            f"Saved '{snap.mindmap.name}' — archetype {snap.mindmap.archetype}, "
            f"{len(snap.rules)} rules.",
            severity="information",
        )
        from chamak.tui.screens.editor import EditorScreen
        self.app.switch_screen(EditorScreen(mindmap_id=snap.mindmap.id))
