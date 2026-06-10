"""Portfolio sanity-check against a linked mind map.

Detects the simplest, most useful case: 'you say you avoid high debt but you
own these levered names'. Style-drift, sector concentration, and risk
clustering are richer follow-ups; the protocol below makes them easy to add."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from chamak.core.models import Holding, MindMapSnapshot
from chamak.scoring.engine import score
from chamak.storage.repositories import portfolios as port_repo, stocks as stocks_repo


@dataclass
class Violation:
    ticker: str
    rule_text: str
    satisfaction: float
    severity: float  # rule weight * (1 - satisfaction)


@dataclass
class PortfolioReport:
    portfolio_id: str
    n_holdings: int
    n_scored: int
    avg_compatibility: float
    violations: list[Violation]
    sector_concentration: dict[str, float]
    notes: list[str]


def analyze(
    conn: sqlite3.Connection, portfolio_id: str, snap: MindMapSnapshot
) -> PortfolioReport:
    holdings: list[Holding] = port_repo.holdings(conn, portfolio_id)
    if not holdings:
        return PortfolioReport(
            portfolio_id=portfolio_id, n_holdings=0, n_scored=0,
            avg_compatibility=0.0, violations=[], sector_concentration={},
            notes=["Portfolio is empty."],
        )

    n_scored = 0
    sum_score = 0.0
    violations: list[Violation] = []
    sector_value: dict[str, float] = {}
    notes: list[str] = []

    total_value = sum(h.quantity * (h.avg_cost or 0.0) for h in holdings) or 0.0

    for h in holdings:
        f = stocks_repo.latest_fundamentals(conn, h.ticker)
        if f is None:
            notes.append(f"No cached fundamentals for {h.ticker} — run `chamak ingest`.")
            continue
        s = stocks_repo.get_stock(conn, h.ticker)
        sec = (s.sector if s else "") or "Unknown"
        if total_value > 0 and h.avg_cost:
            sector_value[sec] = sector_value.get(sec, 0.0) + h.quantity * h.avg_cost
        b = score(snap, f)
        n_scored += 1
        sum_score += b.score
        for c in b.contributions:
            if c.satisfaction < 0.5 and not c.missing_metric:
                violations.append(
                    Violation(
                        ticker=h.ticker,
                        rule_text=c.rule_text,
                        satisfaction=c.satisfaction,
                        severity=c.weight * (1.0 - c.satisfaction),
                    )
                )

    avg = sum_score / n_scored if n_scored else 0.0
    sector_pct = {k: v / total_value for k, v in sector_value.items()} if total_value else {}

    # Surface biggest concentration
    if sector_pct:
        top_sec, top_w = max(sector_pct.items(), key=lambda kv: kv[1])
        if top_w > 0.4:
            notes.append(f"Sector concentration: {top_sec} is {top_w:.0%} of portfolio.")

    violations.sort(key=lambda v: v.severity, reverse=True)
    return PortfolioReport(
        portfolio_id=portfolio_id,
        n_holdings=len(holdings),
        n_scored=n_scored,
        avg_compatibility=round(avg, 4),
        violations=violations,
        sector_concentration=sector_pct,
        notes=notes,
    )
