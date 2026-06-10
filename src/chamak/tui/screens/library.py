from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from chamak.core.models import MindMap
from chamak.storage.repositories import mindmaps as mm_repo, versions as ver_repo


class LibraryScreen(Screen):
    BINDINGS = [
        Binding("n", "new", "New"),
        Binding("d", "duplicate", "Duplicate"),
        Binding("a", "archive_toggle", "Archive"),
        Binding("e", "edit", "Edit"),
        Binding("V", "view", "View flowchart"),
        Binding("v", "versions", "Versions"),
        Binding("enter", "view", "View"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("[bold]Your Investing Styles[/]", classes="title")
            yield Static(
                "[bold]Enter[/] view as flowchart   [bold]e[/] edit   [bold]n[/] new   "
                "[bold]d[/] duplicate   [bold]a[/] archive   [bold]v[/] versions",
                classes="dim",
            )
            self.table = DataTable(cursor_type="row")
            self.table.add_columns("Name", "Style", "v", "Updated", "Status")
            yield self.table
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_rows()

    def refresh_rows(self) -> None:
        self.table.clear()
        rows = mm_repo.list_all(self.app.conn, include_archived=True)  # type: ignore[attr-defined]
        self._row_ids: list[str] = []
        for m in rows:
            self.table.add_row(
                m.name,
                m.archetype or "—",
                str(m.current_version),
                m.updated_at.strftime("%Y-%m-%d %H:%M"),
                "archived" if m.archived else "active",
            )
            self._row_ids.append(m.id)
        if rows:
            self.table.move_cursor(row=0)

    def _selected_id(self) -> str | None:
        try:
            row = self.table.cursor_row
            return self._row_ids[row]
        except (IndexError, AttributeError):
            return None

    def action_new(self) -> None:
        from chamak.tui.screens.interview import InterviewScreen
        self.app.push_screen(InterviewScreen(name="New Mind Map"))

    def action_edit(self) -> None:
        mm_id = self._selected_id()
        if not mm_id:
            return
        from chamak.tui.screens.editor import EditorScreen
        self.app.push_screen(EditorScreen(mindmap_id=mm_id))

    def action_view(self) -> None:
        mm_id = self._selected_id()
        if not mm_id:
            return
        from chamak.tui.screens.flowchart_view import FlowchartViewScreen
        self.app.push_screen(FlowchartViewScreen(mindmap_id=mm_id))

    def action_versions(self) -> None:
        mm_id = self._selected_id()
        if not mm_id:
            return
        from chamak.tui.screens.history import HistoryScreen
        self.app.push_screen(HistoryScreen(mindmap_id=mm_id))

    def action_archive_toggle(self) -> None:
        mm_id = self._selected_id()
        if not mm_id:
            return
        mm = mm_repo.get(self.app.conn, mm_id)  # type: ignore[attr-defined]
        if mm:
            mm_repo.archive(self.app.conn, mm.id, archived=not mm.archived)  # type: ignore[attr-defined]
            self.refresh_rows()

    def action_duplicate(self) -> None:
        mm_id = self._selected_id()
        if not mm_id:
            return
        conn = self.app.conn  # type: ignore[attr-defined]
        src = mm_repo.get(conn, mm_id)
        snap = ver_repo.load_latest(conn, mm_id)
        if not (src and snap):
            return
        new_mm = MindMap(
            name=f"{src.name} (copy)",
            type=src.type,
            archetype=src.archetype,
            description=src.description,
        )
        # rebuild snapshot with the new mindmap id but same graph
        new_snap = snap.model_copy()
        new_snap.mindmap = new_mm
        mm_repo.insert(conn, new_mm)
        version = ver_repo.save_snapshot(conn, new_snap, message="duplicated")
        mm_repo.replace_graph(conn, new_mm.id, new_snap.nodes, new_snap.edges, new_snap.rules)
        new_mm.current_version = version.version
        mm_repo.update_meta(conn, new_mm)
        self.refresh_rows()
