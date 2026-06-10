"""Three plain-English quiz questions that drive the simple-mode style builder.

Each option maps to a list of "rule specs" (metric/op/value/weight). When
the user finishes the quiz we just stack the chosen specs into a fresh
mind map snapshot and persist it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RuleSpec:
    metric: str
    op: str
    value: float
    weight: float = 1.0
    polarity: str = "prefer"


@dataclass(frozen=True)
class Choice:
    key: str
    title: str
    blurb: str
    icon: str  # single-glyph mood marker
    belief_label: str
    belief_description: str
    rules: list[RuleSpec] = field(default_factory=list)


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    choices: list[Choice]


QUESTIONS: list[Question] = [
    Question(
        id="vibe",
        text="When you think about money, which sounds most like you?",
        choices=[
            Choice(
                key="cautious",
                title="Careful",
                blurb="I'd rather not lose it than try to double it.",
                icon="▣",
                belief_label="Safety first",
                belief_description="Avoid risky bets — keep what you've got.",
                rules=[
                    RuleSpec("debt_to_equity", "<", 0.5, weight=1.5),
                    RuleSpec("current_ratio", ">", 1.5, weight=0.8),
                    RuleSpec("beta", "<", 1.0, weight=0.7),
                ],
            ),
            Choice(
                key="balanced",
                title="Balanced",
                blurb="Some ups and downs are fine if it's the right business.",
                icon="◆",
                belief_label="Steady and solid",
                belief_description="Decent returns, sensible risks.",
                rules=[
                    RuleSpec("roe", ">", 12, weight=1.1),
                    RuleSpec("debt_to_equity", "<", 1.0, weight=1.0),
                ],
            ),
            Choice(
                key="bold",
                title="Bold",
                blurb="Big swings don't scare me — I want growth.",
                icon="▲",
                belief_label="Growth seeker",
                belief_description="I'll ride volatility for upside.",
                rules=[
                    RuleSpec("revenue_growth", ">", 15, weight=1.5),
                    RuleSpec("earnings_growth", ">", 15, weight=1.2),
                ],
            ),
        ],
    ),
    Question(
        id="like",
        text="Which kind of business sounds more exciting to own a slice of?",
        choices=[
            Choice(
                key="steady",
                title="A steady business",
                blurb="Boring but profitable — the kind that's been around forever.",
                icon="◼",
                belief_label="Steady operator",
                belief_description="Quality companies with long track records.",
                rules=[
                    RuleSpec("roce", ">", 15, weight=1.2),
                    RuleSpec("years_since_listing", ">", 10, weight=0.7),
                ],
            ),
            Choice(
                key="fast",
                title="A fast-growing business",
                blurb="The next big thing — exciting, not always profitable yet.",
                icon="◢",
                belief_label="Growth machine",
                belief_description="Top-line growth tells the story.",
                rules=[
                    RuleSpec("revenue_growth", ">", 12, weight=1.3),
                    RuleSpec("revenue_cagr_3y", ">", 15, weight=1.0),
                ],
            ),
            Choice(
                key="income",
                title="A business that pays me",
                blurb="Cash in my account every quarter, like rent from a tenant.",
                icon="◉",
                belief_label="Income from cash flow",
                belief_description="Dividends + real cash from operations.",
                rules=[
                    RuleSpec("dividend_yield", ">", 2.5, weight=1.5),
                    RuleSpec("fcf_yield", ">", 3, weight=1.0),
                ],
            ),
        ],
    ),
    Question(
        id="price",
        text="When you go shopping, which one feels right?",
        choices=[
            Choice(
                key="cheap",
                title="I look for deals",
                blurb="Why pay full price? I want a bargain.",
                icon="◀",
                belief_label="Bargain hunter",
                belief_description="Reasonable price beats hype.",
                rules=[
                    RuleSpec("pe", "<", 20, weight=1.2),
                    RuleSpec("pb", "<", 3, weight=0.8),
                ],
            ),
            Choice(
                key="fair",
                title="Fair price, fair quality",
                blurb="I'll pay what something's worth — no more, no less.",
                icon="●",
                belief_label="Fair value",
                belief_description="No premiums for hype; no chasing junk.",
                rules=[
                    RuleSpec("pe", "<", 30, weight=0.9),
                    RuleSpec("operating_margin", ">", 12, weight=1.0),
                ],
            ),
            Choice(
                key="quality",
                title="Quality is worth paying for",
                blurb="The best stuff isn't cheap — I'll pay up for it.",
                icon="▶",
                belief_label="Pay for quality",
                belief_description="A great business at fair price beats a fair business at any price.",
                rules=[
                    RuleSpec("roce", ">", 20, weight=1.3),
                    RuleSpec("operating_margin", ">", 18, weight=1.0),
                ],
            ),
        ],
    ),
]
