"use client";

import React from "react";

type Scores = {
  faithfulness: number;
  stats_correctness: number;
  hallucination: number;
  risk_caveats: number;
  overall: number;
};

type Props = { scores: Scores };

const RUBRICS: Array<{
  key: keyof Scores;
  label: string;
  description: string;
  color: (v: number) => string;
}> = [
  {
    key: "faithfulness",
    label: "Faithfulness",
    description: "Claims match backtest data",
    color: (v) => (v >= 0.7 ? "#3fb950" : v >= 0.4 ? "#d29922" : "#f85149"),
  },
  {
    key: "stats_correctness",
    label: "Statistical Correctness",
    description: "p-value and CI interpreted correctly",
    color: (v) => (v >= 0.7 ? "#3fb950" : v >= 0.4 ? "#d29922" : "#f85149"),
  },
  {
    key: "hallucination",
    label: "Hallucination",
    description: "All claims grounded in data",
    color: (v) => (v >= 0.7 ? "#3fb950" : v >= 0.4 ? "#d29922" : "#f85149"),
  },
  {
    key: "risk_caveats",
    label: "Risk Caveats",
    description: "≥3 specific risk factors present",
    color: (v) => (v >= 0.7 ? "#3fb950" : v >= 0.4 ? "#d29922" : "#f85149"),
  },
  {
    key: "overall",
    label: "Overall",
    description: "Weighted average of all rubrics",
    color: (v) => (v >= 0.7 ? "#3fb950" : v >= 0.4 ? "#d29922" : "#f85149"),
  },
];

function ScoreRow({
  label,
  description,
  value,
  barColor,
  isOverall,
}: {
  label: string;
  description: string;
  value: number;
  barColor: string;
  isOverall: boolean;
}) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className={`mb-3 ${isOverall ? "mt-4 border-t pt-4" : ""}`} style={isOverall ? { borderColor: "var(--border)" } : {}}>
      <div className="mb-1 flex items-baseline justify-between">
        <div>
          <span
            className={`text-xs ${isOverall ? "font-semibold" : "font-medium"}`}
            style={{ color: isOverall ? "var(--text-primary)" : "var(--text-secondary)" }}
          >
            {label}
          </span>
          {!isOverall && (
            <span className="ml-2 hidden text-xs sm:inline" style={{ color: "var(--text-muted)" }}>
              {description}
            </span>
          )}
        </div>
        <span
          className="font-mono text-xs font-semibold"
          style={{ color: barColor }}
        >
          {value === 0 ? "—" : value.toFixed(2)}
        </span>
      </div>
      <div
        className="h-1.5 w-full overflow-hidden rounded-full"
        style={{ backgroundColor: "var(--bg-surface)" }}
      >
        <div
          className="h-1.5 rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%`, backgroundColor: barColor }}
        />
      </div>
    </div>
  );
}

export default function EvalScoreCard({ scores }: Props) {
  return (
    <div
      className="rounded-3xl p-6 shadow-xl"
      style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border)" }}
    >
      <h2
        className="font-heading mb-5 text-lg font-semibold"
        style={{ color: "var(--text-primary)" }}
      >
        Eval Scores
      </h2>

      {RUBRICS.map((r) => (
        <ScoreRow
          key={r.key}
          label={r.label}
          description={r.description}
          value={scores[r.key]}
          barColor={r.color(scores[r.key])}
          isOverall={r.key === "overall"}
        />
      ))}

      {scores.overall > 0 && (
        <div
          className="mt-3 rounded-sm p-2 text-center text-xs"
          style={{
            backgroundColor:
              scores.overall >= 0.7
                ? "rgba(63,185,80,0.1)"
                : scores.overall >= 0.4
                ? "rgba(210,153,34,0.1)"
                : "rgba(248,81,73,0.1)",
            color:
              scores.overall >= 0.7
                ? "var(--accent-green)"
                : scores.overall >= 0.4
                ? "var(--accent-amber)"
                : "var(--accent-red)",
          }}
        >
          {scores.overall >= 0.7
            ? "✓ Memo quality meets threshold (≥0.70)"
            : scores.overall >= 0.4
            ? "⚠ Memo quality below threshold — may trigger revision"
            : "✗ Low quality — Critic should revise"}
        </div>
      )}
    </div>
  );
}
