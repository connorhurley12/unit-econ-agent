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
    cac: float                    # Customer acquisition cost ($)
    aov: float                    # Average order value ($)
    orders_per_month: float       # Orders per customer per month
    gross_margin_pct: float       # Gross margin as a decimal (e.g. 0.30)
    variable_cost_per_order: float  # Variable cost per order ($)
    monthly_churn_rate: float     # Monthly churn as a decimal (e.g. 0.08)
    monthly_fixed_costs: float = 0.0  # Monthly fixed overhead ($)
    monthly_arpu_growth_rate: float = 0.0  # MoM % growth in ARPU from upsell/cross-sell, e.g. 0.02 = 2%


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


# ── Core calculations ─────────────────────────────────────────────────────────

def compute_contribution_margin_per_order(inputs: UnitEconInputs) -> float:
    """Contribution margin per order = (AOV × gross_margin_%) − variable_cost."""
    return (inputs.aov * inputs.gross_margin_pct) - inputs.variable_cost_per_order


def compute_monthly_contribution(inputs: UnitEconInputs) -> float:
    """Monthly contribution per customer = contribution_margin × orders_per_month."""
    cm = compute_contribution_margin_per_order(inputs)
    return cm * inputs.orders_per_month


def compute_ltv(inputs: UnitEconInputs) -> float:
    """
    LTV with optional expansion revenue (Skok formula).

    If monthly_arpu_growth_rate == 0: LTV = a / c  (simple formula)
    If monthly_arpu_growth_rate >  0: LTV = a/c + m/c²  (linear expansion)

    Where:
      a = monthly contribution per customer (initial)
      m = a × monthly_arpu_growth_rate  (monthly $ growth in contribution)
      c = monthly churn rate
    """
    mc = compute_monthly_contribution(inputs)
    if inputs.monthly_churn_rate <= 0:
        return float("inf")
    c = inputs.monthly_churn_rate
    if inputs.monthly_arpu_growth_rate > 0:
        m = mc * inputs.monthly_arpu_growth_rate
        return mc / c + m / (c ** 2)
    return mc / c


def compute_ltv_cac_ratio(inputs: UnitEconInputs) -> float:
    """LTV : CAC ratio."""
    ltv = compute_ltv(inputs)
    if inputs.cac <= 0:
        return float("inf")
    return ltv / inputs.cac


def compute_payback_months(inputs: UnitEconInputs) -> float:
    """Payback period in months = CAC / monthly_contribution."""
    mc = compute_monthly_contribution(inputs)
    if mc <= 0:
        return float("inf")
    return inputs.cac / mc


# ── Health scoring ────────────────────────────────────────────────────────────

def compute_health_flags(inputs: UnitEconInputs, outputs: UnitEconOutputs) -> List[HealthFlag]:
    """Generate severity flags based on thresholds."""
    flags: List[HealthFlag] = []

    # Positive signal: negative churn achieved
    if inputs.monthly_arpu_growth_rate > inputs.monthly_churn_rate:
        flags.append(HealthFlag(
            "positive",
            f"Negative churn achieved — expansion revenue ({inputs.monthly_arpu_growth_rate:.1%}/mo) outpaces churn ({inputs.monthly_churn_rate:.1%}/mo)",
        ))

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

    outputs = UnitEconOutputs(
        contribution_margin_per_order=cm_order,
        monthly_contribution=mc,
        ltv=ltv,
        ltv_cac_ratio=ltv_cac,
        payback_months=payback,
        health_score=0,
        health_flags=[],
    )

    outputs.health_flags = compute_health_flags(inputs, outputs)
    outputs.health_score = compute_health_score(outputs)

    return outputs


def inputs_from_dict(d: dict) -> UnitEconInputs:
    """Build UnitEconInputs from a flat dictionary (e.g. loaded from JSON)."""
    return UnitEconInputs(
        cac=float(d["cac"]),
        aov=float(d["aov"]),
        orders_per_month=float(d["orders_per_month"]),
        gross_margin_pct=float(d["gross_margin_pct"]),
        variable_cost_per_order=float(d["variable_cost_per_order"]),
        monthly_churn_rate=float(d["monthly_churn_rate"]),
        monthly_fixed_costs=float(d.get("monthly_fixed_costs", 0)),
        monthly_arpu_growth_rate=float(d.get("monthly_arpu_growth_rate", 0)),
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
    print(f"  CAC:                     ${inputs.cac:,.2f}")
    print(f"  AOV:                     ${inputs.aov:,.2f}")
    print(f"  Orders/month:            {inputs.orders_per_month:.1f}")
    print(f"  Gross margin:            {inputs.gross_margin_pct:.0%}")
    print(f"  Variable cost/order:     ${inputs.variable_cost_per_order:,.2f}")
    print(f"  Monthly churn:           {inputs.monthly_churn_rate:.1%}")
    print("-" * 50)
    print(f"  Contribution/order:      ${outputs.contribution_margin_per_order:,.2f}")
    print(f"  Monthly contribution:    ${outputs.monthly_contribution:,.2f}")
    print(f"  LTV:                     ${outputs.ltv:,.2f}")
    print(f"  LTV:CAC ratio:           {outputs.ltv_cac_ratio:.2f}x")
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
