from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from chamak.core.ids import new_id
from chamak.core.models import MindMapSnapshot, MindMapVersion, utcnow
from chamak.storage.db import transaction


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def next_version(conn: sqlite3.Connection, mindmap_id: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(version), 0) AS v FROM mindmap_versions WHERE mindmap_id=?",
        (mindmap_id,),
    ).fetchone()
    return int(row["v"]) + 1


def save_snapshot(
    conn: sqlite3.Connection, snapshot: MindMapSnapshot, message: str = ""
) -> MindMapVersion:
    v = next_version(conn, snapshot.mindmap.id)
    version = MindMapVersion(
        id=new_id(),
        mindmap_id=snapshot.mindmap.id,
        version=v,
        message=message,
        snapshot=snapshot,
        created_at=utcnow(),
    )
    payload = snapshot.model_dump(mode="json")
    with transaction(conn):
        conn.execute(
            """INSERT INTO mindmap_versions(id, mindmap_id, version, message, graph_json, created_at)
               VALUES (?,?,?,?,?,?)""",
            (
                version.id,
                version.mindmap_id,
                version.version,
                version.message,
                json.dumps(payload),
                _iso(version.created_at),
            ),
        )
        conn.execute(
            "UPDATE mindmaps SET current_version=?, updated_at=? WHERE id=?",
            (v, _iso(version.created_at), snapshot.mindmap.id),
        )
    return version


def list_versions(conn: sqlite3.Connection, mindmap_id: str) -> list[dict]:
    rows = conn.execute(
        """SELECT id, version, message, created_at
           FROM mindmap_versions WHERE mindmap_id=? ORDER BY version DESC""",
        (mindmap_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def load_version(
    conn: sqlite3.Connection, mindmap_id: str, version: int
) -> MindMapSnapshot | None:
    row = conn.execute(
        "SELECT graph_json FROM mindmap_versions WHERE mindmap_id=? AND version=?",
        (mindmap_id, version),
    ).fetchone()
    if not row:
        return None
    return MindMapSnapshot.model_validate_json(row["graph_json"])


def load_latest(conn: sqlite3.Connection, mindmap_id: str) -> MindMapSnapshot | None:
    row = conn.execute(
        """SELECT graph_json FROM mindmap_versions
           WHERE mindmap_id=? ORDER BY version DESC LIMIT 1""",
        (mindmap_id,),
    ).fetchone()
    if not row:
        return None
    return MindMapSnapshot.model_validate_json(row["graph_json"])
