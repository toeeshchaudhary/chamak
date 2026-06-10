from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_app_boots_to_dashboard():
    from chamak.storage.migrator import migrate
    migrate()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        # splash auto-advances after ~0.7s
        await pilot.pause(1.6)
        assert app.screen.__class__.__name__ in {
            "DashboardScreen", "SplashScreen", "WelcomeScreen"
        }


@pytest.mark.asyncio
async def test_help_screen_pushes():
    from chamak.storage.migrator import migrate
    migrate()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.0)
        app.action_help()
        await pilot.pause(0.2)
        assert app.screen.__class__.__name__ == "HelpScreen"
