"""ASCII candlestick chart renderer.

Renders a sequence of OHLC candles into a multi-row, multi-column string
of box-drawing + half-block characters with Rich color markup. Each candle
takes one column.
"""

from __future__ import annotations

from chamak.demo.prices import Candle

# Colors
GREEN = "#98c379"
RED = "#e06c75"
GREY = "#5a5a5a"
AXIS = "#3a3a3a"


def _y_position(value: float, vmin: float, vmax: float, rows: int) -> int:
    """Map a price into a row index (0 = top, rows-1 = bottom)."""
    if vmax == vmin:
        return rows // 2
    frac = (vmax - value) / (vmax - vmin)
    return max(0, min(rows - 1, int(round(frac * (rows - 1)))))


def render_candles(
    candles: list[Candle],
    *,
    rows: int = 8,
    width: int | None = None,
    show_axis: bool = True,
) -> str:
    """Render a candlestick chart. Returns Rich-markup multi-line string."""
    if not candles:
        return "[dim](no price data)[/]"
    if width is not None and width < len(candles):
        # Take the most recent N candles to fit the width
        candles = candles[-width:]

    vmin = min(c.low for c in candles)
    vmax = max(c.high for c in candles)
    if vmax == vmin:
        vmax = vmin + 1

    # Each cell is (char, color or None). We compress adjacent same-color cells
    # into a single Rich markup span when joining the row — keeps the tag count
    # manageable so Rich's parser can handle it.
    grid: list[list[tuple[str, str | None]]] = [
        [(" ", None) for _ in candles] for _ in range(rows)
    ]

    for x, c in enumerate(candles):
        up = c.close >= c.open
        col = GREEN if up else RED
        y_high = _y_position(c.high, vmin, vmax, rows)
        y_low = _y_position(c.low, vmin, vmax, rows)
        y_open = _y_position(c.open, vmin, vmax, rows)
        y_close = _y_position(c.close, vmin, vmax, rows)
        body_top = min(y_open, y_close)
        body_bot = max(y_open, y_close)

        for y in range(y_high, y_low + 1):
            if body_top <= y <= body_bot:
                continue
            grid[y][x] = ("│", col)
        if body_top == body_bot:
            grid[body_top][x] = ("━", col)
        else:
            for y in range(body_top, body_bot + 1):
                grid[y][x] = ("█", col)

    def _row_to_str(row: list[tuple[str, str | None]]) -> str:
        out_parts: list[str] = []
        run_color: str | None = None
        run_chars: list[str] = []

        def flush() -> None:
            if not run_chars:
                return
            txt = "".join(run_chars)
            if run_color is None:
                out_parts.append(txt)
            else:
                out_parts.append(f"[{run_color}]{txt}[/]")
            run_chars.clear()

        for ch, color in row:
            nonlocal_color = color
            if nonlocal_color != run_color:
                flush()
                run_color = nonlocal_color
            run_chars.append(ch)
        flush()
        return "".join(out_parts)

    body_lines = [_row_to_str(row) for row in grid]

    if show_axis:
        # Y-axis labels: top value, mid value, bottom value
        label_top = _fmt(vmax)
        label_bot = _fmt(vmin)
        label_pad = max(len(label_top), len(label_bot))
        out_lines: list[str] = []
        for i, line in enumerate(body_lines):
            if i == 0:
                prefix = label_top.rjust(label_pad) + " "
            elif i == len(body_lines) - 1:
                prefix = label_bot.rjust(label_pad) + " "
            else:
                prefix = " " * label_pad + " "
            out_lines.append(f"[{AXIS}]{prefix}[/]{line}")
        return "\n".join(out_lines)

    return "\n".join(body_lines)


def render_sparkline(values: list[float], *, width: int = 30) -> str:
    """Tiny one-line sparkline for trend display. Uses Unicode bars."""
    if not values:
        return ""
    if len(values) > width:
        # Average-down to width
        step = len(values) / width
        sampled = [values[int(i * step)] for i in range(width)]
        values = sampled
    blocks = "▁▂▃▄▅▆▇█"
    vmin, vmax = min(values), max(values)
    rng = vmax - vmin or 1
    chars = []
    last = values[0]
    for v in values:
        idx = int((v - vmin) / rng * (len(blocks) - 1))
        color = GREEN if v >= last else RED
        chars.append(f"[{color}]{blocks[idx]}[/]")
        last = v
    return "".join(chars)


def _fmt(value: float) -> str:
    if value >= 10000:
        return f"₹{value/1000:.1f}k"
    if value >= 1:
        return f"₹{value:.0f}"
    return f"₹{value:.2f}"
