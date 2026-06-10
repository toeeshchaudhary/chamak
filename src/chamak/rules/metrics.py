"""Registry of metrics the rule language can reference.

Each entry carries:
  - a short `label` (financial term, e.g. "ROE")
  - a `plain` label (everyday term, e.g. "Return on each rupee of equity")
  - `phrase_high` / `phrase_low` — used when translating a rule into prose:
      "ROE > 15"  → "ROE is at least 15%"               (terse)
      "ROE > 15"  → "the company earns at least ₹15 of profit per ₹100 of equity"  (plain)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    plain: str
    unit: str
    category: str
    higher_better: bool
    k: float = 4.0
    # Plain-English fragments — used when rendering rules to prose.
    # Should fit as: "{phrase_high} {value}{unit_suffix}"
    phrase_high: str = ""   # e.g. "earns at least"
    phrase_low: str = ""    # e.g. "owes less than"
    unit_suffix: str = ""   # e.g. "%", "×", "x net worth"

    @property
    def display(self) -> str:
        return f"{self.label} ({self.unit})"


# Canonical metric keys are lowercase_snake_case.
REGISTRY: dict[str, MetricSpec] = {m.key: m for m in [
    # Valuation
    MetricSpec("pe", "P/E", "Price vs annual profit",
               unit="x", category="valuation", higher_better=False, k=3.0,
               phrase_high="trades at over",
               phrase_low="trades at no more than",
               unit_suffix="× earnings"),
    MetricSpec("pb", "P/B", "Price vs accounting net worth",
               unit="x", category="valuation", higher_better=False, k=3.0,
               phrase_high="trades at more than",
               phrase_low="trades at no more than",
               unit_suffix="× book value"),
    MetricSpec("ps", "P/S", "Price vs annual sales",
               unit="x", category="valuation", higher_better=False, k=3.0,
               phrase_high="trades at more than",
               phrase_low="trades at no more than",
               unit_suffix="× sales"),
    MetricSpec("ev_ebitda", "EV/EBITDA", "Enterprise value vs cash earnings",
               unit="x", category="valuation", higher_better=False, k=3.0,
               phrase_high="is priced above",
               phrase_low="is priced at no more than",
               unit_suffix="× operating profit"),
    MetricSpec("peg", "PEG", "Price-to-earnings vs growth",
               unit="x", category="valuation", higher_better=False, k=4.0,
               phrase_high="has a PEG over",
               phrase_low="has a PEG under"),
    MetricSpec("dividend_yield", "Dividend Yield", "Annual cash you get per ₹100 invested",
               unit="percent", category="valuation", higher_better=True, k=3.0,
               phrase_high="pays a dividend of at least",
               phrase_low="pays a dividend below",
               unit_suffix="%"),

    # Profitability
    MetricSpec("roe", "ROE", "Profit earned on shareholders' money",
               unit="percent", category="profitability", higher_better=True, k=4.0,
               phrase_high="earns at least",
               phrase_low="earns less than",
               unit_suffix="% on shareholder equity"),
    MetricSpec("roce", "ROCE", "Profit earned on all capital used",
               unit="percent", category="profitability", higher_better=True, k=4.0,
               phrase_high="earns at least",
               phrase_low="earns less than",
               unit_suffix="% on total capital"),
    MetricSpec("roa", "ROA", "Profit per rupee of assets",
               unit="percent", category="profitability", higher_better=True, k=4.0,
               phrase_high="earns at least",
               phrase_low="earns less than",
               unit_suffix="% on assets"),
    MetricSpec("net_margin", "Net Margin", "Profit kept per rupee of sales",
               unit="percent", category="profitability", higher_better=True, k=4.0,
               phrase_high="keeps at least",
               phrase_low="keeps less than",
               unit_suffix="% of every sale as profit"),
    MetricSpec("operating_margin", "Operating Margin", "Operating profit per rupee of sales",
               unit="percent", category="profitability", higher_better=True, k=4.0,
               phrase_high="has operating margins above",
               phrase_low="has operating margins under",
               unit_suffix="%"),
    MetricSpec("gross_margin", "Gross Margin", "Gross profit per rupee of sales",
               unit="percent", category="profitability", higher_better=True, k=4.0,
               phrase_high="has gross margins above",
               phrase_low="has gross margins under",
               unit_suffix="%"),

    # Growth
    MetricSpec("revenue_growth", "Revenue Growth (YoY)", "Sales growth over last year",
               unit="percent", category="growth", higher_better=True, k=3.0,
               phrase_high="grew sales by at least",
               phrase_low="grew sales by less than",
               unit_suffix="% last year"),
    MetricSpec("earnings_growth", "Earnings Growth (YoY)", "Profit growth over last year",
               unit="percent", category="growth", higher_better=True, k=3.0,
               phrase_high="grew profits by at least",
               phrase_low="grew profits by less than",
               unit_suffix="% last year"),
    MetricSpec("revenue_cagr_3y", "Revenue CAGR (3y)", "Sales growth over 3 years",
               unit="percent", category="growth", higher_better=True, k=3.0,
               phrase_high="has compounded sales at",
               phrase_low="grew sales slower than",
               unit_suffix="% / year (3y)"),
    MetricSpec("eps_cagr_3y", "EPS CAGR (3y)", "Per-share profit growth over 3 years",
               unit="percent", category="growth", higher_better=True, k=3.0,
               phrase_high="has compounded EPS at",
               phrase_low="grew EPS slower than",
               unit_suffix="% / year (3y)"),

    # Leverage / safety
    MetricSpec("debt_to_equity", "Debt/Equity", "How much it owes vs. its own money",
               unit="ratio", category="leverage", higher_better=False, k=5.0,
               phrase_high="owes more than",
               phrase_low="owes less than",
               unit_suffix="× its net worth"),
    MetricSpec("interest_coverage", "Interest Coverage", "How easily it can pay interest",
               unit="x", category="leverage", higher_better=True, k=3.0,
               phrase_high="covers interest at least",
               phrase_low="covers interest under",
               unit_suffix="× over"),
    MetricSpec("current_ratio", "Current Ratio", "Short-term assets vs short-term bills",
               unit="ratio", category="leverage", higher_better=True, k=4.0,
               phrase_high="has short-term assets above",
               phrase_low="has short-term assets below",
               unit_suffix="× its short-term bills"),
    MetricSpec("quick_ratio", "Quick Ratio", "Cash + receivables vs short-term bills",
               unit="ratio", category="leverage", higher_better=True, k=4.0,
               phrase_high="has liquid assets above",
               phrase_low="has liquid assets below",
               unit_suffix="× its short-term bills"),

    # Quality / cashflow
    MetricSpec("fcf_yield", "FCF Yield", "Real cash earned per ₹100 invested",
               unit="percent", category="quality", higher_better=True, k=3.0,
               phrase_high="throws off at least",
               phrase_low="throws off less than",
               unit_suffix="% in real cash each year"),
    MetricSpec("promoter_holding", "Promoter Holding", "Stake owned by the founders/family",
               unit="percent", category="quality", higher_better=True, k=3.0,
               phrase_high="has owners holding at least",
               phrase_low="has owners holding less than",
               unit_suffix="% of the company"),
    MetricSpec("pledged_pct", "Pledged Shares %", "Owner shares pledged to lenders",
               unit="percent", category="quality", higher_better=False, k=6.0,
               phrase_high="has owners who pledged more than",
               phrase_low="has owners who pledged less than",
               unit_suffix="% of their stake"),
    MetricSpec("years_since_listing", "Years Listed", "How long it's been a public company",
               unit="years", category="quality", higher_better=True, k=2.0,
               phrase_high="has been listed at least",
               phrase_low="has been listed less than",
               unit_suffix=" years"),

    # Size / price
    MetricSpec("market_cap_cr", "Market Cap", "Total market value of the company",
               unit="rupees_cr", category="size", higher_better=True, k=1.0,
               phrase_high="is worth at least ₹",
               phrase_low="is worth less than ₹",
               unit_suffix=" crore"),
    MetricSpec("price", "Last Price", "Current share price",
               unit="rupees", category="price", higher_better=True, k=1.0,
               phrase_high="trades above ₹",
               phrase_low="trades below ₹"),
    MetricSpec("beta", "Beta", "How much it moves vs the market",
               unit="x", category="price", higher_better=False, k=3.0,
               phrase_high="swings more than",
               phrase_low="swings less than",
               unit_suffix="× the market"),
]}


def get(key: str) -> MetricSpec | None:
    return REGISTRY.get(key.lower())


def keys() -> list[str]:
    return sorted(REGISTRY.keys())


def by_category() -> dict[str, list[MetricSpec]]:
    out: dict[str, list[MetricSpec]] = {}
    for m in REGISTRY.values():
        out.setdefault(m.category, []).append(m)
    for v in out.values():
        v.sort(key=lambda m: m.label)
    return out
