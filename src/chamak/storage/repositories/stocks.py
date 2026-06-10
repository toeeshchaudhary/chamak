from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from chamak.core.models import Stock, StockFundamentals
from chamak.storage.db import transaction


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def upsert_stock(conn: sqlite3.Connection, s: Stock) -> None:
    with transaction(conn):
        conn.execute(
            """INSERT INTO stocks(ticker, name, exchange, sector, industry)
               VALUES (?,?,?,?,?)
               ON CONFLICT(ticker) DO UPDATE SET
                   name=excluded.name,
                   exchange=excluded.exchange,
                   sector=excluded.sector,
                   industry=excluded.industry""",
            (s.ticker, s.name, s.exchange, s.sector, s.industry),
        )


def list_stocks(conn: sqlite3.Connection) -> list[Stock]:
    rows = conn.execute("SELECT * FROM stocks ORDER BY ticker").fetchall()
    return [
        Stock(
            ticker=r["ticker"],
            name=r["name"],
            exchange=r["exchange"],
            sector=r["sector"],
            industry=r["industry"],
        )
        for r in rows
    ]


def get_stock(conn: sqlite3.Connection, ticker: str) -> Stock | None:
    row = conn.execute("SELECT * FROM stocks WHERE ticker=?", (ticker,)).fetchone()
    if not row:
        return None
    return Stock(
        ticker=row["ticker"],
        name=row["name"],
        exchange=row["exchange"],
        sector=row["sector"],
        industry=row["industry"],
    )


def save_fundamentals(
    conn: sqlite3.Connection, f: StockFundamentals, source: str = "yfinance"
) -> None:
    with transaction(conn):
        conn.execute(
            """INSERT OR REPLACE INTO fundamentals(ticker, as_of, metrics_json, source)
               VALUES (?,?,?,?)""",
            (f.ticker, _iso(f.as_of), json.dumps(f.metrics), source),
        )


def latest_fundamentals(
    conn: sqlite3.Connection, ticker: str
) -> StockFundamentals | None:
    row = conn.execute(
        """SELECT * FROM fundamentals WHERE ticker=? ORDER BY as_of DESC LIMIT 1""",
        (ticker,),
    ).fetchone()
    if not row:
        return None
    s = get_stock(conn, ticker)
    return StockFundamentals(
        ticker=ticker,
        name=s.name if s else "",
        sector=s.sector if s else "",
        industry=s.industry if s else "",
        metrics=json.loads(row["metrics_json"]),
        as_of=datetime.fromisoformat(row["as_of"]),
    )
