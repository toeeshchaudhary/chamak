from __future__ import annotations

import sqlite3
from typing import Iterable

from chamak.core.models import MindMapSnapshot, Recommendation, StockFundamentals
from chamak.scoring.engine import score
from chamak.storage.repositories import stocks as stocks_repo


def rank(
    snap: MindMapSnapshot,
    fundamentals: Iterable[StockFundamentals],
    *,
    top_k: int | None = None,
    min_score: float = 0.0,
) -> list[Recommendation]:
    recs: list[Recommendation] = []
    for f in fundamentals:
        breakdown = score(snap, f)
        if breakdown.score < min_score:
            continue
        recs.append(
            Recommendation(
                mindmap_id=snap.mindmap.id,
                mindmap_version=snap.mindmap.current_version,
                ticker=f.ticker,
                score=breakdown.score,
                confidence=breakdown.confidence,
                breakdown=breakdown,
            )
        )
    recs.sort(key=lambda r: (r.score, r.confidence), reverse=True)
    if top_k:
        recs = recs[:top_k]
    return recs


def rank_from_db(
    conn: sqlite3.Connection,
    snap: MindMapSnapshot,
    tickers: Iterable[str] | None = None,
    *,
    top_k: int | None = None,
    min_score: float = 0.0,
) -> list[Recommendation]:
    if tickers is None:
        tickers = [s.ticker for s in stocks_repo.list_stocks(conn)]
    funds = []
    for t in tickers:
        f = stocks_repo.latest_fundamentals(conn, t)
        if f is not None:
            funds.append(f)
    return rank(snap, funds, top_k=top_k, min_score=min_score)
