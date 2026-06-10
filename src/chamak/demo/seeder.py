"""Idempotent demo seeder.

Writes:
  - 30+ stocks + fundamentals
  - 3 prebuilt mind maps (Value, Quality, Dividend)
  - 1 portfolio linked to "Value Investor" with a hand-picked basket
  - 15 demo news items with multi-label sentiment

Safe to re-run. Detects existing rows by primary key and skips dupes.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from chamak.core.ids import new_id
from chamak.core.models import Holding, MindMapSnapshot, Portfolio, Stock, StockFundamentals
from chamak.demo.data import DEMO_STOCKS
from chamak.demo.mindmaps import BLUEPRINTS, build_snapshot
from chamak.demo.news import DEMO_NEWS, now_minus
from chamak.storage.db import connect, transaction
from chamak.storage.migrator import migrate
from chamak.storage.repositories import (
    mindmaps as mm_repo,
    portfolios as port_repo,
    stocks as stocks_repo,
    versions as ver_repo,
)

log = logging.getLogger("chamak.demo.seeder")


@dataclass
class SeedReport:
    stocks: int
    mindmaps: int
    portfolios: int
    news: int


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _seed_stocks(conn: sqlite3.Connection) -> int:
    n = 0
    for d in DEMO_STOCKS:
        stocks_repo.upsert_stock(conn, Stock(
            ticker=d.ticker, name=d.name, exchange="NSE",
            sector=d.sector, industry=d.industry,
        ))
        stocks_repo.save_fundamentals(
            conn,
            StockFundamentals(
                ticker=d.ticker, name=d.name, sector=d.sector, industry=d.industry,
                metrics=dict(d.metrics),
            ),
            source="demo",
        )
        n += 1
    return n


def _existing_mindmap_names(conn: sqlite3.Connection) -> set[str]:
    return {m.name for m in mm_repo.list_all(conn, include_archived=True)}


def _seed_mindmaps(conn: sqlite3.Connection) -> tuple[int, dict[str, str]]:
    """Returns (count_created, name->id map for ALL demo mindmaps)."""
    existing = _existing_mindmap_names(conn)
    name_to_id: dict[str, str] = {}
    created = 0
    for bp in BLUEPRINTS:
        if bp.name in existing:
            for m in mm_repo.list_all(conn, include_archived=True):
                if m.name == bp.name:
                    name_to_id[bp.name] = m.id
            continue
        snap: MindMapSnapshot = build_snapshot(bp)
        mm_repo.insert(conn, snap.mindmap)
        v = ver_repo.save_snapshot(conn, snap, message="seeded by demo")
        mm_repo.replace_graph(conn, snap.mindmap.id, snap.nodes, snap.edges, snap.rules)
        snap.mindmap.current_version = v.version
        mm_repo.update_meta(conn, snap.mindmap)
        name_to_id[bp.name] = snap.mindmap.id
        created += 1
    return created, name_to_id


def _seed_portfolio(conn: sqlite3.Connection, mm_id: str | None) -> int:
    # Skip if any portfolio already exists with this name.
    for p in port_repo.list_all(conn):
        if p.name == "Demo Long-Term":
            return 0
    pf = Portfolio(name="Demo Long-Term", mindmap_id=mm_id)
    port_repo.create(conn, pf)
    basket = [
        ("HDFCBANK", 50, 1620),
        ("TCS", 30, 3500),
        ("ITC", 200, 380),
        ("RELIANCE", 25, 2700),
        ("MARUTI", 5, 11000),
        # one intentional contradiction so portfolio analysis lights up
        ("TATAMOTORS", 100, 720),
        ("ADANIENT", 20, 2400),
    ]
    for ticker, qty, avg in basket:
        port_repo.add_holding(conn, Holding(portfolio_id=pf.id, ticker=ticker,
                                            quantity=qty, avg_cost=avg))
    return 1


def _seed_news(conn: sqlite3.Connection) -> int:
    n = 0
    with transaction(conn):
        for item in DEMO_NEWS:
            url = f"demo://news/{abs(hash(item.title))}"
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO news
                       (id, url, title, source, published_at, body, tickers, sectors, sentiment_json)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        new_id(),
                        url,
                        item.title,
                        item.source,
                        _iso(now_minus(item.days_ago)),
                        item.body,
                        json.dumps(item.tickers),
                        json.dumps(item.sectors),
                        json.dumps([{"label": l, "confidence": c} for l, c in item.sentiment]),
                    ),
                )
                if conn.total_changes:
                    n += 1
            except sqlite3.IntegrityError:
                pass
    return n


def seed(conn: sqlite3.Connection | None = None) -> SeedReport:
    own = False
    if conn is None:
        migrate()
        conn = connect()
        own = True
    try:
        n_stocks = _seed_stocks(conn)
        n_mm, name_to_id = _seed_mindmaps(conn)
        # Link demo portfolio to the value mind map if it exists
        n_pf = _seed_portfolio(conn, name_to_id.get("Value Investor"))
        n_news = _seed_news(conn)
        return SeedReport(stocks=n_stocks, mindmaps=n_mm, portfolios=n_pf, news=n_news)
    finally:
        if own:
            conn.close()


def reset(conn: sqlite3.Connection | None = None) -> None:
    """Drop user data (keeps schema). Use only after explicit user confirmation."""
    own = False
    if conn is None:
        migrate()
        conn = connect()
        own = True
    try:
        with transaction(conn):
            for table in ("portfolio_holdings", "portfolios", "rules", "edges",
                          "nodes", "mindmap_versions", "mindmaps",
                          "fundamentals", "stocks", "news", "recommendations",
                          "scans", "events", "audit_logs"):
                conn.execute(f"DELETE FROM {table};")
    finally:
        if own:
            conn.close()
