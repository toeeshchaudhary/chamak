from __future__ import annotations

from typing import Literal

Exchange = Literal["NSE", "BSE"]


def to_yf(ticker: str, exchange: Exchange = "NSE") -> str:
    """Map a bare ticker to a yfinance symbol."""
    t = ticker.upper().strip()
    if t.endswith(".NS") or t.endswith(".BO"):
        return t
    suffix = ".NS" if exchange == "NSE" else ".BO"
    return f"{t}{suffix}"


def from_yf(symbol: str) -> tuple[str, Exchange]:
    s = symbol.upper().strip()
    if s.endswith(".NS"):
        return s[:-3], "NSE"
    if s.endswith(".BO"):
        return s[:-3], "BSE"
    return s, "NSE"
