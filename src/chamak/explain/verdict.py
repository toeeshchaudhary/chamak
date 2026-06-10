"""Convert a numeric compatibility score into a verdict tier + summary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Verdict:
    tier: str        # "strong" | "good" | "mixed" | "poor"
    label: str       # display name
    headline: str    # one-line gist
    color: str       # hex color for UI


def for_score(score: float, *, hard_failures: bool = False) -> Verdict:
    if hard_failures:
        return Verdict(
            tier="poor",
            label="DOESN'T FIT",
            headline="This stock breaks a rule you said was non-negotiable.",
            color="#e06c75",
        )
    if score >= 0.75:
        return Verdict(
            tier="strong",
            label="STRONG FIT",
            headline="Matches almost everything you care about.",
            color="#98c379",
        )
    if score >= 0.60:
        return Verdict(
            tier="good",
            label="GOOD FIT",
            headline="Matches most of what you care about.",
            color="#88c0d0",
        )
    if score >= 0.45:
        return Verdict(
            tier="mixed",
            label="MIXED",
            headline="A few things you like, a few you don't.",
            color="#e5c07b",
        )
    return Verdict(
        tier="poor",
        label="POOR FIT",
        headline="Doesn't really match your style.",
        color="#d19a66",
    )
