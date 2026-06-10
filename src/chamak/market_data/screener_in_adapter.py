"""Placeholder for a screener.in adapter.

screener.in does not expose an official API. Real implementation would
scrape the company page with a polite delay and parse the fundamentals
table. Deferred to a follow-up — we ship the protocol now and an explicit
NotImplementedError so callers don't silently fall through.
"""

from __future__ import annotations

from chamak.core.models import Stock, StockFundamentals
from chamak.market_data.base import FundamentalsProvider


class ScreenerInProvider(FundamentalsProvider):
    name = "screener.in"

    def fetch(self, ticker: str) -> StockFundamentals | None:
        raise NotImplementedError("screener.in adapter is a TODO(phase-2)")

    def info(self, ticker: str) -> Stock | None:
        raise NotImplementedError("screener.in adapter is a TODO(phase-2)")
