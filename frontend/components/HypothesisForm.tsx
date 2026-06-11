"use client";

import React, { useState } from "react";

const EXAMPLE_HYPOTHESES = [
  "Does a 14-day RSI below 30 on SPY generate significant mean-reversion returns over 5 trading days from 2015 to 2024?",
  "Do small-cap stocks (IWM) outperform large-cap (SPY) in the 5 trading days following FOMC rate-hold announcements (2010–2024)?",
  "Does buying the S&P 500 on the first trading day of January and selling after 5 days generate excess returns versus buy-and-hold?",
  "Does a 50/200-day moving average crossover on QQQ generate risk-adjusted excess returns over buy-and-hold from 2010 to 2024?",
];

type Props = {
  onRun: (hypothesis: string) => Promise<void>;
  running: boolean;
};

export default function HypothesisForm({ onRun, running }: Props) {
  const [hypothesis, setHypothesis] = useState(EXAMPLE_HYPOTHESES[0]);
  const [showExamples, setShowExamples] = useState(false);

  function selectExample(h: string): void {
    setHypothesis(h);
    setShowExamples(false);
  }

  const canRun = !running && hypothesis.trim().length >= 5;

  return (
    <div
      className="rounded-3xl p-6 shadow-xl"
      style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border)" }}
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-heading text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
          Research Hypothesis
        </h2>
        <button
          className="rounded-md px-2 py-1 text-xs transition-colors hover:opacity-80"
          style={{
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border)",
            color: "var(--accent-blue)",
          }}
          onClick={() => setShowExamples((v) => !v)}
          type="button"
        >
          Examples ↓
        </button>
      </div>

      {/* Example dropdown */}
      {showExamples && (
        <div
          className="mb-3 rounded-sm p-2 text-xs"
          style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border)" }}
        >
          {EXAMPLE_HYPOTHESES.map((h, i) => (
            <button
              key={i}
              className="block w-full rounded px-2 py-1.5 text-left transition-colors hover:bg-opacity-50"
              style={{ color: "var(--text-primary)" }}
              onMouseEnter={(e) => ((e.target as HTMLElement).style.backgroundColor = "var(--bg-card)")}
              onMouseLeave={(e) => ((e.target as HTMLElement).style.backgroundColor = "transparent")}
              onClick={() => selectExample(h)}
              type="button"
            >
              {h}
            </button>
          ))}
        </div>
      )}

      <textarea
        id="hypothesis-input"
        className="h-36 w-full resize-none rounded-2xl p-4 text-sm outline-none transition-all focus:ring-1 focus:ring-[#00D1FF]/50 focus:shadow-[0_0_15px_rgba(0,209,255,0.15)]"
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid transparent",
          color: "var(--text-primary)",
          lineHeight: "1.6",
        }}
        value={hypothesis}
        onChange={(e) => setHypothesis(e.target.value)}
        placeholder="Enter a trading hypothesis to evaluate…"
      />

      <div className="mt-3 flex items-center gap-3">
        <button
          id="run-research-button"
          className="flex flex-1 items-center justify-center gap-2 rounded-xl px-4 py-3 font-heading text-base font-bold transition-all shadow-[0_0_20px_rgba(0,209,255,0.3)] hover:shadow-[0_0_30px_rgba(0,209,255,0.6)] hover:scale-[1.02] active:scale-[0.98] disabled:scale-100 disabled:shadow-none disabled:cursor-not-allowed disabled:opacity-40"
          style={{
            background: canRun
              ? "linear-gradient(135deg, #00D1FF, #0077FF)"
              : "rgba(17,17,17,0.5)",
            color: "#ffffff",
            border: canRun ? "none" : "1px solid rgba(255,255,255,0.05)",
          }}
          disabled={!canRun}
          onClick={() => onRun(hypothesis)}
          type="button"
        >
          {running ? (
            <>
              <span className="pulse-running inline-block h-2 w-2 rounded-full bg-amber-400" />
              Researching…
            </>
          ) : (
            <>⚡ Run Research</>
          )}
        </button>
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          {hypothesis.trim().length} chars
        </span>
      </div>
    </div>
  );
}
