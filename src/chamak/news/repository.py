"""Storage helpers for the news table."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any


def list_recent(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, Any]]:
    rows = conn.execute(
        """SELECT id, url, title, source, published_at, body, tickers, sectors, sentiment_json
           FROM news ORDER BY published_at DESC NULLS LAST LIMIT ?""",
        (limit,),
    ).fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append({
            "id": r["id"],
            "url": r["url"],
            "title": r["title"],
            "source": r["source"],
            "published_at": (
                datetime.fromisoformat(r["published_at"]) if r["published_at"] else None
            ),
            "body": r["body"] or "",
            "tickers": json.loads(r["tickers"] or "[]"),
            "sectors": json.loads(r["sectors"] or "[]"),
            "sentiment": json.loads(r["sentiment_json"] or "[]"),
        })
    return out


def for_ticker(conn: sqlite3.Connection, ticker: str, limit: int = 20) -> list[dict[str, Any]]:
    items = list_recent(conn, limit=500)
    return [it for it in items if ticker.upper() in [t.upper() for t in it["tickers"]]][:limit]
