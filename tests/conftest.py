from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_xdg(monkeypatch, tmp_path: Path):
    """Force every test to write into its own XDG dirs so we never touch
    the user's real db."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    # platformdirs caches results; clear any module-level cache by re-importing
    import importlib
    import chamak.config as cfg
    importlib.reload(cfg)
    yield


@pytest.fixture()
def conn():
    from chamak.storage.db import connect
    from chamak.storage.migrator import migrate
    migrate()
    c = connect()
    yield c
    c.close()
