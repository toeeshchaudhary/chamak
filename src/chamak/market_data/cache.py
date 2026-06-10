from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from chamak.config import paths


@dataclass
class CacheEntry:
    body: dict
    fetched_at: float
    ttl_s: float


def _fund_path(ticker: str) -> Path:
    return paths().fundamentals_cache / f"{ticker.upper()}.json"


def write_fundamentals(ticker: str, data: dict, ttl_s: float) -> None:
    payload = {"fetched_at": time.time(), "ttl_s": ttl_s, "body": data}
    _fund_path(ticker).write_text(json.dumps(payload))


def read_fundamentals(ticker: str) -> CacheEntry | None:
    p = _fund_path(ticker)
    if not p.exists():
        return None
    try:
        payload = json.loads(p.read_text())
    except json.JSONDecodeError:
        return None
    return CacheEntry(body=payload["body"], fetched_at=payload["fetched_at"], ttl_s=payload["ttl_s"])


def is_fresh(entry: CacheEntry | None, max_age_s: float) -> bool:
    if entry is None:
        return False
    return (time.time() - entry.fetched_at) < min(max_age_s, entry.ttl_s)
