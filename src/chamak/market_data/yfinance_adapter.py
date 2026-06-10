"""yfinance adapter — best-effort fundamentals + price.

yfinance returns inconsistent fields for Indian tickers. We translate what
we can into our canonical metric keys (matched against the rule registry).
Fields we can't compute are simply omitted; the evaluator handles that.

This module imports yfinance lazily so importing chamak doesn't pay the cost.
"""

from __future__ import annotations

import logging
from typing import Any

from chamak.core.models import Stock, StockFundamentals, utcnow
from chamak.market_data.base import FundamentalsProvider
from chamak.market_data.cache import is_fresh, read_fundamentals, write_fundamentals
from chamak.market_data.tickers import to_yf

log = logging.getLogger("chamak.market_data.yfinance")


# Map our canonical metric keys to yfinance "info" keys + a transform.
def _pct(x: Any) -> float | None:
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    # yfinance returns fractions for some fields (0.15 = 15%)
    return v * 100.0 if -1.5 <= v <= 1.5 else v


def _identity(x: Any) -> float | None:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


_INFO_MAP: dict[str, tuple[str, Any]] = {
    # canonical -> (yf field, transform)
    "pe": ("trailingPE", _identity),
    "pb": ("priceToBook", _identity),
    "ps": ("priceToSalesTrailing12Months", _identity),
    "ev_ebitda": ("enterpriseToEbitda", _identity),
    "dividend_yield": ("dividendYield", _pct),
    "roe": ("returnOnEquity", _pct),
    "roa": ("returnOnAssets", _pct),
    "net_margin": ("profitMargins", _pct),
    "operating_margin": ("operatingMargins", _pct),
    "gross_margin": ("grossMargins", _pct),
    "revenue_growth": ("revenueGrowth", _pct),
    "earnings_growth": ("earningsGrowth", _pct),
    "debt_to_equity": ("debtToEquity", lambda v: _identity(v) / 100.0 if v is not None else None),
    "current_ratio": ("currentRatio", _identity),
    "quick_ratio": ("quickRatio", _identity),
    "beta": ("beta", _identity),
    "price": ("currentPrice", _identity),
    "market_cap_cr": ("marketCap", lambda v: _identity(v) / 1e7 if v is not None else None),
}


def _info_to_metrics(info: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    for k, (yf_key, fn) in _INFO_MAP.items():
        v = fn(info.get(yf_key))
        if v is not None and v == v:  # NaN guard
            out[k] = v
    return out


class YFinanceProvider(FundamentalsProvider):
    name = "yfinance"

    def __init__(self, *, ttl_s: float = 7 * 24 * 3600, cache_max_age_s: float | None = None) -> None:
        self.ttl_s = ttl_s
        self.cache_max_age_s = cache_max_age_s if cache_max_age_s is not None else ttl_s

    def _fetch_raw(self, ticker: str) -> dict | None:
        try:
            import yfinance as yf  # type: ignore
        except ImportError:
            log.warning("yfinance not installed")
            return None
        sym = to_yf(ticker)
        try:
            t = yf.Ticker(sym)
            info = t.info or {}
        except Exception as e:  # network failures, JSON errors, scrape changes
            log.warning("yfinance fetch failed for %s: %s", sym, e)
            return None
        return info

    def fetch(self, ticker: str, *, refresh: bool = False) -> StockFundamentals | None:
        cached = read_fundamentals(ticker)
        if not refresh and is_fresh(cached, self.cache_max_age_s):
            info = cached.body
        else:
            info = self._fetch_raw(ticker)
            if info is None:
                return cached and StockFundamentals(
                    ticker=ticker,
                    metrics=_info_to_metrics(cached.body),
                    name=cached.body.get("longName", ""),
                    sector=cached.body.get("sector", ""),
                    industry=cached.body.get("industry", ""),
                ) or None
            write_fundamentals(ticker, info, self.ttl_s)
        metrics = _info_to_metrics(info)
        return StockFundamentals(
            ticker=ticker,
            name=info.get("longName") or info.get("shortName") or "",
            sector=info.get("sector", ""),
            industry=info.get("industry", ""),
            metrics=metrics,
            as_of=utcnow(),
        )

    def info(self, ticker: str) -> Stock | None:
        f = self.fetch(ticker)
        if f is None:
            return None
        return Stock(
            ticker=ticker, name=f.name, exchange="NSE", sector=f.sector, industry=f.industry
        )
