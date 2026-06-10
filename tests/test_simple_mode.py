"""Smoke tests for Simple mode + interactive demo."""

from __future__ import annotations

import re

import pytest


def _seed():
    from chamak.storage.migrator import migrate
    migrate()
    from chamak.demo.seeder import seed
    seed()


def test_candle_chart_renders():
    from chamak.demo.prices import history_for
    from chamak.tui.widgets.candle import render_candles, render_sparkline
    hist = history_for("TCS", days=30)
    assert len(hist) == 30
    out = render_candles(hist, rows=8, width=40)
    plain = re.sub(r"\[/?[^\]]*\]", "", out)
    assert "█" in plain or "━" in plain
    spark = render_sparkline([c.close for c in hist], width=20)
    assert spark


def test_style_builder_produces_runnable_snapshot():
    from chamak.tui.simple.style_builder import build_snapshot
    snap = build_snapshot({"vibe": "balanced", "like": "steady", "price": "fair"})
    assert snap.mindmap.archetype
    assert len(snap.nodes) >= 4   # root + 3 beliefs
    assert len(snap.rules) >= 3


def test_friendly_explainer():
    from chamak.tui.simple.explain_friendly import (
        friendly_concerns, friendly_reasons, headline_for, stars,
    )
    assert stars(0.85).count("★") == 5
    assert stars(0.3).count("★") == 2
    assert "strong" in headline_for(0.85).lower() or "fit" in headline_for(0.85).lower()
    assert "probably not" in headline_for(0.5, hard_fail=True).lower()


@pytest.mark.asyncio
async def test_simple_app_boots_to_welcome_on_empty_db():
    from chamak.storage.migrator import migrate
    migrate()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(force_mode="simple")
    async with app.run_test() as pilot:
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "SimpleWelcomeScreen"


@pytest.mark.asyncio
async def test_simple_app_boots_to_home_when_styles_exist():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(force_mode="simple")
    async with app.run_test() as pilot:
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "SimpleHomeScreen"


@pytest.mark.asyncio
async def test_quiz_completes_and_lands_on_home():
    from chamak.storage.migrator import migrate
    migrate()  # no seed; quiz should seed stocks itself
    from chamak.tui.app import ChamakApp
    from chamak.tui.simple.quiz import SimpleQuizScreen
    app = ChamakApp(force_mode="simple")
    async with app.run_test() as pilot:
        await pilot.pause(0.3)
        scr = SimpleQuizScreen()
        app.push_screen(scr)
        await pilot.pause(0.3)
        # Drive the quiz programmatically — pilot.press is flaky on number keys
        # in the test pilot, and what we want to verify is the transition.
        scr._pick(0)
        await pilot.pause(0.1)
        scr._pick(0)
        await pilot.pause(0.1)
        scr._pick(0)
        await pilot.pause(0.5)
        assert app.screen.__class__.__name__ == "SimpleHomeScreen"


@pytest.mark.asyncio
async def test_stock_card_carousel_navigates():
    _seed()
    from chamak.storage.repositories import mindmaps as mm_repo
    from chamak.tui.app import ChamakApp
    from chamak.tui.simple.stock_card import SimpleStockCardScreen
    app = ChamakApp(force_mode="simple")
    async with app.run_test() as pilot:
        await pilot.pause(0.3)
        mm = mm_repo.list_all(app.conn)[0]
        scr = SimpleStockCardScreen(mindmap_id=mm.id)
        app.push_screen(scr)
        await pilot.pause(0.4)
        assert app.screen.__class__.__name__ == "SimpleStockCardScreen"
        assert len(scr.recs) > 0
        first = scr.idx
        scr.action_next()
        await pilot.pause(0.2)
        assert scr.idx != first
        scr.action_prev()
        await pilot.pause(0.2)
        assert scr.idx == first


@pytest.mark.asyncio
async def test_vibe_check_records_picks():
    _seed()
    from chamak.storage.repositories import mindmaps as mm_repo
    from chamak.tui.app import ChamakApp
    from chamak.tui.simple.vibe_check import VibeCheckScreen
    app = ChamakApp(force_mode="simple")
    async with app.run_test() as pilot:
        await pilot.pause(0.3)
        mm = mm_repo.list_all(app.conn)[0]
        app.push_screen(VibeCheckScreen(mindmap_id=mm.id))
        await pilot.pause(0.4)
        scr = app.screen
        assert scr.__class__.__name__ == "VibeCheckScreen"
        if scr.rounds:
            await pilot.press("left")
            await pilot.pause(0.1)
            assert scr.rounds[0].user_pick == "left"


@pytest.mark.asyncio
async def test_simple_autopilot_runs():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="simple_demo", force_mode="simple")
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        # The autopilot screen should be at the bottom of the stack
        names = [s.__class__.__name__ for s in app.screen_stack]
        assert "SimpleAutopilotScreen" in names


def test_mode_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    import importlib
    import chamak.config as cfg
    importlib.reload(cfg)
    # Default
    assert cfg.get_mode() == "simple"
    cfg.set_mode("advanced")
    assert cfg.get_mode() == "advanced"
    cfg.set_mode("simple")
    assert cfg.get_mode() == "simple"
