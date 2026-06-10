from __future__ import annotations

from datetime import datetime

from chamak.news.base import NewsItem


class RSSProvider:
    """Stub. A real implementation pulls Moneycontrol/Livemint/BSE/NSE filings RSS,
    dedups by URL hash, extracts body text, and ticker-maps via the stocks table."""

    name = "rss-stub"

    def fetch(self, since: datetime | None = None) -> list[NewsItem]:
        return []
