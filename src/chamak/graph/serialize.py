from __future__ import annotations

import json

from chamak.core.models import MindMapSnapshot


def to_json(snap: MindMapSnapshot) -> str:
    return json.dumps(snap.model_dump(mode="json"))


def from_json(s: str) -> MindMapSnapshot:
    return MindMapSnapshot.model_validate_json(s)
