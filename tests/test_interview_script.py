from __future__ import annotations

from chamak.interview.engine import InterviewEngine


def test_full_run_produces_snapshot():
    e = InterviewEngine()
    # Walk every question with a sane answer.
    answers = {
        "horizon": "long",
        "capital_cr": 5.0,
        "risk": "low",
        "debt": "averse",
        "valuation": "value",
        "quality": ["high_roe", "cash"],
        "management": 5,
        "philosophy": "I prefer companies that have survived multiple cycles.",
        "bad_experiences": "Avoid high debt and pledged shares.",
    }
    for q in e.questions:
        e.answer(answers.get(q["id"], ""))
    snap = e.build_snapshot("Test Mind Map")
    assert snap.mindmap.name == "Test Mind Map"
    # We should at least have rules from value + averse + low-risk + quality + management
    assert len(snap.rules) >= 5
    assert any(r.text.startswith("debt_to_equity") for r in snap.rules)


def test_partial_run_skips_cleanly():
    e = InterviewEngine()
    e.answer("short")
    while not e.done():
        e.skip()
    snap = e.build_snapshot("T")
    # Even with mostly skipped, we get an archetype + root node
    assert len(snap.nodes) >= 1
