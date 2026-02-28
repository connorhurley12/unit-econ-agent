"""Core unit economics calculations. Pure Python — no Streamlit imports."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class UnitEconInputs:
    """All inputs needed for the unit economics model."""
    aov: float                    # Average order value ($)
    orders_per_month: float       # Orders per customer per month
    gross_margin_pct: float       # Gross margin as a decimal (e.g. 0.30)
    variable_cost_per_order: float  # Variable cost per order ($)
    monthly_churn_rate: float     # Monthly churn as a decimal (e.g. 0.08)
    monthly_fixed_costs: float = 0.0  # Monthly fixed overhead ($)
    annual_discount_rate: float = 0.10  # Cost of capital / hurdle rate
    channels: list = field(default_factory=lambda: [
        {"name": "Paid", "cac": 25.0, "pct_of_new_customers": 0.60},
        {"name": "Organic", "cac": 8.0, "pct_of_new_customers": 0.30},
        {"name": "Referral", "cac": 4.0, "pct_of_new_customers": 0.10},
    ])

    @property
    def blended_cac(self) -> float:
        """Weighted-average CAC across all acquisition channels."""
        if not self.channels:
            return 0.0
        return sum(ch["cac"] * ch["pct_of_new_customers"] for ch in self.channels)


@dataclass
class HealthFlag:
    """A single diagnostic flag."""
    severity: str   # "critical" | "warning" | "watch"
    message: str


@dataclass
class UnitEconOutputs:
    """All computed outputs."""
    contribution_margin_per_order: float
    monthly_contribution: float
    ltv: float
    ltv_cac_ratio: float
    payback_months: float
    health_score: int
    health_flags: List[HealthFlag] = field(default_factory=list)
    discounted_ltv: float = 0.0
    discounted_ltv_cac_ratio: float = 0.0


# ── Core calculations ─────────────────────────────────────────────────────────

def compute_contribution_margin_per_order(inputs: UnitEconInputs) -> float:
    """Contribution margin per order = (AOV × gross_margin_%) − variable_cost."""
    return (inputs.aov * inputs.gross_margin_pct) - inputs.variable_cost_per_order


def compute_monthly_contribution(inputs: UnitEconInputs) -> float:
    """Monthly contribution per customer = contribution_margin × orders_per_month."""
    cm = compute_contribution_margin_per_order(inputs)
    return cm * inputs.orders_per_month


def compute_ltv(inputs: UnitEconInputs) -> float:
    """LTV = monthly_contribution × (1 / churn_rate)."""
    mc = compute_monthly_contribution(inputs)
    if inputs.monthly_churn_rate <= 0:
        return float("inf")
    return mc * (1.0 / inputs.monthly_churn_rate)


def compute_ltv_cac_ratio(inputs: UnitEconInputs) -> float:
    """LTV : CAC ratio (uses blended CAC across channels)."""
    ltv = compute_ltv(inputs)
    if inputs.blended_cac <= 0:
        return float("inf")
    return ltv / inputs.blended_cac


def compute_payback_months(inputs: UnitEconInputs) -> float:
    """Payback period in months = blended_cac / monthly_contribution."""
    mc = compute_monthly_contribution(inputs)
    if mc <= 0:
        return float("inf")
    return inputs.blended_cac / mc


def compute_discounted_ltv(inputs: UnitEconInputs) -> float:
    """Discounted LTV using monthly discounted cash flows over the avg lifetime."""
    mc = compute_monthly_contribution(inputs)
    if inputs.monthly_churn_rate <= 0:
        return float("inf")

    monthly_rate = (1 + inputs.annual_discount_rate) ** (1 / 12) - 1
    avg_lifetime_months = int(round(1.0 / inputs.monthly_churn_rate))

    discounted_ltv = 0.0
    for t in range(1, avg_lifetime_months + 1):
        survivors = (1 - inputs.monthly_churn_rate) ** (t - 1)
        monthly_cf = survivors * mc
        discounted_ltv += monthly_cf / (1 + monthly_rate) ** t

    return discounted_ltv


# ── Health scoring ────────────────────────────────────────────────────────────

def compute_health_flags(inputs: UnitEconInputs, outputs: UnitEconOutputs) -> List[HealthFlag]:
    """Generate severity flags based on thresholds."""
    flags: List[HealthFlag] = []

    if outputs.ltv_cac_ratio < 1.0:
        flags.append(HealthFlag("critical", f"LTV:CAC ratio is {outputs.ltv_cac_ratio:.2f} (< 1.0) — you lose money on every customer"))

    if outputs.payback_months > 18:
        flags.append(HealthFlag("warning", f"Payback period is {outputs.payback_months:.1f} months (> 18) — slow capital recovery"))

    cm_pct = compute_contribution_margin_per_order(inputs) / inputs.aov if inputs.aov > 0 else 0
    if cm_pct < 0.10:
        flags.append(HealthFlag("warning", f"Contribution margin is {cm_pct:.1%} of AOV (< 10%) — thin margins"))

    if inputs.monthly_churn_rate > 0.10:
        flags.append(HealthFlag("watch", f"Monthly churn is {inputs.monthly_churn_rate:.1%} (> 10%) — retention risk"))

    return flags


def compute_health_score(outputs: UnitEconOutputs) -> int:
    """
    Health score 0–100 based on key metrics.

    Scoring (each component 0–25):
      - LTV:CAC ratio:  >=3 → 25, >=1 → proportional, <1 → 0
      - Payback:         <=6 → 25, <=18 → proportional, >18 → 0
      - Margin:          >=20% → 25, proportional down to 0
      - Churn penalty:   <=5% → 25, <=15% → proportional, >15% → 0
    We reconstruct churn from LTV and monthly contribution.
    """
    score = 0.0

    # LTV:CAC component (0–25)
    ratio = outputs.ltv_cac_ratio
    if ratio >= 3.0:
        score += 25
    elif ratio >= 1.0:
        score += 25 * ((ratio - 1.0) / 2.0)

    # Payback component (0–25)
    pb = outputs.payback_months
    if pb <= 6:
        score += 25
    elif pb <= 18:
        score += 25 * ((18 - pb) / 12.0)

    # Margin component (0–25) — use contribution_margin_per_order relative to a benchmark
    cm = outputs.contribution_margin_per_order
    if cm >= 5.0:
        score += 25
    elif cm > 0:
        score += 25 * min(cm / 5.0, 1.0)

    # Monthly contribution component (0–25)
    mc = outputs.monthly_contribution
    if mc >= 15.0:
        score += 25
    elif mc > 0:
        score += 25 * min(mc / 15.0, 1.0)

    return max(0, min(100, int(round(score))))


# ── Top-level compute ─────────────────────────────────────────────────────────

def compute(inputs: UnitEconInputs) -> UnitEconOutputs:
    """Run all calculations and return the full output bundle."""
    cm_order = compute_contribution_margin_per_order(inputs)
    mc = compute_monthly_contribution(inputs)
    ltv = compute_ltv(inputs)
    ltv_cac = compute_ltv_cac_ratio(inputs)
    payback = compute_payback_months(inputs)
    disc_ltv = compute_discounted_ltv(inputs)
    disc_ltv_cac = (disc_ltv / inputs.blended_cac) if inputs.blended_cac > 0 else float("inf")

    outputs = UnitEconOutputs(
        contribution_margin_per_order=cm_order,
        monthly_contribution=mc,
        ltv=ltv,
        ltv_cac_ratio=ltv_cac,
        payback_months=payback,
        health_score=0,
        health_flags=[],
        discounted_ltv=disc_ltv,
        discounted_ltv_cac_ratio=disc_ltv_cac,
    )

    outputs.health_flags = compute_health_flags(inputs, outputs)
    outputs.health_score = compute_health_score(outputs)

    return outputs


def inputs_from_dict(d: dict) -> UnitEconInputs:
    """Build UnitEconInputs from a dictionary (e.g. loaded from JSON).

    Supports both new ``channels`` format and legacy flat ``cac`` field.
    """
    if "channels" in d:
        channels = d["channels"]
    elif "cac" in d:
        channels = [{"name": "Blended", "cac": float(d["cac"]), "pct_of_new_customers": 1.0}]
    else:
        channels = []
    return UnitEconInputs(
        aov=float(d["aov"]),
        orders_per_month=float(d["orders_per_month"]),
        gross_margin_pct=float(d["gross_margin_pct"]),
        variable_cost_per_order=float(d["variable_cost_per_order"]),
        monthly_churn_rate=float(d["monthly_churn_rate"]),
        monthly_fixed_costs=float(d.get("monthly_fixed_costs", 0)),
        annual_discount_rate=float(d.get("annual_discount_rate", 0.10)),
        channels=channels,
    )


def outputs_to_dict(outputs: UnitEconOutputs) -> dict:
    """Serialize outputs to a plain dict (JSON-safe)."""
    d = asdict(outputs)
    # health_flags are already dicts via asdict
    return d


# ── CLI entry point ───────────────────────────────────────────────────────────

def cli_main(argv: list | None = None) -> None:
    parser = argparse.ArgumentParser(description="Unit Economics Calculator")
    parser.add_argument("--config", required=True, help="Path to JSON config file")
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path) as f:
        raw = json.load(f)

    inputs = inputs_from_dict(raw)
    outputs = compute(inputs)

    print("=" * 50)
    print("  UNIT ECONOMICS SUMMARY")
    print("=" * 50)
    print(f"  Blended CAC:             ${inputs.blended_cac:,.2f}")
    if inputs.channels:
        for ch in inputs.channels:
            print(f"    {ch['name']:20s}  CAC ${ch['cac']:>8,.2f}  ({ch['pct_of_new_customers']:.0%})")
    print(f"  AOV:                     ${inputs.aov:,.2f}")
    print(f"  Orders/month:            {inputs.orders_per_month:.1f}")
    print(f"  Gross margin:            {inputs.gross_margin_pct:.0%}")
    print(f"  Variable cost/order:     ${inputs.variable_cost_per_order:,.2f}")
    print(f"  Monthly churn:           {inputs.monthly_churn_rate:.1%}")
    print("-" * 50)
    print(f"  Contribution/order:      ${outputs.contribution_margin_per_order:,.2f}")
    print(f"  Monthly contribution:    ${outputs.monthly_contribution:,.2f}")
    print(f"  LTV:                     ${outputs.ltv:,.2f}")
    print(f"  Discounted LTV:          ${outputs.discounted_ltv:,.2f}")
    print(f"  LTV:CAC ratio:           {outputs.ltv_cac_ratio:.2f}x")
    print(f"  Disc. LTV:CAC ratio:     {outputs.discounted_ltv_cac_ratio:.2f}x")
    print(f"  Payback period:          {outputs.payback_months:.1f} months")
    print(f"  Health score:            {outputs.health_score}/100")
    print("-" * 50)

    if outputs.health_flags:
        print("  FLAGS:")
        for flag in outputs.health_flags:
            icon = {"critical": "!!!", "warning": " ! ", "watch": " ~ "}[flag.severity]
            print(f"  [{icon}] {flag.severity.upper()}: {flag.message}")
    else:
        print("  No health flags — looking good!")

    print("=" * 50)


if __name__ == "__main__":
    cli_main()
