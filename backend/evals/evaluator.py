"""Memo evaluator — LLM-as-judge via Gemini 3 Flash + deterministic fallback."""

from __future__ import annotations

import logging
import os
from typing import Any

from evals.judge_templates import get_templates

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Deterministic heuristic scorers (used as fallback and for speed)
# ---------------------------------------------------------------------------


def _contains_all_numbers(memo: str, backtest_result: dict[str, Any]) -> bool:
    """Check whether key numeric result fields appear in the memo text."""
    keys = ["total_return", "sharpe", "max_drawdown", "win_rate", "num_trades"]
    for key in keys:
        if key not in backtest_result:
            continue
        token = str(round(float(backtest_result[key]), 4))
        # Also accept the truncated integer version for num_trades
        if token not in memo and str(backtest_result[key]) not in memo:
            return False
    return True


def _score_stats_correctness(memo: str, stat_summary: dict[str, Any]) -> float:
    """Score whether the memo correctly reports statistical test outcomes."""
    lower = memo.lower()
    has_pvalue = "p_value" in lower or "p-value" in lower or "p value" in lower
    has_significance = (
        "significant" in lower
        or "significance" in lower
        or "confidence" in lower
    )
    has_bootstrap = "bootstrap" in lower or "confidence interval" in lower or "ci" in lower

    score = 0.0
    if has_pvalue:
        score += 0.4
    if has_significance:
        score += 0.4
    if has_bootstrap:
        score += 0.2

    # Verify the direction claim matches the actual significance result
    t_test = stat_summary.get("t_test", {})
    sig = t_test.get("significant_at_5pct", None)
    if sig is not None:
        if sig and ("not significant" in lower or "fail to reject" in lower):
            score -= 0.3  # claims not significant when it is
        if not sig and "significant" in lower and "not" not in lower and "fail" not in lower:
            score -= 0.2  # claims significant when it isn't

    # Check bootstrap CI interpretation
    boot = stat_summary.get("bootstrap", {})
    lower_ci = boot.get("lower", None)
    upper_ci = boot.get("upper", None)
    if lower_ci is not None and upper_ci is not None:
        ci_zero = lower_ci < 0 < upper_ci
        if ci_zero and "spans zero" not in lower and "includes zero" not in lower and "not statistically" not in lower:
            score -= 0.1  # CI spans zero but memo doesn't acknowledge it

    return max(0.0, min(1.0, score))


def _score_hallucination(memo: str, backtest_result: dict[str, Any]) -> float:
    """Score inversely to detected hallucination (1.0 = no hallucination)."""
    if not backtest_result:
        return 0.5
    required_sections = [
        "HYPOTHESIS", "DATA SOURCES", "METHODOLOGY",
        "RESULTS", "STATISTICAL ANALYSIS", "RISK CAVEATS",
        "CONCLUSION", "DISCLAIMER",
    ]
    present = sum(1 for s in required_sections if s in memo.upper())
    structural_score = present / len(required_sections)

    # Penalise if the memo cites numbers not present in backtest_result
    penalty = 0.0
    import re  # noqa: PLC0415
    memo_numbers = set(re.findall(r"\d+\.\d{3,}", memo))
    allowed = {
        str(round(float(backtest_result.get(k, 0)), 4))
        for k in ("total_return", "sharpe", "max_drawdown", "win_rate")
    }
    suspicious = memo_numbers - allowed
    if len(suspicious) > 5:
        penalty = 0.1  # minor hallucination risk

    return round(max(0.0, structural_score - penalty), 4)


def _score_risk_caveats(memo: str) -> float:
    """Score presence and specificity of risk caveat statements."""
    section_markers = ["RISK CAVEATS", "risk caveats"]
    if not any(marker in memo for marker in section_markers):
        return 0.0
    caveat_terms = [
        "overfitting", "transaction cost", "regime", "bias",
        "slippage", "liquidity", "survivorship", "look-ahead",
        "data snooping", "out-of-sample", "multiple testing",
        "parameter sensitivity", "execution", "market impact",
    ]
    hits = sum(1 for term in caveat_terms if term.lower() in memo.lower())
    if hits >= 5:
        return 1.0
    if hits >= 3:
        return 0.85
    if hits >= 1:
        return 0.5
    return 0.0


# ---------------------------------------------------------------------------
# Gemini LLM-as-judge (optional, activated when google-genai is importable)
# ---------------------------------------------------------------------------


def _llm_judge_score(
    template_prompt: str,
    labels: dict[str, float],
    memo: str,
    context: str,
    model: str,
) -> float | None:
    """
    Call Gemini Flash to score memo against a rubric template.

    Returns the numeric score mapped from the label, or None if the call fails.
    """
    try:
        import google.genai as genai  # noqa: PLC0415

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE"

        if use_vertex:
            client = genai.Client(
                vertexai=True,
                project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            )
        elif api_key:
            client = genai.Client(api_key=api_key)
        else:
            return None

        prompt = (
            f"{template_prompt}\n\n"
            f"=== CONTEXT / REFERENCE DATA ===\n{context}\n\n"
            f"=== RESEARCH MEMO ===\n{memo}\n\n"
            f"Respond with EXACTLY ONE of: {', '.join(labels.keys())}. "
            f"No other text."
        )

        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        label = response.text.strip().upper()
        # Try exact match first, then prefix match
        for key, score in labels.items():
            if label == key.upper():
                return score
        for key, score in labels.items():
            if label.startswith(key.upper()):
                return score
        return None

    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM judge call failed (%s: %s) — using heuristic fallback", type(exc).__name__, exc)
        return None


