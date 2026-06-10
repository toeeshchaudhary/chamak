from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from chamak.storage.db import transaction


def log(
    conn: sqlite3.Connection,
    action: str,
    target: str,
    payload: dict | None = None,
    actor: str = "local",
) -> None:
    with transaction(conn):
        conn.execute(
            """INSERT INTO audit_logs(actor, action, target, payload_json, created_at)
               VALUES (?,?,?,?,?)""",
            (
                actor,
                action,
                target,
                json.dumps(payload or {}),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
