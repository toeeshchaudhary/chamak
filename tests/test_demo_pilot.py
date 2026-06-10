from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_welcome_screen_loads_demo():
    """First-run welcome screen with `2` should seed demo data."""
    from chamak.storage.migrator import migrate
    migrate()
    from chamak.tui.app import ChamakApp
    from chamak.storage.db import connect
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        # splash → welcome (empty db) or dashboard (already-seeded)
        name = app.screen.__class__.__name__
        assert name in {"WelcomeScreen", "DashboardScreen"}
        if name == "WelcomeScreen":
            await pilot.press("1")   # 1 = "Try with sample data" (demo)
            await pilot.pause(1.0)
            assert app.screen.__class__.__name__ == "DashboardScreen"
        # Verify demo data is now in db
        c = connect()
        try:
            from chamak.storage.repositories import mindmaps as mm_repo, stocks as stocks_repo
            assert len(mm_repo.list_all(c)) >= 1
            assert len(stocks_repo.list_stocks(c)) >= 1
        finally:
            c.close()


@pytest.mark.asyncio
async def test_demo_pilot_starts():
    from chamak.storage.migrator import migrate
    migrate()
    from chamak.demo.seeder import seed
    seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="demo_pilot")
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        # We should be on the autopilot or a child scene by now
        names = {s.__class__.__name__ for s in app.screen_stack}
        assert "DemoPilotScreen" in names
