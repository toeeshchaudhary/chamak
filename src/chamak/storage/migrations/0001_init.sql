-- Chamak initial schema.
-- Single-user, local SQLite. JSON1 used for graph snapshots.

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    settings_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS mindmaps (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,                -- rule | narrative | hybrid
    archetype TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    current_version INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_mindmaps_archived ON mindmaps(archived);

CREATE TABLE IF NOT EXISTS mindmap_versions (
    id TEXT PRIMARY KEY,
    mindmap_id TEXT NOT NULL REFERENCES mindmaps(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    graph_json TEXT NOT NULL,          -- full MindMapSnapshot
    created_at TEXT NOT NULL,
    UNIQUE(mindmap_id, version)
);

CREATE INDEX IF NOT EXISTS idx_versions_mindmap ON mindmap_versions(mindmap_id, version DESC);

-- Live (latest-saved) graph tables for queryable access. Mirrors the snapshot.
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    mindmap_id TEXT NOT NULL REFERENCES mindmaps(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    weight REAL NOT NULL DEFAULT 1.0,
    confidence REAL NOT NULL DEFAULT 1.0,
    payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_nodes_mindmap ON nodes(mindmap_id);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);

CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY,
    mindmap_id TEXT NOT NULL REFERENCES mindmaps(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'supports',
    weight REAL NOT NULL DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_edges_mindmap ON edges(mindmap_id);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target);

CREATE TABLE IF NOT EXISTS rules (
    id TEXT PRIMARY KEY,
    mindmap_id TEXT NOT NULL REFERENCES mindmaps(id) ON DELETE CASCADE,
    node_id TEXT NOT NULL,
    text TEXT NOT NULL,
    ast_json TEXT NOT NULL,
    hard INTEGER NOT NULL DEFAULT 0,
    weight REAL NOT NULL DEFAULT 1.0,
    confidence REAL NOT NULL DEFAULT 1.0,
    polarity TEXT NOT NULL DEFAULT 'prefer'
);

CREATE INDEX IF NOT EXISTS idx_rules_mindmap ON rules(mindmap_id);
CREATE INDEX IF NOT EXISTS idx_rules_node ON rules(node_id);

CREATE TABLE IF NOT EXISTS stocks (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    exchange TEXT NOT NULL DEFAULT 'NSE',
    sector TEXT NOT NULL DEFAULT '',
    industry TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS fundamentals (
    ticker TEXT NOT NULL REFERENCES stocks(ticker) ON DELETE CASCADE,
    as_of TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'yfinance',
    PRIMARY KEY (ticker, as_of)
);

CREATE INDEX IF NOT EXISTS idx_fundamentals_ticker ON fundamentals(ticker, as_of DESC);

CREATE TABLE IF NOT EXISTS recommendations (
    id TEXT PRIMARY KEY,
    mindmap_id TEXT NOT NULL,
    mindmap_version INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    score REAL NOT NULL,
    confidence REAL NOT NULL,
    breakdown_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recs_mindmap ON recommendations(mindmap_id, score DESC);

CREATE TABLE IF NOT EXISTS news (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    published_at TEXT,
    body TEXT,
    tickers TEXT NOT NULL DEFAULT '[]',  -- JSON array of mapped tickers
    sectors TEXT NOT NULL DEFAULT '[]',
    sentiment_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at DESC);

CREATE TABLE IF NOT EXISTS portfolios (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mindmap_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id TEXT PRIMARY KEY,
    portfolio_id TEXT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 0,
    avg_cost REAL NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_holdings_portfolio ON portfolio_holdings(portfolio_id);

CREATE TABLE IF NOT EXISTS scans (
    id TEXT PRIMARY KEY,
    mindmap_id TEXT NOT NULL,
    mindmap_version INTEGER NOT NULL,
    universe TEXT NOT NULL,
    top_k INTEGER NOT NULL,
    results_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT NOT NULL DEFAULT 'local',
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
