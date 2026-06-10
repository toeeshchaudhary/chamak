from __future__ import annotations

import logging
import logging.handlers
import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_data_dir, user_cache_dir, user_log_dir

APP_NAME = "chamak"


@dataclass(frozen=True)
class Paths:
    data: Path
    cache: Path
    logs: Path
    db: Path
    ohlcv_cache: Path
    fundamentals_cache: Path


def paths() -> Paths:
    data = Path(user_data_dir(APP_NAME))
    cache = Path(user_cache_dir(APP_NAME))
    logs = Path(user_log_dir(APP_NAME))
    for p in (data, cache, logs):
        p.mkdir(parents=True, exist_ok=True)
    ohlcv = cache / "ohlcv"
    fund = cache / "fundamentals"
    ohlcv.mkdir(exist_ok=True)
    fund.mkdir(exist_ok=True)
    return Paths(
        data=data,
        cache=cache,
        logs=logs,
        db=data / "chamak.db",
        ohlcv_cache=ohlcv,
        fundamentals_cache=fund,
    )


def openrouter_key() -> str | None:
    return os.environ.get("OPENROUTER_API_KEY")


# ---- settings (mode preference, etc.) ----

def _settings_path() -> Path:
    return paths().data / "settings.json"


def load_settings() -> dict:
    import json
    p = _settings_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(settings: dict) -> None:
    import json
    p = _settings_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(settings, indent=2))


def get_mode() -> str:
    """Returns 'simple' or 'advanced'. Defaults to 'simple' for first-time users."""
    return load_settings().get("mode", "simple")


def set_mode(mode: str) -> None:
    if mode not in ("simple", "advanced"):
        raise ValueError(f"unknown mode {mode!r}")
    s = load_settings()
    s["mode"] = mode
    save_settings(s)


_LOG_INIT = False


def setup_logging(level: int = logging.INFO) -> None:
    global _LOG_INIT
    if _LOG_INIT:
        return
    p = paths()
    handler = logging.handlers.RotatingFileHandler(
        p.logs / "chamak.log", maxBytes=1_000_000, backupCount=3
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root = logging.getLogger("chamak")
    root.setLevel(level)
    root.addHandler(handler)
    root.propagate = False
    _LOG_INIT = True
