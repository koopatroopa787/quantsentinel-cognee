"""Judge templates for memo quality scoring."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JudgeTemplate:
    """Simple rubric template representation."""

    name: str
    prompt: str
    labels: dict[str, float]


FAITHFULNESS_TEMPLATE = JudgeTemplate(
    name="faithfulness",
    prompt=(
        "You are a strict quantitative research auditor.\n"
        "Check: (1) Do ALL numeric values in the memo (returns, Sharpe, drawdown, p-value, CI bounds) "
        "exactly match the reference data? (2) Is the drawdown reported as a fraction in [0,1]? "
        "(3) Is the win rate reported as a fraction in [0,1]? (4) Does the methodology description "
        "match what the hypothesis is actually testing (e.g., a FOMC hypothesis must not just say "
        "'mean-reversion signal' without mentioning FOMC)?\n"
        "Respond PASS only if ALL four checks pass. Respond PARTIAL if numbers match but methodology "
        "or framing is imprecise. Respond FAIL if numbers are wrong or physically impossible values appear."
    ),
    labels={"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0},
)

STATS_CORRECTNESS_TEMPLATE = JudgeTemplate(
    name="stats_correctness",
    prompt=(
        "You are a senior statistician reviewing a research memo.\n"
        "Check: (1) Is the p-value significance conclusion correct (significant if p<0.05, not significant otherwise)? "
        "(2) Is the bootstrap CI interpretation correct (if CI spans zero, the edge is not reliably positive)? "
        "(3) Does the confidence level (high/medium/low) align with the statistical evidence? "
        "(4) Are Sharpe ratio and total return discussed in context of each other?\n"
        "Respond PASS if all four checks pass. PARTIAL if 2-3 pass. FAIL if the significance "
        "conclusion contradicts the p-value."
    ),
    labels={"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0},
)

HALLUCINATION_TEMPLATE = JudgeTemplate(
    name="hallucination",
    prompt=(
        "You are a fact-checker for quantitative research.\n"
        "Check: (1) Are all numeric claims traceable to the reference data provided? "
        "(2) Does the memo avoid inventing facts about the market or the strategy not supported by the data? "
        "(3) Is the ticker and date range mentioned correctly? "
        "(4) Does the conclusion avoid overclaiming (e.g., calling a strategy 'profitable' when total_return "
        "or Sharpe is mediocre)?\n"
        "Respond NO_HALLUCINATION if all four checks pass. MINOR if there is vague or imprecise language "
        "but no invented numbers. MAJOR if numbers are fabricated or the conclusion contradicts the data."
    ),
    labels={"NO_HALLUCINATION": 1.0, "MINOR": 0.5, "MAJOR": 0.0},
)

RISK_CAVEATS_TEMPLATE = JudgeTemplate(
    name="risk_caveats",
    prompt=(
        "You are evaluating whether a research memo adequately discloses risk.\n"
        "Check: (1) Are at least 3 specific, named risk factors listed (not just generic statements)? "
        "(2) Does at least one caveat relate specifically to the strategy type tested "
        "(e.g., event-study risk for FOMC, look-ahead bias for SMA, RSI parameter sensitivity)? "
        "(3) Are overfitting and out-of-sample testing mentioned? "
        "(4) Are transaction costs and slippage mentioned?\n"
        "Respond FULL if all four checks pass. PARTIAL if 2-3 pass. NONE if fewer than 2 pass."
    ),
    labels={"FULL": 1.0, "PARTIAL": 0.5, "NONE": 0.0},
)


def get_templates() -> list[JudgeTemplate]:
    """Return all scoring templates in fixed order."""
    return [
        FAITHFULNESS_TEMPLATE,
        STATS_CORRECTNESS_TEMPLATE,
        HALLUCINATION_TEMPLATE,
        RISK_CAVEATS_TEMPLATE,
    ]

