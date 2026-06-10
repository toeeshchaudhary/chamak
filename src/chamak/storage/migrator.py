from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path

from chamak.core.errors import MigrationError
from chamak.storage.db import connect, transaction


def _migrations_dir() -> Path:
    return Path(str(files("chamak.storage").joinpath("migrations")))


def _current_version(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchone()
    if not row:
        return 0
    row = conn.execute(
        "SELECT MAX(version) AS v FROM schema_version"
    ).fetchone()
    return int(row["v"] or 0)


def migrate(conn: sqlite3.Connection | None = None) -> int:
    """Apply pending migrations. Returns the resulting schema version."""
    own = False
    if conn is None:
        conn = connect()
        own = True
    try:
        d = _migrations_dir()
        files_sorted = sorted(d.glob("*.sql"))
        applied = _current_version(conn)
        max_seen = applied
        for f in files_sorted:
            try:
                version = int(f.name.split("_", 1)[0])
            except ValueError as e:
                raise MigrationError(f"bad migration name: {f.name}") from e
            if version <= applied:
                continue
            sql = f.read_text()
            # executescript handles its own transactions (it issues an
            # implicit COMMIT). Don't wrap it in our `transaction` ctx.
            conn.executescript(sql)
            with transaction(conn):
                conn.execute(
                    "INSERT INTO schema_version(version, applied_at) VALUES (?, ?)",
                    (version, datetime.now(timezone.utc).isoformat()),
                )
            max_seen = version
        return max_seen
    finally:
        if own:
            conn.close()
