from __future__ import annotations

import re

import pytest

from chamak.demo.mindmaps import VALUE, build_snapshot
from chamak.tui.widgets.flowchart import (
    COLOR_RULE_FAIL,
    COLOR_RULE_MATCH,
    render_flowchart,
)


def _strip_markup(s: str) -> str:
    return re.sub(r"\[/?[^\]]*\]", "", s)


def test_flowchart_renders_root_label():
    snap = build_snapshot(VALUE)
    out = _strip_markup(render_flowchart(snap, max_width=120))
    assert "Value Investor" in out


def test_flowchart_renders_belief_boxes():
    snap = build_snapshot(VALUE)
    out = _strip_markup(render_flowchart(snap, max_width=140))
    # Each Value Investor belief label should appear
    expected = [
        "Margin of safety", "Avoid leverage", "Earn on capital",
        "Cash flow is real", "Long-term operator",
    ]
    for word in expected:
        # account for line-wrapping inside boxes by checking first word
        head = word.split()[0]
        assert head in out, f"missing belief snippet: {head}"


def test_flowchart_renders_connectors():
    """The branching characters should appear in the output."""
    snap = build_snapshot(VALUE)
    out = _strip_markup(render_flowchart(snap, max_width=140))
    assert "│" in out
    assert "┌" in out and "┐" in out
    # branch row should contain horizontal segments
    assert "─" in out


def test_flowchart_highlights_matched_and_failed_rules():
    snap = build_snapshot(VALUE)
    statuses = {snap.rules[0].id: "match", snap.rules[1].id: "fail"}
    out = render_flowchart(snap, rule_status=statuses, max_width=120)
    assert COLOR_RULE_MATCH in out
    assert COLOR_RULE_FAIL in out


def test_flowchart_handles_empty_style():
    from chamak.core.models import MindMap, MindMapSnapshot
    snap = MindMapSnapshot(mindmap=MindMap(name="Empty"), nodes=[], edges=[], rules=[])
    out = render_flowchart(snap)
    assert "empty" in out.lower() or "no" in out.lower()


@pytest.mark.asyncio
async def test_flowchart_view_screen_mounts():
    from chamak.storage.migrator import migrate
    from chamak.demo.seeder import seed
    from chamak.storage.repositories import mindmaps as mm_repo
    from chamak.tui.app import ChamakApp
    from chamak.tui.screens.flowchart_view import FlowchartViewScreen

    migrate()
    seed()
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        mm = mm_repo.list_all(app.conn)[0]
        app.push_screen(FlowchartViewScreen(mindmap_id=mm.id))
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "FlowchartViewScreen"
