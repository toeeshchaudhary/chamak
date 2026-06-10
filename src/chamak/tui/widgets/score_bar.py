"""ASCII score bar used in tables and stock detail headers."""

from __future__ import annotations

_BLOCKS = "▏▎▍▌▋▊▉█"
_EMPTY = "░"


def render_bar(value: float, width: int = 12) -> str:
    """Render a 0..1 value as a partial-block bar. Returns Rich markup."""
    value = max(0.0, min(1.0, value))
    total_eighths = int(round(value * width * 8))
    full_blocks = total_eighths // 8
    remainder = total_eighths - full_blocks * 8
    bar = "█" * full_blocks
    if remainder and full_blocks < width:
        bar += _BLOCKS[remainder - 1]
    bar = bar.ljust(width, _EMPTY)
    color = score_color(value)
    return f"[{color}]{bar}[/]"


def score_color(value: float) -> str:
    if value >= 0.75:
        return "#98c379"  # green-ish
    if value >= 0.5:
        return "#e5c07b"  # amber
    if value >= 0.25:
        return "#d19a66"  # orange
    return "#6b6b6b"      # dim


def render_pct(value: float) -> str:
    color = score_color(value)
    return f"[{color}]{value:.0%}[/]"
