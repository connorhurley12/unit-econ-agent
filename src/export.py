"""Export utilities for CSV and JSON downloads."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict

import pandas as pd

from src.model import UnitEconInputs, UnitEconOutputs


def inputs_to_json(inputs: UnitEconInputs) -> str:
    """Serialize inputs to pretty JSON."""
    return json.dumps(asdict(inputs), indent=2)


def summary_to_json(inputs: UnitEconInputs, outputs: UnitEconOutputs) -> str:
    """Build a full summary dict and serialize to JSON."""
    summary: Dict[str, Any] = {
        "inputs": asdict(inputs),
        "outputs": {
            "contribution_margin_per_order": round(outputs.contribution_margin_per_order, 4),
            "monthly_contribution": round(outputs.monthly_contribution, 4),
            "ltv": round(outputs.ltv, 2),
            "ltv_cac_ratio": round(outputs.ltv_cac_ratio, 4),
            "payback_months": round(outputs.payback_months, 2),
            "health_score": outputs.health_score,
            "health_flags": [asdict(f) for f in outputs.health_flags],
        },
    }
    return json.dumps(summary, indent=2)


def cohort_to_csv(cohort_df: pd.DataFrame) -> str:
    """Convert a cohort DataFrame to CSV string."""
    return cohort_df.to_csv(index=False)
