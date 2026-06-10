from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from chamak.graph.diff import diff
from chamak.storage.repositories import versions as ver_repo


class HistoryScreen(Screen):
    BINDINGS = [
        Binding("d", "diff_prev", "Diff vs prev"),
        Binding("r", "restore", "Restore"),
    ]

    DEFAULT_CSS = """
    #cols { height: 1fr; }
    #left { width: 50%; }
    #right { width: 1fr; padding-left: 2; }
    """

    def __init__(self, mindmap_id: str) -> None:
        super().__init__()
        self.mindmap_id = mindmap_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("[bold]Version History[/]", classes="title")
        with Horizontal(id="cols"):
            with Vertical(id="left"):
                self.table = DataTable(cursor_type="row")
                self.table.add_columns("v", "When", "Message")
                yield self.table
            with Vertical(id="right"):
                yield Static("[bold]Diff[/]", classes="panel-title")
                self.diff_view = Static("Pick a version and press d to diff vs previous.", classes="panel")
                yield self.diff_view
        yield Footer()

    def on_mount(self) -> None:
        self._versions = ver_repo.list_versions(self.app.conn, self.mindmap_id)  # type: ignore[attr-defined]
        for v in self._versions:
            self.table.add_row(str(v["version"]), v["created_at"][:19].replace("T", " "), v["message"])

    def _selected_version(self) -> int | None:
        try:
            return int(self._versions[self.table.cursor_row]["version"])
        except (IndexError, AttributeError):
            return None

    def action_diff_prev(self) -> None:
        v = self._selected_version()
        if v is None or v <= 1:
            self.diff_view.update("No previous version to diff against.")
            return
        conn = self.app.conn  # type: ignore[attr-defined]
        new = ver_repo.load_version(conn, self.mindmap_id, v)
        old = ver_repo.load_version(conn, self.mindmap_id, v - 1)
        if not (new and old):
            self.diff_view.update("Version load failed.")
            return
        d = diff(old, new)
        lines = [f"[bold]v{v-1} → v{v}[/]   {d.summary()}", ""]
        if d.added_nodes:
            lines.append("[green]+ nodes[/]")
            for n in d.added_nodes:
                lines.append(f"  + {n.label}  [dim]({n.type.value})[/]")
        if d.removed_nodes:
            lines.append("[red]- nodes[/]")
            for n in d.removed_nodes:
                lines.append(f"  - {n.label}")
        if d.modified_nodes:
            lines.append("[yellow]~ nodes[/]")
            for old_n, new_n in d.modified_nodes:
                lines.append(f"  ~ {old_n.label}  →  {new_n.label}")
        if d.added_rules:
            lines.append("[green]+ rules[/]")
            for r in d.added_rules:
                lines.append(f"  + {r.text}")
        if d.removed_rules:
            lines.append("[red]- rules[/]")
            for r in d.removed_rules:
                lines.append(f"  - {r.text}")
        if d.modified_rules:
            lines.append("[yellow]~ rules[/]")
            for old_r, new_r in d.modified_rules:
                lines.append(f"  ~ {old_r.text}  →  {new_r.text}")
        self.diff_view.update("\n".join(lines) or "No differences.")

    def action_restore(self) -> None:
        v = self._selected_version()
        if v is None:
            return
        conn = self.app.conn  # type: ignore[attr-defined]
        snap = ver_repo.load_version(conn, self.mindmap_id, v)
        if not snap:
            return
        from chamak.storage.repositories import mindmaps as mm_repo
        new_version = ver_repo.save_snapshot(conn, snap, message=f"restore from v{v}")
        mm_repo.replace_graph(conn, self.mindmap_id, snap.nodes, snap.edges, snap.rules)
        mm = mm_repo.get(conn, self.mindmap_id)
        if mm:
            mm.current_version = new_version.version
            mm_repo.update_meta(conn, mm)
        self.notify(f"Restored as v{new_version.version}.", severity="information")
