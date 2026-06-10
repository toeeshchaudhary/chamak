from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Iterable

from chamak.core.models import (
    Edge,
    MindMap,
    MindMapType,
    Node,
    NodeType,
    Rule,
    utcnow,
)
from chamak.storage.db import transaction


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _row_to_mindmap(row: sqlite3.Row) -> MindMap:
    return MindMap(
        id=row["id"],
        name=row["name"],
        type=MindMapType(row["type"]),
        archetype=row["archetype"],
        description=row["description"],
        archived=bool(row["archived"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        current_version=int(row["current_version"]),
    )


def insert(conn: sqlite3.Connection, mm: MindMap) -> None:
    with transaction(conn):
        conn.execute(
            """INSERT INTO mindmaps
               (id, name, type, archetype, description, archived, created_at, updated_at, current_version)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                mm.id,
                mm.name,
                mm.type.value,
                mm.archetype,
                mm.description,
                int(mm.archived),
                _iso(mm.created_at),
                _iso(mm.updated_at),
                mm.current_version,
            ),
        )


def update_meta(conn: sqlite3.Connection, mm: MindMap) -> None:
    mm.updated_at = utcnow()
    with transaction(conn):
        conn.execute(
            """UPDATE mindmaps
               SET name=?, type=?, archetype=?, description=?, archived=?,
                   updated_at=?, current_version=?
               WHERE id=?""",
            (
                mm.name,
                mm.type.value,
                mm.archetype,
                mm.description,
                int(mm.archived),
                _iso(mm.updated_at),
                mm.current_version,
                mm.id,
            ),
        )


def get(conn: sqlite3.Connection, mm_id: str) -> MindMap | None:
    row = conn.execute("SELECT * FROM mindmaps WHERE id=?", (mm_id,)).fetchone()
    return _row_to_mindmap(row) if row else None


def list_all(conn: sqlite3.Connection, include_archived: bool = False) -> list[MindMap]:
    if include_archived:
        rows = conn.execute("SELECT * FROM mindmaps ORDER BY updated_at DESC").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM mindmaps WHERE archived=0 ORDER BY updated_at DESC"
        ).fetchall()
    return [_row_to_mindmap(r) for r in rows]


def archive(conn: sqlite3.Connection, mm_id: str, archived: bool = True) -> None:
    with transaction(conn):
        conn.execute(
            "UPDATE mindmaps SET archived=?, updated_at=? WHERE id=?",
            (int(archived), _iso(utcnow()), mm_id),
        )


def delete(conn: sqlite3.Connection, mm_id: str) -> None:
    with transaction(conn):
        conn.execute("DELETE FROM mindmaps WHERE id=?", (mm_id,))


# --- live graph (latest-saved) ---

def replace_graph(
    conn: sqlite3.Connection,
    mm_id: str,
    nodes: Iterable[Node],
    edges: Iterable[Edge],
    rules: Iterable[Rule],
) -> None:
    with transaction(conn):
        conn.execute("DELETE FROM nodes WHERE mindmap_id=?", (mm_id,))
        conn.execute("DELETE FROM edges WHERE mindmap_id=?", (mm_id,))
        conn.execute("DELETE FROM rules WHERE mindmap_id=?", (mm_id,))
        for n in nodes:
            conn.execute(
                """INSERT INTO nodes(id, mindmap_id, type, label, description, weight, confidence, payload_json)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    n.id,
                    mm_id,
                    n.type.value,
                    n.label,
                    n.description,
                    n.weight,
                    n.confidence,
                    json.dumps(n.payload),
                ),
            )
        for e in edges:
            conn.execute(
                """INSERT INTO edges(id, mindmap_id, source, target, kind, weight)
                   VALUES (?,?,?,?,?,?)""",
                (e.id, mm_id, e.source, e.target, e.kind, e.weight),
            )
        for r in rules:
            conn.execute(
                """INSERT INTO rules(id, mindmap_id, node_id, text, ast_json, hard, weight, confidence, polarity)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    r.id,
                    mm_id,
                    r.node_id,
                    r.text,
                    json.dumps(r.ast_json),
                    int(r.hard),
                    r.weight,
                    r.confidence,
                    r.polarity,
                ),
            )


def load_graph(conn: sqlite3.Connection, mm_id: str) -> tuple[list[Node], list[Edge], list[Rule]]:
    nrows = conn.execute("SELECT * FROM nodes WHERE mindmap_id=?", (mm_id,)).fetchall()
    erows = conn.execute("SELECT * FROM edges WHERE mindmap_id=?", (mm_id,)).fetchall()
    rrows = conn.execute("SELECT * FROM rules WHERE mindmap_id=?", (mm_id,)).fetchall()
    nodes = [
        Node(
            id=r["id"],
            type=NodeType(r["type"]),
            label=r["label"],
            description=r["description"],
            weight=r["weight"],
            confidence=r["confidence"],
            payload=json.loads(r["payload_json"] or "{}"),
        )
        for r in nrows
    ]
    edges = [
        Edge(
            id=r["id"],
            source=r["source"],
            target=r["target"],
            kind=r["kind"],
            weight=r["weight"],
        )
        for r in erows
    ]
    rules = [
        Rule(
            id=r["id"],
            node_id=r["node_id"],
            text=r["text"],
            ast_json=json.loads(r["ast_json"]),
            hard=bool(r["hard"]),
            weight=r["weight"],
            confidence=r["confidence"],
            polarity=r["polarity"],
        )
        for r in rrows
    ]
    return nodes, edges, rules
