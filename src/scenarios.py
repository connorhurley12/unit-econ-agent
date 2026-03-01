"""Pre-built what-if scenarios and impact summary generation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, List

from src.model import UnitEconInputs, UnitEconOutputs, compute


@dataclass
class Scenario:
    """A named what-if scenario that modifies inputs."""
    name: str
    description: str
    apply: Callable[[UnitEconInputs], UnitEconInputs]


def _aov_increase_15(inputs: UnitEconInputs) -> UnitEconInputs:
    return replace(inputs, aov=inputs.aov * 1.15)


def _delivery_cost_drop(inputs: UnitEconInputs) -> UnitEconInputs:
    new_vc = max(0.0, inputs.variable_cost_per_order - 1.50)
    return replace(inputs, variable_cost_per_order=new_vc)


def _batch_two_orders(inputs: UnitEconInputs) -> UnitEconInputs:
    return replace(inputs, variable_cost_per_order=inputs.variable_cost_per_order * 0.5)


def _spoilage_doubles(inputs: UnitEconInputs) -> UnitEconInputs:
    # Spoilage doubling reduces gross margin by ~3 percentage points
    shrink = min(inputs.gross_margin_pct, 0.03)
    return replace(inputs, gross_margin_pct=inputs.gross_margin_pct - shrink)


def _churn_drops_to_5(inputs: UnitEconInputs) -> UnitEconInputs:
    return replace(inputs, monthly_churn_rate=0.05)


def _churn_halved(inputs: UnitEconInputs) -> UnitEconInputs:
    return replace(inputs, monthly_churn_rate=inputs.monthly_churn_rate * 0.5)


DEFAULT_SCENARIOS: List[Scenario] = [
    Scenario(
        name="AOV +15%",
        description="What if average order value increases 15%?",
        apply=_aov_increase_15,
    ),
    Scenario(
        name="Delivery cost -$1.50",
        description="What if delivery cost drops $1.50 per order?",
        apply=_delivery_cost_drop,
    ),
    Scenario(
        name="Batch 2 orders per run",
        description="What if you batch 2 orders per delivery run, halving variable cost?",
        apply=_batch_two_orders,
    ),
    Scenario(
        name="Spoilage doubles",
        description="What if spoilage/shrink doubles, reducing gross margin?",
        apply=_spoilage_doubles,
    ),
    Scenario(
        name="Churn drops to 5%",
        description="What if monthly churn drops to 5%?",
        apply=_churn_drops_to_5,
    ),
    Scenario(
        name="Churn halved",
        description="What if churn rate is cut in half?",
        apply=_churn_halved,
    ),
]


def get_default_scenarios() -> List[Scenario]:
    """Return the list of pre-built scenarios."""
    return DEFAULT_SCENARIOS


def apply_scenario(
    inputs: UnitEconInputs,
    scenario: Scenario,
) -> tuple[UnitEconInputs, UnitEconOutputs]:
    """Apply a scenario and compute new outputs."""
    new_inputs = scenario.apply(inputs)
    new_outputs = compute(new_inputs)
    return new_inputs, new_outputs


def generate_impact_summary(
    inputs_before: UnitEconInputs,
    outputs_before: UnitEconOutputs,
    inputs_after: UnitEconInputs,
    outputs_after: UnitEconOutputs,
) -> str:
    """Generate a plain-English impact summary comparing before and after."""
    cm_before = outputs_before.contribution_margin_per_order
    cm_after = outputs_after.contribution_margin_per_order
    cm_delta = cm_after - cm_before

    parts = []

    # Contribution margin change
    if cm_delta > 0:
        parts.append(
            f"Contribution margin improves from ${cm_before:,.2f} to ${cm_after:,.2f} per order"
        )
    elif cm_delta < 0:
        parts.append(
            f"Contribution margin drops from ${cm_before:,.2f} to ${cm_after:,.2f} per order"
        )
    else:
        parts.append("No change in contribution margin per order")

    # Breakeven comparison
    if outputs_before.contribution_margin_per_order > 0 and inputs_before.monthly_fixed_costs > 0:
        be_before = inputs_before.monthly_fixed_costs / outputs_before.contribution_margin_per_order
        if outputs_after.contribution_margin_per_order > 0:
            be_after = inputs_after.monthly_fixed_costs / outputs_after.contribution_margin_per_order
            parts.append(
                f"reaching breakeven at {be_after:,.0f} orders/month instead of {be_before:,.0f}"
            )
        else:
            parts.append("breakeven is no longer achievable")
    elif outputs_after.contribution_margin_per_order > 0 and inputs_after.monthly_fixed_costs > 0:
        be_after = inputs_after.monthly_fixed_costs / outputs_after.contribution_margin_per_order
        parts.append(f"breakeven now possible at {be_after:,.0f} orders/month")

    # LTV:CAC change
    ltv_cac_before = outputs_before.ltv_cac_ratio
    ltv_cac_after = outputs_after.ltv_cac_ratio
    if ltv_cac_before < float("inf") and ltv_cac_after < float("inf"):
        parts.append(f"LTV:CAC moves from {ltv_cac_before:.1f}x to {ltv_cac_after:.1f}x")

    return ", ".join(parts) + "."
