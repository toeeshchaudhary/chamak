"""Hand-curated demo news headlines + multi-label sentiment.

Not real headlines — synthesized to exercise sentiment + ticker mapping
during a demo without requiring network access."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class DemoNewsItem:
    title: str
    source: str
    days_ago: int
    tickers: list[str]
    sectors: list[str]
    sentiment: list[tuple[str, float]]  # (label, confidence)
    body: str = ""


DEMO_NEWS: list[DemoNewsItem] = [
    DemoNewsItem(
        title="TCS bags ten-year, ₹15,000 cr deal with European bank",
        source="Demo Wire",
        days_ago=1,
        tickers=["TCS"],
        sectors=["IT"],
        sentiment=[("bullish", 0.85), ("growth_signal", 0.78)],
        body="TCS announced a multi-year transformation deal expected to add 2-3% to FY revenue.",
    ),
    DemoNewsItem(
        title="HDFC Bank Q3 NIM compression sharper than expected",
        source="Demo Wire",
        days_ago=2,
        tickers=["HDFCBANK"],
        sectors=["Banking"],
        sentiment=[("bearish", 0.65), ("management_concern", 0.45)],
        body="Net interest margin slipped 18 bps QoQ; deposit growth lags loan book.",
    ),
    DemoNewsItem(
        title="ITC hotels demerger record date set for next quarter",
        source="Demo Wire",
        days_ago=3,
        tickers=["ITC"],
        sectors=["FMCG"],
        sentiment=[("bullish", 0.55), ("innovation_signal", 0.4)],
    ),
    DemoNewsItem(
        title="Tata Motors EV PV losses persist; JLR China weakness continues",
        source="Demo Wire",
        days_ago=4,
        tickers=["TATAMOTORS"],
        sectors=["Auto"],
        sentiment=[("bearish", 0.7), ("competitive_threat", 0.6), ("debt_concern", 0.35)],
    ),
    DemoNewsItem(
        title="Adani Enterprises pledged-share level under scrutiny",
        source="Demo Wire",
        days_ago=2,
        tickers=["ADANIENT"],
        sectors=["Diversified"],
        sentiment=[("bearish", 0.8), ("governance_risk", 0.85), ("debt_concern", 0.65)],
    ),
    DemoNewsItem(
        title="Coal India announces ₹15.75/share interim dividend",
        source="Demo Wire",
        days_ago=1,
        tickers=["COALINDIA"],
        sectors=["Energy"],
        sentiment=[("bullish", 0.6), ("sector_tailwind", 0.5)],
    ),
    DemoNewsItem(
        title="Maruti Suzuki posts record monthly dispatch on SUV mix",
        source="Demo Wire",
        days_ago=2,
        tickers=["MARUTI"],
        sectors=["Auto"],
        sentiment=[("bullish", 0.75), ("growth_signal", 0.7), ("sector_tailwind", 0.5)],
    ),
    DemoNewsItem(
        title="Reliance retail GMV growth slows, JioMart restructuring continues",
        source="Demo Wire",
        days_ago=3,
        tickers=["RELIANCE"],
        sectors=["Conglomerate"],
        sentiment=[("bearish", 0.45), ("management_concern", 0.4)],
    ),
    DemoNewsItem(
        title="Sun Pharma's specialty business inflects; Ilumya growth above plan",
        source="Demo Wire",
        days_ago=5,
        tickers=["SUNPHARMA"],
        sectors=["Pharma"],
        sentiment=[("bullish", 0.78), ("growth_signal", 0.72), ("innovation_signal", 0.65)],
    ),
    DemoNewsItem(
        title="Vodafone Idea AGR dues clarification sought from DoT",
        source="Demo Wire",
        days_ago=1,
        tickers=["VODAIDEA"],
        sectors=["Telecom"],
        sentiment=[("bearish", 0.7), ("regulatory_risk", 0.85), ("debt_concern", 0.8)],
    ),
    DemoNewsItem(
        title="HUL prestige beauty BU outpacing core FMCG growth",
        source="Demo Wire",
        days_ago=4,
        tickers=["HINDUNILVR"],
        sectors=["FMCG"],
        sentiment=[("bullish", 0.6), ("growth_signal", 0.55), ("innovation_signal", 0.5)],
    ),
    DemoNewsItem(
        title="Asian Paints loses share to Birla Opus in tier-2 cities",
        source="Demo Wire",
        days_ago=2,
        tickers=["ASIANPAINT"],
        sectors=["Paints"],
        sentiment=[("bearish", 0.6), ("competitive_threat", 0.75)],
    ),
    DemoNewsItem(
        title="Indian IT sector outlook revised to neutral by Demo Brokerage",
        source="Demo Brokerage",
        days_ago=1,
        tickers=["TCS", "INFY", "HCLTECH", "WIPRO"],
        sectors=["IT"],
        sentiment=[("sector_headwind", 0.6)],
    ),
    DemoNewsItem(
        title="Cement majors signal pricing discipline post monsoon",
        source="Demo Wire",
        days_ago=2,
        tickers=["ULTRACEMCO"],
        sectors=["Cement"],
        sentiment=[("sector_tailwind", 0.55), ("bullish", 0.5)],
    ),
    DemoNewsItem(
        title="Bharti Airtel ARPU climbs to ₹211; 5G capex peak ahead",
        source="Demo Wire",
        days_ago=3,
        tickers=["BHARTIARTL"],
        sectors=["Telecom"],
        sentiment=[("bullish", 0.7), ("growth_signal", 0.6), ("debt_concern", 0.3)],
    ),
]


def now_minus(days_ago: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days_ago)
