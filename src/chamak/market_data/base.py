from __future__ import annotations

from typing import Protocol

from chamak.core.models import Stock, StockFundamentals


class FundamentalsProvider(Protocol):
    name: str

    def fetch(self, ticker: str) -> StockFundamentals | None: ...
    def info(self, ticker: str) -> Stock | None: ...


class PriceProvider(Protocol):
    name: str

    def history(self, ticker: str, period: str = "1y") -> list[dict]: ...
