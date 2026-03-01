"""Waterfall chart utilities for per-order unit economics visualization."""

from __future__ import annotations

import plotly.graph_objects as go

from src.model import UnitEconInputs, UnitEconOutputs, compute_contribution_margin_per_order


# ── Colors ────────────────────────────────────────────────────────────────────

GREEN = "#10B981"
RED = "#EF4444"
BLUE = "#3B82F6"
PLOTLY_TEMPLATE = "plotly_white"


def build_waterfall_data(inputs: UnitEconInputs) -> dict:
    """Build data for a per-order waterfall chart.

    Returns dict with keys: labels, values, measures, text.
    """
    revenue = inputs.aov
    cogs = inputs.aov * (1 - inputs.gross_margin_pct)
    variable_cost = inputs.variable_cost_per_order
    cm = compute_contribution_margin_per_order(inputs)

    return {
        "labels": ["Revenue (AOV)", "COGS", "Gross Profit", "Variable Costs", "CM / Order"],
        "values": [revenue, -cogs, 0, -variable_cost, 0],
        "measures": ["absolute", "relative", "total", "relative", "total"],
        "text": [
            f"${revenue:,.2f}",
            f"-${cogs:,.2f}",
            f"${revenue - cogs:,.2f}",
            f"-${variable_cost:,.2f}",
            f"${cm:,.2f}",
        ],
    }


def create_waterfall_figure(
    data: dict,
    title: str = "Unit Economics per Order",
    height: int = 420,
) -> go.Figure:
    """Create a Plotly waterfall chart from build_waterfall_data() output."""
    fig = go.Figure(go.Waterfall(
        name="Unit Economics",
        orientation="v",
        measure=data["measures"],
        x=data["labels"],
        y=data["values"],
        textposition="outside",
        text=data["text"],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": GREEN}},
        decreasing={"marker": {"color": RED}},
        totals={"marker": {"color": BLUE}},
    ))
    fig.update_layout(
        title=title,
        template=PLOTLY_TEMPLATE,
        height=height,
        showlegend=False,
        yaxis_title="$ per Order",
        waterfallgap=0.3,
    )
    return fig
