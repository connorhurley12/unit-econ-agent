"""Sensitivity analysis: measure how each lever impacts LTV:CAC."""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from src.model import UnitEconInputs, compute_ltv_cac_ratio


# Mapping of lever names to their UnitEconInputs field names
LEVERS: Dict[str, str] = {
    "CAC": "cac",
    "AOV": "aov",
    "Orders/mo": "orders_per_month",
    "Gross Margin": "gross_margin_pct",
    "Variable Cost": "variable_cost_per_order",
    "Churn Rate": "monthly_churn_rate",
}


def _tweak_input(inputs: UnitEconInputs, field: str, pct_change: float) -> UnitEconInputs:
    """Return a copy of inputs with one field adjusted by pct_change (e.g. 0.10 = +10%)."""
    current = getattr(inputs, field)
    new_val = current * (1 + pct_change)
    return replace(inputs, **{field: new_val})


def tornado_data(inputs: UnitEconInputs, improvement_pct: float = 0.10) -> pd.DataFrame:
    """
    For each lever, compute the LTV:CAC change from a standard improvement.

    For CAC and variable cost, "improvement" means *decreasing* the value,
    so we negate the pct_change for those.

    Returns a DataFrame with columns: lever, baseline, improved, delta, pct_delta
    sorted by absolute delta descending.
    """
    baseline = compute_ltv_cac_ratio(inputs)
    rows = []

    for label, field in LEVERS.items():
        # For cost levers, improvement = reduction
        direction = -1.0 if field in ("cac", "variable_cost_per_order", "monthly_churn_rate") else 1.0
        tweaked = _tweak_input(inputs, field, direction * improvement_pct)
        improved = compute_ltv_cac_ratio(tweaked)
        delta = improved - baseline
        pct_delta = (delta / baseline * 100) if baseline != 0 else 0

        rows.append({
            "lever": label,
            "baseline": baseline,
            "improved": improved,
            "delta": delta,
            "pct_delta": pct_delta,
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("delta", key=abs, ascending=False).reset_index(drop=True)
    return df


def sweep_lever(
    inputs: UnitEconInputs,
    field: str,
    pct_range: float = 0.40,
    n_points: int = 41,
) -> pd.DataFrame:
    """
    Sweep a single lever across ±pct_range and compute LTV:CAC at each point.

    Returns DataFrame with columns: pct_change, value, ltv_cac
    """
    pcts = np.linspace(-pct_range, pct_range, n_points)
    rows = []
    for pct in pcts:
        tweaked = _tweak_input(inputs, field, pct)
        ratio = compute_ltv_cac_ratio(tweaked)
        rows.append({
            "pct_change": pct,
            "value": getattr(tweaked, field),
            "ltv_cac": ratio,
        })
    return pd.DataFrame(rows)
