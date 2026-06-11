"""Chart generation helper tools — dark-theme styled output."""

from __future__ import annotations

import base64
import io

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.style as mstyle
import numpy as np

matplotlib.use("Agg")  # Non-interactive backend for server use


def generate_equity_curve_chart(
    equity_curve: list[float],
    dates: list[str],
    title: str,
) -> str:
    """
    Generate a dark-theme base64 PNG chart for the equity curve.

    Parameters
    ----------
    equity_curve:
        Normalised portfolio values (starting at 1.0).
    dates:
        List of date strings aligned with equity_curve entries.
    title:
        Chart title string.

    Returns
    -------
    str
        Base64-encoded PNG image string (no data: prefix).
    """
    # Downsample for very long series to keep chart readable
    max_points = 500
    if len(equity_curve) > max_points:
        step = max(1, len(equity_curve) // max_points)
        equity_curve = equity_curve[::step]
        dates = dates[::step]

    fig, ax = plt.subplots(figsize=(10, 4), dpi=120)
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#161b22")

    xs = range(len(equity_curve))

    # Gradient fill under the curve
    ax.fill_between(
        xs,
        1.0,
        equity_curve,
        where=[v >= 1.0 for v in equity_curve],
        alpha=0.15,
        color="#3fb950",
        interpolate=True,
    )
    ax.fill_between(
        xs,
        1.0,
        equity_curve,
        where=[v < 1.0 for v in equity_curve],
        alpha=0.15,
        color="#f85149",
        interpolate=True,
    )

    # Main equity curve line
    ax.plot(xs, equity_curve, color="#58a6ff", linewidth=1.8, zorder=5)

    # Baseline
    ax.axhline(y=1.0, color="#484f58", linestyle="--", linewidth=0.8, alpha=0.7)

    # Draw end-point marker
    if equity_curve:
        final = equity_curve[-1]
        dot_color = "#3fb950" if final >= 1.0 else "#f85149"
        ax.scatter([len(equity_curve) - 1], [final], color=dot_color, s=40, zorder=6)

    # Styling
    ax.set_title(title, color="#e6edf3", fontsize=11, pad=10)
    ax.set_xlabel("", color="#8b949e")
    ax.set_ylabel("Portfolio Value", color="#8b949e", fontsize=9)
    ax.tick_params(colors="#484f58", labelsize=8)
    ax.spines[["top", "right", "left", "bottom"]].set_color("#21262d")
    ax.grid(color="#21262d", alpha=0.6, linewidth=0.5)

    # X-axis date labels — show ~8 evenly spaced
    n = len(dates)
    if n > 8:
        step = max(1, n // 8)
        tick_positions = list(range(0, n, step))
        tick_labels = [dates[i] for i in tick_positions]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=30, ha="right", fontsize=7, color="#8b949e")
    else:
        ax.set_xticks(list(range(n)))
        ax.set_xticklabels(dates, rotation=30, ha="right", fontsize=7, color="#8b949e")

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode()
