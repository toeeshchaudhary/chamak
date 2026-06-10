from __future__ import annotations


def test_migrate_creates_tables(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    names = {r["name"] for r in rows}
    expected = {
        "schema_version", "users", "mindmaps", "mindmap_versions",
        "nodes", "edges", "rules", "stocks", "fundamentals",
        "recommendations", "news", "portfolios", "portfolio_holdings",
        "scans", "events", "audit_logs",
    }
    assert expected.issubset(names), f"missing: {expected - names}"


def test_migrate_is_idempotent(conn):
    from chamak.storage.migrator import migrate
    v = migrate(conn)
    v2 = migrate(conn)
    assert v == v2
