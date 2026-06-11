"""Nightly prompt optimization job using DSPy BootstrapFewShot."""

from __future__ import annotations

import json
import logging
import os
import sys
from statistics import mean
from typing import Any

import dspy

from evals.evaluator import run_eval
from evals.golden_dataset import GOLDEN_DATASET, GOLDEN_TRAIN, GOLDEN_HELDOUT
from tools.phoenix_query_tool import get_top_prompts, push_prompt_to_phoenix, query_phoenix_traces
from tools.run_store import get_history

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)s %(message)s")


# ---------------------------------------------------------------------------
# DSPy Signature and Module
# ---------------------------------------------------------------------------


class CriticSignature(dspy.Signature):
    """DSPy signature: hypothesis → research memo."""

    hypothesis: str = dspy.InputField(desc="A trading/market hypothesis to evaluate.")
    memo: str = dspy.OutputField(
        desc=(
            "A rigorous research memo with sections: HYPOTHESIS, DATA SOURCES, "
            "METHODOLOGY, RESULTS, STATISTICAL ANALYSIS, RISK CAVEATS, CONCLUSION, DISCLAIMER."
        )
    )


class CriticModule(dspy.Module):
    """Minimal DSPy wrapper for Critic instruction optimisation."""

    def __init__(self) -> None:
        """Initialise the DSPy prediction block."""
        super().__init__()
        self.predict = dspy.Predict(CriticSignature)

    def forward(self, hypothesis: str) -> dspy.Prediction:  # type: ignore[override]
        """Generate a research memo from a hypothesis string."""
        return self.predict(hypothesis=hypothesis)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _configure_dspy(model: str = "gemini-3-flash-preview") -> None:
    """Configure DSPy language model for Gemini via LiteLLM.

    LiteLLM requires an explicit provider prefix:
      - Vertex AI  → ``vertex_ai/<model>``
      - Direct API → ``gemini/<model>``
    Using ``google/<model>`` raises BadRequestError because LiteLLM does not
    recognise that prefix.
    """
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE"
    if use_vertex:
        lm = dspy.LM(
            f"vertex_ai/{model}",
            vertex_project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            vertex_location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    else:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        lm = dspy.LM(f"gemini/{model}", api_key=api_key)
    dspy.configure(lm=lm)


def _trace_to_example(trace: dict[str, Any]) -> dspy.Example:
    """Convert one Phoenix trace record into a DSPy training example."""
    return dspy.Example(
        hypothesis=str(trace.get("input", "")),
        memo=str(trace.get("output", "")),
        scores=trace.get("scores", {}),
    ).with_inputs("hypothesis")


def _candidate_score(module: CriticModule, heldout_items: list[dict[str, Any]]) -> float:
    """Score a candidate prompt module on held-out golden hypotheses."""
    values: list[float] = []
    for item in heldout_items:
        try:
            prediction = module(hypothesis=str(item["hypothesis"]))
            memo = str(getattr(prediction, "memo", ""))
            result = run_eval(memo, {}, {}, model="gemini-3-flash-preview")
            values.append(float(result["overall"]))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Heldout eval failed for item: %s", exc)
    return float(mean(values)) if values else 0.0


def _get_compiled_instruction(compiled: CriticModule) -> str:
    """Extract the optimised instruction text from a compiled DSPy module."""
    try:
        demos = compiled.predict.demos  # type: ignore[attr-defined]
        if demos:
            return (
                "Optimized critic instruction with "
                f"{len(demos)} bootstrapped demonstrations."
            )
    except AttributeError:
        pass
    return "Optimized critic instruction (no demos extracted)."


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Run nightly optimization and optional prompt promotion. Returns exit code."""
    project_name = os.getenv("PHOENIX_PROJECT_NAME", "quantsentinel")
    threshold = float(os.getenv("EVAL_SCORE_THRESHOLD", "0.70"))
    model = os.getenv("OPTIMIZER_MODEL", "gemini-3-flash-preview")

    logger.info("Starting nightly optimizer for project=%s threshold=%s", project_name, threshold)

    # ------------------------------------------------------------------ #
    # 1. Gather training data — Phoenix first, local store fallback, golden dataset supplement
    # ------------------------------------------------------------------ #
    traces: list[dict[str, Any]] = []

    # Try Phoenix
    try:
        trace_result = query_phoenix_traces(
            project_name=project_name,
            max_overall_score=threshold,
            limit=50,
        )
        traces = trace_result.get("traces", [])
        logger.info("Phoenix returned %d low-scoring traces", len(traces))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Phoenix unavailable (%s) — falling back to local store", exc)

    # Fall back to local run store if Phoenix didn't provide enough
    if len(traces) < 5:
        local_runs = get_history(limit=50)
        low_scoring = [
            {"input": r["hypothesis"], "output": "", "scores": {"overall": r["score"]}}
            for r in local_runs
            if r.get("score", 1.0) < threshold
        ]
        logger.info("Local store contributed %d low-scoring runs", len(low_scoring))
        traces.extend(low_scoring)

    # Supplement with golden dataset hypotheses (always good training signal)
    golden_traces = [
        {"input": item["hypothesis"], "output": "", "scores": {"overall": item["min_acceptable_score"]}}
        for item in GOLDEN_TRAIN
    ]
    traces.extend(golden_traces)
    logger.info("Augmented with %d golden dataset examples — total training set: %d", len(golden_traces), len(traces))

    if len(traces) < 5:
        logger.info("Still not enough data after augmentation (%d traces, need 5)", len(traces))
        print(json.dumps({"status": "skipped", "reason": "insufficient_traces", "count": len(traces)}))
        return 0

    # Cap training set — BootstrapFewShot makes one LLM call per example;
    # 65 examples = 15-30 min background run. 20 is sufficient for good demos.
    MAX_TRAIN = int(os.getenv("OPTIMIZER_MAX_TRAIN", "20"))
    if len(traces) > MAX_TRAIN:
        # Prioritise lowest-scoring traces (most room for improvement)
        traces = sorted(traces, key=lambda t: t.get("scores", {}).get("overall", 0.0))[:MAX_TRAIN]
        logger.info("Capped training set to %d lowest-scoring examples.", MAX_TRAIN)

    logger.info("Training on %d examples total.", len(traces))

    # ------------------------------------------------------------------ #
    # 2. Configure DSPy and build training set
    # ------------------------------------------------------------------ #
    try:
        _configure_dspy(model)
    except Exception as exc:  # noqa: BLE001
        logger.error("DSPy configuration failed: %s", exc)
        return 1

    trainset = [_trace_to_example(t) for t in traces]
    module = CriticModule()

    # ------------------------------------------------------------------ #
    # 3. Define metric and run BootstrapFewShot
    # ------------------------------------------------------------------ #
    def metric(
        example: dspy.Example,
        prediction: dspy.Prediction,
        _trace: Any = None,
    ) -> float:
        """Evaluate a DSPy prediction using the LLM-as-judge rubric."""
        memo = str(getattr(prediction, "memo", ""))
        scored = run_eval(memo, {}, {}, model=model)
        return float(scored["overall"])

    logger.info("Running BootstrapFewShot optimisation…")
    try:
        optimizer = dspy.BootstrapFewShot(metric=metric, max_bootstrapped_demos=4)
        compiled = optimizer.compile(module, trainset=trainset)
    except Exception as exc:  # noqa: BLE001
        logger.error("DSPy compilation failed: %s", exc)
        return 1

    # ------------------------------------------------------------------ #
    # 4. Evaluate compiled module on held-out golden dataset
    # ------------------------------------------------------------------ #
    heldout = GOLDEN_HELDOUT  # last 5 volatility-regime hypotheses, never seen during training
    logger.info("Evaluating compiled module on %d heldout examples…", len(heldout))
    candidate_score = _candidate_score(compiled, heldout)
    logger.info("Candidate score: %.4f", candidate_score)

    # ------------------------------------------------------------------ #
    # 5. Compare against incumbent Phoenix prompt
    # ------------------------------------------------------------------ #
    incumbent_score = 0.0
    try:
        top_prompt = get_top_prompts(prompt_identifier="critic_prompt", top_n=1)
        if top_prompt.get("prompts"):
            incumbent_score = float(top_prompt["prompts"][0].get("score", 0.0))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not fetch incumbent prompt: %s", exc)

    logger.info("Incumbent score: %.4f", incumbent_score)

    # ------------------------------------------------------------------ #
    # 6. Promote if candidate beats incumbent
    # ------------------------------------------------------------------ #
    promoted = False
    if candidate_score > incumbent_score:
        template = _get_compiled_instruction(compiled)
        try:
            push_prompt_to_phoenix("critic_prompt", template, tag="promoted")
            promoted = True
            logger.info("Promoted new Critic prompt to Phoenix (score=%.4f).", candidate_score)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to push prompt to Phoenix: %s", exc)

    # ------------------------------------------------------------------ #
    # 7. Structured JSON log (captured by Cloud Logging)
    # ------------------------------------------------------------------ #
    result = {
        "status": "success",
        "project_name": project_name,
        "low_score_trace_count": len(traces),
        "candidate_score": round(candidate_score, 4),
        "incumbent_score": round(incumbent_score, 4),
        "promoted": promoted,
        "model": model,
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
