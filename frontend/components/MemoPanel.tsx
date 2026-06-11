"use client";

import React from "react";

type Props = {
  memo: string;
  traceUrl?: string | null;
};

const SECTION_COLORS: Record<string, string> = {
  "1. HYPOTHESIS": "#58a6ff",
  "2. DATA SOURCES": "#3fb950",
  "3. METHODOLOGY": "#bc8cff",
  "4. RESULTS": "#d29922",
  "5. STATISTICAL ANALYSIS": "#f78166",
  "6. RISK CAVEATS": "#ff7b72",
  "7. CONCLUSION": "#58a6ff",
  "8. DISCLAIMER": "#8b949e",
};

function parseAndRenderMemo(text: string): React.ReactNode[] {
  if (!text) return [];
  const lines = text.split("\n");
  const nodes: React.ReactNode[] = [];
  let inSection = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Detect section headers
    const matchedHeader = Object.keys(SECTION_COLORS).find((h) =>
      trimmed.startsWith(h) || trimmed.toUpperCase().startsWith(h.replace(/^\d+\. /, ""))
    );

    if (matchedHeader) {
      const color = SECTION_COLORS[matchedHeader];
      nodes.push(
        <div key={`h-${i}`} className="mt-4 first:mt-0">
          <div
            className="mb-1 inline-block rounded px-2 py-0.5 text-xs font-semibold uppercase tracking-wider"
            style={{ backgroundColor: `${color}20`, color }}
          >
            {trimmed}
          </div>
        </div>
      );
      inSection = true;
    } else if (trimmed.startsWith("- ")) {
      // Bullet point
      nodes.push(
        <div key={`b-${i}`} className="flex items-start gap-2 py-0.5">
          <span className="mt-1 shrink-0 text-xs" style={{ color: "var(--accent-blue)" }}>•</span>
          <span className="text-xs leading-relaxed" style={{ color: "var(--text-primary)" }}>
            {trimmed.slice(2)}
          </span>
        </div>
      );
    } else if (trimmed === "") {
      if (inSection) {
        nodes.push(<div key={`sp-${i}`} className="h-1" />);
      }
    } else {
      // Key-value pairs (e.g. "sharpe: 0.42")
      const kvMatch = trimmed.match(/^([a-zA-Z_\s]+):\s*(.+)$/);
      if (kvMatch) {
        nodes.push(
          <div key={`kv-${i}`} className="flex items-baseline gap-2 py-0.5">
            <span className="shrink-0 text-xs" style={{ color: "var(--text-muted)" }}>
              {kvMatch[1]}
            </span>
            <span
              className="font-mono text-xs font-medium"
              style={{ color: "var(--accent-blue)" }}
            >
              {kvMatch[2]}
            </span>
          </div>
        );
      } else {
        nodes.push(
          <p key={`p-${i}`} className="py-0.5 text-xs leading-relaxed" style={{ color: "var(--text-primary)" }}>
            {trimmed}
          </p>
        );
      }
    }
  }
  return nodes;
}

export default function MemoPanel({ memo, traceUrl }: Props) {
  return (
    <div
      className="rounded-3xl shadow-xl overflow-hidden"
      style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border)" }}
    >
      <div
        className="flex items-center justify-between border-b px-5 py-3"
        style={{ borderColor: "var(--border)" }}
      >
        <h2
          className="font-heading text-lg font-semibold"
          style={{ color: "var(--text-primary)" }}
        >
          Research Memo
        </h2>
        {traceUrl && (
          <a
            href={traceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded px-2 py-0.5 text-xs transition-opacity hover:opacity-80"
            style={{ color: "var(--accent-blue)", backgroundColor: "rgba(88,166,255,0.1)" }}
          >
            View Phoenix Trace ↗
          </a>
        )}
      </div>

      <div className="max-h-[500px] overflow-y-auto p-5">
        {!memo ? (
          <p className="text-xs italic" style={{ color: "var(--text-muted)" }}>
            The research memo will appear here after the Critic agent completes.
          </p>
        ) : (
          <div>{parseAndRenderMemo(memo)}</div>
        )}
      </div>
    </div>
  );
}
