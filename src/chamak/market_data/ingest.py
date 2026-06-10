"""Universe ingestion: pull fundamentals for a list of tickers into the local DB."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass

from chamak.core.models import Stock
from chamak.market_data.universe import universe as resolve_universe
from chamak.market_data.yfinance_adapter import YFinanceProvider
from chamak.storage.repositories import stocks as stocks_repo

log = logging.getLogger("chamak.market_data.ingest")


@dataclass
class IngestReport:
    universe: str
    requested: int
    fetched: int
    failed: list[str]


def ingest(conn: sqlite3.Connection, universe_name: str, *, refresh: bool = False) -> IngestReport:
    tickers = resolve_universe(universe_name)
    provider = YFinanceProvider()
    fetched = 0
    failed: list[str] = []
    for t in tickers:
        f = provider.fetch(t, refresh=refresh)
        if f is None or not f.metrics:
            failed.append(t)
            continue
        stocks_repo.upsert_stock(
            conn,
            Stock(ticker=t, name=f.name, exchange="NSE", sector=f.sector, industry=f.industry),
        )
        stocks_repo.save_fundamentals(conn, f, source="yfinance")
        fetched += 1
    return IngestReport(universe=universe_name, requested=len(tickers), fetched=fetched, failed=failed)
