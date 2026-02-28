"""Cohort LTV curves: simulate monthly cohort decay, cumulative contribution, and revenue."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.model import UnitEconInputs, compute_contribution_margin_per_order


def build_cohort_table(inputs: UnitEconInputs, n_months: int = 36) -> pd.DataFrame:
    """
    Build a month-by-month cohort table starting with 1 000 customers.

    Columns:
      - month: 1..n_months
      - survivors: customers remaining (geometric churn)
      - survivor_pct: survivors / initial
      - monthly_revenue: survivors × orders_per_month × AOV
      - monthly_contribution: survivors × orders_per_month × contribution_margin
      - cumulative_contribution: running sum of monthly_contribution
      - discounted_cumulative_contribution: running sum discounted to present value
      - cac_threshold: total CAC spent on initial cohort (flat line)
    """
    initial_customers = 1_000
    cm_per_order = compute_contribution_margin_per_order(inputs)
    retention = 1.0 - inputs.monthly_churn_rate
    total_cac = initial_customers * inputs.cac

    months = np.arange(1, n_months + 1)
    survivors = initial_customers * (retention ** months)
    survivor_pct = survivors / initial_customers
    monthly_revenue = survivors * inputs.orders_per_month * inputs.aov
    monthly_contribution = survivors * inputs.orders_per_month * cm_per_order
    cumulative_contribution = np.cumsum(monthly_contribution)

    monthly_rate = (1 + inputs.annual_discount_rate) ** (1 / 12) - 1
    discount_factors = (1 + monthly_rate) ** months
    discounted_monthly_contribution = monthly_contribution / discount_factors
    discounted_cumulative_contribution = np.cumsum(discounted_monthly_contribution)

    return pd.DataFrame({
        "month": months,
        "survivors": np.round(survivors, 1),
        "survivor_pct": np.round(survivor_pct, 4),
        "monthly_revenue": np.round(monthly_revenue, 2),
        "monthly_contribution": np.round(monthly_contribution, 2),
        "cumulative_contribution": np.round(cumulative_contribution, 2),
        "discounted_cumulative_contribution": np.round(discounted_cumulative_contribution, 2),
        "cac_threshold": total_cac,
    })


def find_payback_month(cohort_df: pd.DataFrame) -> int | None:
    """Return the first month where cumulative contribution >= CAC threshold, or None."""
    mask = cohort_df["cumulative_contribution"] >= cohort_df["cac_threshold"]
    if mask.any():
        return int(cohort_df.loc[mask.idxmin(), "month"])
    return None
