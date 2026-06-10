"""Mount every screen in isolation and confirm it composes without error.

Catches:
  - attribute-shadowing (`self.tree`, `self.name`, etc. that collide with DOMNode properties)
  - missing imports / typos in compose()
  - reactives that reference unset attributes during mount
"""

from __future__ import annotations

import pytest


def _seed():
    from chamak.storage.migrator import migrate
    migrate()
    from chamak.demo.seeder import seed
    seed()


@pytest.mark.asyncio
async def test_dashboard_mounts():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        assert app.screen.__class__.__name__ == "DashboardScreen"


@pytest.mark.asyncio
async def test_library_mounts():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        app.action_go_library()
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "LibraryScreen"


@pytest.mark.asyncio
async def test_editor_mounts():
    """Regression: editor used `self.tree` which collided with DOMNode.tree."""
    _seed()
    from chamak.tui.app import ChamakApp
    from chamak.storage.repositories import mindmaps as mm_repo
    from chamak.tui.screens.editor import EditorScreen
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        mm = mm_repo.list_all(app.conn)[0]
        app.push_screen(EditorScreen(mindmap_id=mm.id))
        await pilot.pause(0.4)
        assert app.screen.__class__.__name__ == "EditorScreen"


@pytest.mark.asyncio
async def test_history_mounts():
    _seed()
    from chamak.tui.app import ChamakApp
    from chamak.storage.repositories import mindmaps as mm_repo
    from chamak.tui.screens.history import HistoryScreen
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        mm = mm_repo.list_all(app.conn)[0]
        app.push_screen(HistoryScreen(mindmap_id=mm.id))
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "HistoryScreen"


@pytest.mark.asyncio
async def test_recommendations_mounts():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        app.action_go_recs()
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "RecommendationsScreen"


@pytest.mark.asyncio
async def test_stock_detail_mounts():
    _seed()
    from chamak.storage.repositories import mindmaps as mm_repo
    from chamak.tui.app import ChamakApp
    from chamak.tui.screens.stock_detail import StockDetailScreen
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        mm = mm_repo.list_all(app.conn)[0]
        app.push_screen(StockDetailScreen(ticker="TCS", mindmap_id=mm.id))
        await pilot.pause(0.4)
        assert app.screen.__class__.__name__ == "StockDetailScreen"


@pytest.mark.asyncio
async def test_scanner_mounts():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        app.action_go_scanner()
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "ScannerScreen"


@pytest.mark.asyncio
async def test_portfolio_mounts():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        app.action_go_portfolio()
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "PortfolioScreen"


@pytest.mark.asyncio
async def test_news_mounts():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        app.action_go_news()
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "NewsScreen"


@pytest.mark.asyncio
async def test_interview_mounts():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        app.action_go_interview()
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "InterviewScreen"


@pytest.mark.asyncio
async def test_settings_mounts():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        app.action_go_settings()
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "SettingsScreen"


@pytest.mark.asyncio
async def test_help_mounts():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        app.action_help()
        await pilot.pause(0.3)
        assert app.screen.__class__.__name__ == "HelpScreen"


@pytest.mark.asyncio
async def test_welcome_mounts_on_empty_db():
    from chamak.storage.migrator import migrate
    migrate()
    # No seed — should land on welcome
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        assert app.screen.__class__.__name__ == "WelcomeScreen"


@pytest.mark.asyncio
async def test_palette_and_search_modals_mount():
    _seed()
    from chamak.tui.app import ChamakApp
    app = ChamakApp(start_screen="splash", force_mode="advanced")
    async with app.run_test() as pilot:
        await pilot.pause(1.6)
        app.action_show_palette()
        await pilot.pause(0.2)
        assert app.screen.__class__.__name__ == "PaletteModal"
        app.pop_screen()
        await pilot.pause(0.1)
        app.action_show_search()
        await pilot.pause(0.2)
        assert app.screen.__class__.__name__ == "SearchModal"
