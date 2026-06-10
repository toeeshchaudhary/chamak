from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path


def nifty50() -> list[str]:
    data = json.loads(Path(str(files("chamak").joinpath("../../data/nifty50.json"))).read_text())
    return list(data["tickers"])


def _bundled_universe(name: str) -> list[str]:
    # Resolve relative to repo data/ dir, which is included in the wheel via pyproject include.
    candidates = [
        Path(__file__).resolve().parents[3] / "data" / f"{name}.json",  # source layout
        Path(__file__).resolve().parents[2] / "data" / f"{name}.json",
    ]
    for p in candidates:
        if p.exists():
            return list(json.loads(p.read_text())["tickers"])
    raise FileNotFoundError(f"universe {name!r} not found")


def universe(name: str) -> list[str]:
    name = name.lower()
    if name in ("nifty50", "nifty 50"):
        try:
            return _bundled_universe("nifty50")
        except FileNotFoundError:
            return nifty50()
    raise ValueError(f"unknown universe {name!r}")
