from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from chamak.core.models import Holding, Portfolio
from chamak.storage.db import transaction


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def create(conn: sqlite3.Connection, p: Portfolio) -> None:
    with transaction(conn):
        conn.execute(
            "INSERT INTO portfolios(id, name, mindmap_id, created_at) VALUES (?,?,?,?)",
            (p.id, p.name, p.mindmap_id, _iso(p.created_at)),
        )


def list_all(conn: sqlite3.Connection) -> list[Portfolio]:
    rows = conn.execute("SELECT * FROM portfolios ORDER BY created_at DESC").fetchall()
    return [
        Portfolio(
            id=r["id"],
            name=r["name"],
            mindmap_id=r["mindmap_id"],
            created_at=datetime.fromisoformat(r["created_at"]),
        )
        for r in rows
    ]


def get(conn: sqlite3.Connection, portfolio_id: str) -> Portfolio | None:
    row = conn.execute("SELECT * FROM portfolios WHERE id=?", (portfolio_id,)).fetchone()
    if not row:
        return None
    return Portfolio(
        id=row["id"],
        name=row["name"],
        mindmap_id=row["mindmap_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def add_holding(conn: sqlite3.Connection, h: Holding) -> None:
    with transaction(conn):
        conn.execute(
            """INSERT INTO portfolio_holdings(id, portfolio_id, ticker, quantity, avg_cost)
               VALUES (?,?,?,?,?)""",
            (h.id, h.portfolio_id, h.ticker, h.quantity, h.avg_cost),
        )


def remove_holding(conn: sqlite3.Connection, holding_id: str) -> None:
    with transaction(conn):
        conn.execute("DELETE FROM portfolio_holdings WHERE id=?", (holding_id,))


def holdings(conn: sqlite3.Connection, portfolio_id: str) -> list[Holding]:
    rows = conn.execute(
        "SELECT * FROM portfolio_holdings WHERE portfolio_id=? ORDER BY ticker",
        (portfolio_id,),
    ).fetchall()
    return [
        Holding(
            id=r["id"],
            portfolio_id=r["portfolio_id"],
            ticker=r["ticker"],
            quantity=r["quantity"],
            avg_cost=r["avg_cost"],
        )
        for r in rows
    ]


def link_mindmap(conn: sqlite3.Connection, portfolio_id: str, mindmap_id: str | None) -> None:
    with transaction(conn):
        conn.execute(
            "UPDATE portfolios SET mindmap_id=? WHERE id=?",
            (mindmap_id, portfolio_id),
        )
