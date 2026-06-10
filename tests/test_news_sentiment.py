from __future__ import annotations

from chamak.news.base import NewsItem
from chamak.news.sentiment import HeuristicClassifier, classify_text


def _item(title: str, body: str = "") -> NewsItem:
    return NewsItem(id="x", title=title, url="x", source="s",
                    published_at=None, body=body)


def test_bullish_terms_detected():
    tags = classify_text("Maruti posts record monthly dispatches")
    labels = {t.label for t in tags}
    assert "growth_signal" in labels or "bullish" in labels


def test_governance_risk_caught():
    clf = HeuristicClassifier()
    tags = clf.classify(_item("Adani pledged-share level under scrutiny"))
    labels = {t.label for t in tags}
    assert "governance_risk" in labels


def test_regulatory_signal():
    clf = HeuristicClassifier()
    tags = clf.classify(_item("AGR dues clarification sought from DoT"))
    labels = {t.label for t in tags}
    assert "regulatory_risk" in labels


def test_no_false_positive_on_neutral():
    tags = classify_text("Trading update")
    assert tags == []
