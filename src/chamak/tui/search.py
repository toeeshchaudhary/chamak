from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, ListItem, ListView, Static

from chamak.storage.repositories import mindmaps as mm_repo, stocks as stocks_repo


class SearchModal(ModalScreen[None]):
    DEFAULT_CSS = """
    SearchModal { align: center middle; }
    #box { background: #1a1a1c; padding: 1; width: 70; border: tall #2a2a2c; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="box"):
            yield Static("[bold]Search[/]   (mind maps + tickers)", classes="panel-title")
            self.search_input = Input(placeholder="query…")
            yield self.search_input
            self.lv = ListView(*self._items_for(""))
            yield self.lv

    def on_mount(self) -> None:
        self.set_focus(self.search_input)

    def _items_for(self, q: str) -> list[ListItem]:
        q = q.lower()
        items: list[ListItem] = []
        conn = self.app.conn  # type: ignore[attr-defined]
        for m in mm_repo.list_all(conn, include_archived=True):
            if q in m.name.lower() or q in m.archetype.lower():
                items.append(
                    ListItem(Static(f"[mind-map] {m.name}  [dim]{m.archetype}[/]"), id=f"mm-{m.id}")
                )
        for s in stocks_repo.list_stocks(conn):
            if q in s.ticker.lower() or q in s.name.lower():
                items.append(
                    ListItem(Static(f"[stock]    {s.ticker}  [dim]{s.name}[/]"), id=f"st-{s.ticker}")
                )
        return items

    def _populate(self, q: str) -> None:
        for c in list(self.lv.children):
            c.remove()
        for item in self._items_for(q):
            self.lv.mount(item)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._populate(event.value)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        self.dismiss()
        if item_id.startswith("mm-"):
            from chamak.tui.screens.editor import EditorScreen
            self.app.push_screen(EditorScreen(mindmap_id=item_id.removeprefix("mm-")))
        elif item_id.startswith("st-"):
            from chamak.storage.repositories import mindmaps as mm_repo
            mms = mm_repo.list_all(self.app.conn)  # type: ignore[attr-defined]
            if not mms:
                return
            from chamak.tui.screens.stock_detail import StockDetailScreen
            self.app.push_screen(
                StockDetailScreen(ticker=item_id.removeprefix("st-"), mindmap_id=mms[0].id)
            )


def open_search(app) -> None:
    app.push_screen(SearchModal())
