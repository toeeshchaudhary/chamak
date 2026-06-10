"""End-to-end 'is the demo recordable right now?' test.

Run this before screen recording:

    uv run pytest tests/test_demo_recording.py -v

It seeds the demo data, scores against every prebuilt mind map, asserts the
top-line numbers match the script (so the screen recording looks correct),
and finally boots the TUI autopilot through every scene.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_full_demo_recording_pass(tmp_path, monkeypatch):
    """Single-shot rehearsal of the screen-recording flow."""
    # Fresh XDG home so nothing leaks.
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    import importlib
    import chamak.config as cfg
    importlib.reload(cfg)

    # 1. Seed demo data
    from chamak.demo.seeder import seed
    rep = seed()
    assert rep.stocks >= 30, "demo should ship ≥30 stocks"
    assert rep.mindmaps == 3
    assert rep.portfolios == 1
    assert rep.news >= 10

    # 2. Each mind map scores reasonably
    from chamak.storage.db import connect
    from chamak.storage.repositories import mindmaps as mm_repo, versions as ver_repo
    from chamak.recommendation.engine import rank_from_db
    conn = connect()
    try:
        names = ["Value Investor", "Quality Compounder", "Dividend Income"]
        for name in names:
            mm = next(m for m in mm_repo.list_all(conn) if m.name == name)
            snap = ver_repo.load_latest(conn, mm.id)
            assert snap is not None
            recs = rank_from_db(conn, snap, top_k=3)
            assert recs, f"{name} produced no recs"
            assert recs[0].score > 0.6, (
                f"top rec for {name} is {recs[0].ticker} at {recs[0].score:.0%} "
                f"— demo will look bad on camera"
            )

        # 3. Dividend Income should top with high-yield stocks
        div = next(m for m in mm_repo.list_all(conn) if m.name == "Dividend Income")
        snap = ver_repo.load_latest(conn, div.id)
        assert snap is not None
        recs = rank_from_db(conn, snap, top_k=5)
        top5 = {r.ticker for r in recs}
        high_yielders = {"COALINDIA", "VEDL", "ONGC", "HINDPETRO", "POWERGRID", "ITC"}
        assert top5 & high_yielders, (
            f"dividend mind map didn't surface any high-yielder; got {top5}"
        )
    finally:
        conn.close()

    # 4. TUI autopilot boots and walks every scene without exceptions
    from chamak.tui.app import ChamakApp
    from chamak.tui.screens.demo_pilot import _scenes
    app = ChamakApp(start_screen="demo_pilot")
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        assert any(s.__class__.__name__ == "DemoPilotScreen" for s in app.screen_stack)
        # Walk every scene by pressing → so we exercise every screen the demo touches
        for _ in range(len(_scenes()) + 1):
            await pilot.press("right")
            await pilot.pause(0.25)
        # Pause and resume
        await pilot.press("space")
        await pilot.pause(0.2)
        await pilot.press("space")
        await pilot.pause(0.2)