# ---------------------------------------------------------------------------
# Public evaluator
# ---------------------------------------------------------------------------


def _score_faithfulness(memo: str, backtest_result: dict[str, Any]) -> float:
    """Check all key numeric claims in the memo match the backtest data."""
    import re  # noqa: PLC0415
    base = 1.0 if _contains_all_numbers(memo, backtest_result) else 0.5

    # Penalise physically impossible values appearing in the memo
    dd_matches = re.findall(r"max_drawdown[:\s]+([0-9]+\.[0-9]+)", memo)
    for m in dd_matches:
        if float(m) > 1.0:
            base -= 0.3

    wr_matches = re.findall(r"win_rate[:\s]+([0-9]+\.[0-9]+)", memo)
    for m in wr_matches:
        if float(m) > 1.0:
            base -= 0.3

    return max(0.0, min(1.0, base))


def _score_overall(scores: dict[str, float], backtest_result: dict[str, Any]) -> float:
    """Weighted overall score that accounts for economic reasonableness and alpha."""
    raw = (
        scores["faithfulness"] * 0.30
        + scores["stats_correctness"] * 0.30
        + scores["hallucination"] * 0.25
        + scores["risk_caveats"] * 0.15
    )
    # Cap if physically impossible metric values appear
    wr = backtest_result.get("win_rate", 0)
    dd = backtest_result.get("max_drawdown", 0)
    if wr > 1.0 or dd > 1.0:
        raw = min(raw, 0.70)

    # Penalise significant benchmark underperformance (negative alpha)
    # A strategy that massively underperforms buy-and-hold is not a good research output
    alpha = backtest_result.get("alpha", None)
    if alpha is not None:
        if alpha < -0.5:   # strategy returned 50%+ less than benchmark
            raw = min(raw, 0.65)
        elif alpha < -0.2: # strategy returned 20%+ less than benchmark
            raw = min(raw, 0.80)
    elif backtest_result.get("benchmark_total_return") is not None:
        # compute inline if available
        bm = float(backtest_result["benchmark_total_return"])
        tr = float(backtest_result.get("total_return", 0))
        if tr - bm < -0.5:
            raw = min(raw, 0.65)
        elif tr - bm < -0.2:
            raw = min(raw, 0.80)

    return round(raw, 4)


def run_eval(
    memo: str,
    backtest_result: dict[str, Any],
    stat_summary: dict[str, Any],
    model: str = "gemini-3-flash-preview",
) -> dict[str, float]:
    """
    Evaluate a research memo using four rubric templates.

    Strategy:
    1. Try Gemini LLM-as-judge for each rubric.
    2. Fall back to deterministic heuristics if the LLM call fails.
    Returns a dict with five float scores in [0, 1].
    """
    templates = get_templates()
    context = json_safe_context(backtest_result, stat_summary)

    scores: dict[str, float] = {}

    # --- Faithfulness ---
    template = templates[0]
    llm_score = _llm_judge_score(template.prompt, template.labels, memo, context, model)
    scores["faithfulness"] = llm_score if llm_score is not None else (
        _score_faithfulness(memo, backtest_result)
    )

    # --- Statistical Correctness ---
    template = templates[1]
    llm_score = _llm_judge_score(template.prompt, template.labels, memo, context, model)
    scores["stats_correctness"] = llm_score if llm_score is not None else (
        _score_stats_correctness(memo, stat_summary)
    )

    # --- Hallucination (inverted — 1.0 = no hallucination) ---
    template = templates[2]
    llm_score = _llm_judge_score(template.prompt, template.labels, memo, context, model)
    scores["hallucination"] = llm_score if llm_score is not None else (
        _score_hallucination(memo, backtest_result)
    )

    # --- Risk Caveats ---
    template = templates[3]
    llm_score = _llm_judge_score(template.prompt, template.labels, memo, context, model)
    scores["risk_caveats"] = llm_score if llm_score is not None else (
        _score_risk_caveats(memo)
    )

    scores["overall"] = _score_overall(scores, backtest_result)
    return {k: float(v) for k, v in scores.items()}


def json_safe_context(
    backtest_result: dict[str, Any],
    stat_summary: dict[str, Any],
) -> str:
    """Serialise eval context dicts to a compact JSON string for LLM prompts."""
    import json  # noqa: PLC0415

    safe: dict[str, Any] = {}
    for key in ["total_return", "sharpe", "max_drawdown", "win_rate", "num_trades"]:
        if key in backtest_result:
            safe[key] = backtest_result[key]
    if stat_summary:
        safe["statistics"] = stat_summary
    return json.dumps(safe, default=str)
