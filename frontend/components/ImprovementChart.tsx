"use client";

import React from "react";
import {
  CartesianGrid,
  Area,
  AreaChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Point = {
  timestamp: string;
  overall: number;
};

type Props = { points: Point[] };

function formatDate(ts: string): string {
  try {
    return new Date(ts).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return ts;
  }
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const score = payload[0].value;
  const color = score >= 0.7 ? "#3fb950" : score >= 0.4 ? "#d29922" : "#f85149";
  return (
    <div
      className="rounded-sm p-3 text-xs shadow-lg"
      style={{
        backgroundColor: "var(--bg-card)",
        border: "1px solid var(--border)",
        color: "var(--text-primary)",
      }}
    >
      <p style={{ color: "var(--text-muted)" }}>{label}</p>
      <p className="mt-1 font-semibold" style={{ color }}>
        Overall: {score.toFixed(3)}
      </p>
    </div>
  );
}

// Synthetic demonstration data shown when no real traces exist yet
const DEMO_POINTS: Point[] = Array.from({ length: 12 }, (_, i) => ({
  timestamp: new Date(Date.now() - (11 - i) * 24 * 60 * 60 * 1000).toISOString(),
  overall: parseFloat((0.52 + i * 0.032 + (Math.random() - 0.5) * 0.04).toFixed(3)),
}));

export default function ImprovementChart({ points }: Props) {
  const data = points.length >= 1 ? points : DEMO_POINTS;
  const isDemo = points.length < 1;

  const chartData = data.map((p, i) => ({
    date: formatDate(p.timestamp),
    score: p.overall,
    run: i + 1,
  }));

  return (
    <div
      className="rounded-3xl p-6 shadow-xl"
      style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border)" }}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2
            className="font-heading text-lg font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            Self-Improvement
          </h2>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Eval score over time (nightly DSPy optimisation)
          </p>
        </div>
        {isDemo && (
          <span
            className="rounded-full px-2 py-0.5 text-xs"
            style={{
              backgroundColor: "rgba(88,166,255,0.1)",
              color: "var(--accent-blue)",
            }}
          >
            demo data
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
          <defs>
            <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.4}/>
              <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: "var(--text-muted)" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 1]}
            tick={{ fontSize: 10, fill: "var(--text-muted)" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => v.toFixed(1)}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            y={0.7}
            stroke="var(--accent-green)"
            strokeDasharray="4 4"
            strokeOpacity={0.5}
            label={{ value: "threshold", fill: "var(--accent-green)", fontSize: 9 }}
          />
          <Area
            type="monotone"
            dataKey="score"
            stroke="var(--accent-blue)"
            fillOpacity={1}
            fill="url(#colorScore)"
            strokeWidth={2}
            dot={{ fill: "var(--accent-blue)", r: 3, strokeWidth: 0 }}
            activeDot={{ r: 5, fill: "var(--accent-blue)", stroke: "rgba(0,209,255,0.5)", strokeWidth: 4 }}
            style={{ filter: "drop-shadow(0 0 8px rgba(0,209,255,0.4))" }}
          />
        </AreaChart>
      </ResponsiveContainer>

      <div className="mt-3 flex items-center gap-4 text-xs" style={{ color: "var(--text-muted)" }}>
        <span className="flex items-center gap-1">
          <span className="h-0.5 w-4 rounded" style={{ backgroundColor: "var(--accent-blue)" }} />
          Overall score
        </span>
        <span className="flex items-center gap-1">
          <span className="h-0.5 w-4 rounded" style={{ backgroundColor: "var(--accent-green)", opacity: 0.6 }} />
          0.70 threshold
        </span>
      </div>
    </div>
  );
}
