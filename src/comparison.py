"""Segment comparison logic — pure Python, no Streamlit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from src.model import UnitEconInputs, UnitEconOutputs, compute


@dataclass
class MetricRow:
    """One row in the comparison table."""
    label: str
    value_a: float
    value_b: float
    fmt: str  # python format string e.g. "${:,.2f}"
    higher_is_better: bool  # True = green when higher


# ── Thresholds for cell coloring ─────────────────────────────────────────────
# Maps metric label → (red_below, yellow_below, green_at_or_above)
METRIC_THRESHOLDS = {
    "LTV": (50.0, 200.0),
    "CAC": None,  # special: lower is better, handled separately
    "LTV:CAC": (1.0, 3.0),
    "Payback Period (mo)": None,  # lower is better
    "Contribution Margin": (0.0, 5.0),
    "Health Score": (40, 70),
}


def cell_color(label: str, value: float) -> str:
    """Return 'green', 'yellow', or 'red' for a metric value."""
    if label == "CAC":
        # Lower is better
        if value <= 50:
            return "green"
        if value <= 200:
            return "yellow"
        return "red"

    if label == "Payback Period (mo)":
        # Lower is better
        if value == float("inf"):
            return "red"
        if value <= 6:
            return "green"
        if value <= 18:
            return "yellow"
        return "red"

    thresholds = METRIC_THRESHOLDS.get(label)
    if thresholds is None:
        return "yellow"

    red_below, green_at = thresholds
    if value < red_below:
        return "red"
    if value >= green_at:
        return "green"
    return "yellow"


COLOR_HEX = {
    "green": "#10B981",
    "yellow": "#F59E0B",
    "red": "#EF4444",
}

COLOR_BG_HEX = {
    "green": "#D1FAE5",
    "yellow": "#FEF3C7",
    "red": "#FEE2E2",
}


def build_comparison_rows(
    out_a: UnitEconOutputs, out_b: UnitEconOutputs
) -> List[MetricRow]:
    """Build the list of metric rows for the comparison table."""
    return [
        MetricRow("LTV", out_a.ltv, out_b.ltv, "${:,.2f}", True),
        MetricRow("CAC", _get_cac(out_a), _get_cac(out_b), "${:,.2f}", False),
        MetricRow("LTV:CAC", out_a.ltv_cac_ratio, out_b.ltv_cac_ratio, "{:.2f}x", True),
        MetricRow("Payback Period (mo)", out_a.payback_months, out_b.payback_months, "{:.1f}", False),
        MetricRow("Contribution Margin", out_a.contribution_margin_per_order, out_b.contribution_margin_per_order, "${:,.2f}", True),
        MetricRow("Health Score", out_a.health_score, out_b.health_score, "{:.0f}/100", True),
    ]


def _get_cac(outputs: UnitEconOutputs) -> float:
    """Extract CAC from outputs via the ratio: CAC = LTV / ratio."""
    if outputs.ltv_cac_ratio == 0 or outputs.ltv_cac_ratio == float("inf"):
        return 0.0
    return outputs.ltv / outputs.ltv_cac_ratio


def format_value(fmt: str, value: float) -> str:
    """Format a metric value, handling infinity."""
    if value == float("inf"):
        return "∞"
    return fmt.format(value)


# ── Verdict generation ───────────────────────────────────────────────────────

def generate_verdict(
    inputs_a: UnitEconInputs,
    inputs_b: UnitEconInputs,
    out_a: UnitEconOutputs,
    out_b: UnitEconOutputs,
) -> List[str]:
    """Generate plain-English comparison verdicts."""
    verdicts: List[str] = []

    # Overall winner
    a_score = out_a.health_score
    b_score = out_b.health_score
    if a_score > b_score:
        verdicts.append(
            f"**Segment A has stronger overall unit economics** (health score {a_score} vs {b_score})."
        )
    elif b_score > a_score:
        verdicts.append(
            f"**Segment B has stronger overall unit economics** (health score {b_score} vs {a_score})."
        )
    else:
        verdicts.append(
            f"**Both segments have equal health scores** ({a_score})."
        )

    # LTV:CAC vs payback tradeoff
    a_better_ratio = out_a.ltv_cac_ratio > out_b.ltv_cac_ratio
    a_better_payback = out_a.payback_months < out_b.payback_months

    if a_better_ratio and not a_better_payback:
        verdicts.append(
            "Segment A creates more value per customer but requires more capital to scale "
            f"(LTV:CAC {out_a.ltv_cac_ratio:.2f}x vs {out_b.ltv_cac_ratio:.2f}x, "
            f"payback {out_a.payback_months:.1f} vs {out_b.payback_months:.1f} months)."
        )
    elif not a_better_ratio and a_better_payback:
        verdicts.append(
            "Segment B creates more value per customer but requires more capital to scale "
            f"(LTV:CAC {out_b.ltv_cac_ratio:.2f}x vs {out_a.ltv_cac_ratio:.2f}x, "
            f"payback {out_b.payback_months:.1f} vs {out_a.payback_months:.1f} months)."
        )

    # CAC vs churn tradeoff
    a_lower_cac = inputs_a.cac < inputs_b.cac
    a_higher_churn = inputs_a.monthly_churn_rate > inputs_b.monthly_churn_rate

    if a_lower_cac and a_higher_churn:
        verdicts.append(
            "Segment A is cheaper to acquire but has a retention problem "
            f"(CAC ${inputs_a.cac:,.0f} vs ${inputs_b.cac:,.0f}, "
            f"churn {inputs_a.monthly_churn_rate:.0%} vs {inputs_b.monthly_churn_rate:.0%})."
        )
    elif not a_lower_cac and not a_higher_churn and inputs_a.cac != inputs_b.cac:
        verdicts.append(
            "Segment B is cheaper to acquire but has a retention problem "
            f"(CAC ${inputs_b.cac:,.0f} vs ${inputs_a.cac:,.0f}, "
            f"churn {inputs_b.monthly_churn_rate:.0%} vs {inputs_a.monthly_churn_rate:.0%})."
        )

    # Margin comparison
    if out_a.contribution_margin_per_order > out_b.contribution_margin_per_order * 1.5:
        verdicts.append(
            f"Segment A has significantly higher margins "
            f"(${out_a.contribution_margin_per_order:,.2f} vs ${out_b.contribution_margin_per_order:,.2f} per order)."
        )
    elif out_b.contribution_margin_per_order > out_a.contribution_margin_per_order * 1.5:
        verdicts.append(
            f"Segment B has significantly higher margins "
            f"(${out_b.contribution_margin_per_order:,.2f} vs ${out_a.contribution_margin_per_order:,.2f} per order)."
        )

    # LTV comparison
    if out_a.ltv > out_b.ltv * 1.5:
        verdicts.append(
            f"Segment A generates substantially more lifetime value "
            f"(${out_a.ltv:,.0f} vs ${out_b.ltv:,.0f})."
        )
    elif out_b.ltv > out_a.ltv * 1.5:
        verdicts.append(
            f"Segment B generates substantially more lifetime value "
            f"(${out_b.ltv:,.0f} vs ${out_a.ltv:,.0f})."
        )

    return verdicts
