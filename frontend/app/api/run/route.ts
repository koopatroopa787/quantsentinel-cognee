import { NextRequest } from "next/server";

// Allow long-running SSE streams (ADK timeout + fallback can take several minutes)
export const maxDuration = 600; // seconds — respected by Vercel; no-op locally
export const dynamic = "force-dynamic";

const backendBase = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
// Total budget for one research run: ADK timeout (90s) + fallback (~60s) + margin
const REQUEST_TIMEOUT_MS = 300_000; // 5 minutes

/** Safe fetch wrapper — returns null on any network/HTTP error instead of throwing. */
async function safeFetch(url: string): Promise<Response | null> {
  try {
    const res = await fetch(url, {
      // Short timeout so a down backend doesn't block the whole page load
      signal: AbortSignal.timeout(4000),
    });
    return res;
  } catch {
    return null;
  }
}

export async function GET(request: NextRequest): Promise<Response> {
  const mode = request.nextUrl.searchParams.get("mode");
  if (mode !== "bootstrap") {
    return new Response(JSON.stringify({ error: "Unsupported mode" }), { status: 400 });
  }

  // Both Phoenix-backed endpoints may fail when Phoenix is offline — degrade gracefully
  const [historyRes, improvementRes] = await Promise.all([
    safeFetch(`${backendBase}/history`),
    safeFetch(`${backendBase}/improvement`),
  ]);

  let history: unknown[] = [];
  let improvementPoints: unknown[] = [];

  try {
    if (historyRes?.ok) {
      const historyData = await historyRes.json();
      history = (historyData.items ?? []).slice(0, 5).map((item: Record<string, unknown>) => ({
        // Support both local store format (hypothesis/score) and Phoenix trace format (input/scores.overall)
        hypothesis: (item.hypothesis as string) ?? (item.input as string) ?? "unknown",
        score: (item.score as number) ?? (item.scores as Record<string, number>)?.overall ?? 0,
        timestamp: (item.timestamp as string) ?? (item.created_at as string) ?? "",
      }));
    }
  } catch {
    // JSON parse failure — leave history empty
  }

  try {
    if (improvementRes?.ok) {
      const improvementData = await improvementRes.json();
      improvementPoints = improvementData.points ?? [];
    }
  } catch {
    // JSON parse failure — leave points empty
  }

  return new Response(
    JSON.stringify({ history, improvement: improvementPoints }),
    { headers: { "Content-Type": "application/json" } }
  );
}

export async function POST(request: NextRequest): Promise<Response> {
  let body: string;
  try {
    body = await request.text();
  } catch {
    return new Response(JSON.stringify({ error: "Failed to read request body" }), { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${backendBase}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      // Explicit timeout so the Node.js socket never silently drops the stream
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Backend unreachable";
    // Return a single SSE error event so the frontend's event loop terminates cleanly
    const errorSse = `event: error\ndata: ${JSON.stringify({ message: `Backend unreachable: ${message}` })}\n\n`;
    return new Response(errorSse, {
      status: 200, // keep 200 so the browser reads the body as SSE
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  }

  if (!upstream.body) {
    const errorSse = `event: error\ndata: ${JSON.stringify({ message: "Backend stream unavailable" })}\n\n`;
    return new Response(errorSse, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  }

  const stream = new TransformStream();
  upstream.body.pipeTo(stream.writable).catch(() => {
    // Swallow pipe errors (client disconnect, etc.)
  });

  return new Response(stream.readable, {
    status: upstream.status,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
