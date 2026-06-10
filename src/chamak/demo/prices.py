"""Synthetic but plausible price histories for the demo universe.

Generated deterministically from the ticker name + the stock's known
beta/growth so the charts look right and never change between runs.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from chamak.demo.data import DEMO_STOCKS, DemoStock


@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float


def _seed_for(ticker: str) -> int:
    return sum((i + 1) * ord(c) for i, c in enumerate(ticker))


def _history_for(stock: DemoStock, *, days: int = 30) -> list[Candle]:
    """Plausible-looking OHLC history ending at the stock's current price."""
    rng = random.Random(_seed_for(stock.ticker))
    metrics = stock.metrics
    beta = float(metrics.get("beta", 1.0))
    growth = float(metrics.get("revenue_growth", metrics.get("earnings_growth", 0)))
    drift = (growth / 365.0) * 0.5  # daily drift from annual growth
    if growth < -10:
        drift -= 0.001
    vol = 0.011 * max(0.4, beta)

    price = float(metrics.get("price", 100.0))
    closes: list[float] = []
    p = price
    for _ in range(days):
        closes.append(p)
        shock = rng.gauss(0, 1)
        p = p / (1 + drift + vol * shock)
    closes.reverse()  # so first element is oldest, last is newest

    candles: list[Candle] = []
    prev_close = closes[0] * (1 - vol * rng.gauss(0, 1))
    for c in closes:
        o = prev_close
        # intra-day high/low
        spread = vol * max(o, c)
        high = max(o, c) + abs(rng.gauss(0, spread))
        low = min(o, c) - abs(rng.gauss(0, spread))
        candles.append(Candle(open=round(o, 2), high=round(high, 2),
                              low=round(low, 2), close=round(c, 2)))
        prev_close = c
    return candles


def history_by_ticker() -> dict[str, list[Candle]]:
    return {s.ticker: _history_for(s) for s in DEMO_STOCKS}


def history_for(ticker: str, days: int = 30) -> list[Candle]:
    for s in DEMO_STOCKS:
        if s.ticker == ticker:
            return _history_for(s, days=days)
    return []
