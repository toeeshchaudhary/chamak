from __future__ import annotations

import pytest

from chamak.demo.data import DEMO_STOCKS, by_ticker
from chamak.demo.mindmaps import BLUEPRINTS, build_snapshot
from chamak.demo.news import DEMO_NEWS
from chamak.demo.seeder import seed, reset
from chamak.recommendation.engine import rank_from_db
from chamak.scoring.engine import score
from chamak.storage.repositories import (
    mindmaps as mm_repo,
    portfolios as port_repo,
    stocks as stocks_repo,
    versions as ver_repo,
)


def test_demo_stocks_have_required_metrics():
    required = {"pe", "pb", "roe", "debt_to_equity"}
    for s in DEMO_STOCKS:
        missing = required - set(s.metrics.keys())
        assert not missing, f"{s.ticker} missing {missing}"


def test_blueprints_build_clean_snapshots():
    for bp in BLUEPRINTS:
        snap = build_snapshot(bp)
        assert snap.mindmap.name == bp.name
        assert snap.nodes  # root + beliefs
        assert snap.rules
        # All rules must reference real nodes
        node_ids = {n.id for n in snap.nodes}
        for r in snap.rules:
            assert r.node_id in node_ids


def test_seed_is_idempotent(conn):
    r1 = seed(conn)
    r2 = seed(conn)
    # Second seed must not duplicate mind maps / portfolios.
    assert r2.mindmaps == 0
    assert r2.portfolios == 0
    # Stock upserts are by design; both runs should report the same count
    assert r1.stocks == r2.stocks


def test_seed_produces_runnable_recommendations(conn):
    seed(conn)
    # Pick the Quality Compounder mind map
    quality = next(m for m in mm_repo.list_all(conn) if m.name == "Quality Compounder")
    snap = ver_repo.load_latest(conn, quality.id)
    assert snap is not None
    recs = rank_from_db(conn, snap, top_k=5)
    assert len(recs) == 5
    # Top result should be solidly positive; bottom of the spread should be lower
    assert recs[0].score > 0.6
    # Make sure TCS / HCLTECH / NESTLEIND / EICHERMOT-style quality names dominate the top
    quality_names = {"TCS", "INFY", "HCLTECH", "EICHERMOT", "NESTLEIND",
                     "PIDILITIND", "ASIANPAINT", "ITC", "TITAN", "HDFCBANK"}
    top3 = {r.ticker for r in recs[:3]}
    assert top3 & quality_names


def test_value_mindmap_avoids_high_debt(conn):
    seed(conn)
    value = next(m for m in mm_repo.list_all(conn) if m.name == "Value Investor")
    snap = ver_repo.load_latest(conn, value.id)
    assert snap is not None
    book = by_ticker()
    junk_fund = stocks_repo.latest_fundamentals(conn, "VODAIDEA")
    quality_fund = stocks_repo.latest_fundamentals(conn, "ITC")
    assert junk_fund and quality_fund
    junk = score(snap, junk_fund)
    quality = score(snap, quality_fund)
    assert quality.score > junk.score
    assert quality.score > 0.5
    assert junk.score < 0.5


def test_demo_portfolio_violations_surface_high_debt(conn):
    seed(conn)
    pf = next(p for p in port_repo.list_all(conn) if p.name == "Demo Long-Term")
    assert pf.mindmap_id is not None
    snap = ver_repo.load_latest(conn, pf.mindmap_id)
    assert snap is not None
    from chamak.portfolio.analysis import analyze
    rep = analyze(conn, pf.id, snap)
    assert rep.n_holdings > 0
    # ADANIENT or TATAMOTORS should violate the low-debt rule.
    violating_tickers = {v.ticker for v in rep.violations}
    assert "ADANIENT" in violating_tickers or "TATAMOTORS" in violating_tickers


def test_demo_news_classifier_tags_articles():
    from chamak.news.base import NewsItem
    from chamak.news.sentiment import HeuristicClassifier
    clf = HeuristicClassifier()
    for raw in DEMO_NEWS[:5]:
        item = NewsItem(
            id="x", title=raw.title, url="x", source=raw.source,
            published_at=None, tickers=raw.tickers, sectors=raw.sectors,
            body=raw.body,
        )
        tags = clf.classify(item)
        # Not every demo headline yields a tag, but most should
        if tags:
            assert all(0 <= t.confidence <= 1 for t in tags)


def test_reset_wipes_user_data(conn):
    seed(conn)
    assert mm_repo.list_all(conn)
    reset(conn)
    assert mm_repo.list_all(conn) == []
    assert stocks_repo.list_stocks(conn) == []


def test_score_bar_renders():
    from chamak.tui.widgets.score_bar import render_bar, render_pct
    s = render_bar(0.5, width=10)
    assert "[" in s and "]" in s
    assert render_pct(0.0) and render_pct(1.0)
