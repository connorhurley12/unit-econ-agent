"""Playbook generation: recommendations and PDF export."""

from __future__ import annotations

from typing import List

import pandas as pd

from src.model import UnitEconInputs, UnitEconOutputs


def generate_recommendations(
    inputs: UnitEconInputs,
    outputs: UnitEconOutputs,
    tornado_df: pd.DataFrame,
) -> List[str]:
    """Generate top 2-3 actionable recommendations from tornado analysis and health flags."""
    recs: List[str] = []

    # Top levers from tornado chart
    for _, row in tornado_df.head(2).iterrows():
        lever = row["lever"]
        pct = row["pct_delta"]
        direction = "improvement" if pct > 0 else "change"
        recs.append(
            f"Your biggest lever is **{lever}**. A 10% {direction} would shift "
            f"LTV:CAC by {pct:+.1f}%. Focus optimization efforts here."
        )

    # Health-flag-based recommendations
    for flag in outputs.health_flags:
        if flag.severity == "critical":
            recs.append(f"**Urgent fix needed:** {flag.message}")
            break
        if flag.severity == "warning":
            recs.append(f"**Watch out:** {flag.message}")
            break

    return recs[:3]


def generate_executive_summary(
    inputs: UnitEconInputs,
    outputs: UnitEconOutputs,
    template_name: str,
) -> str:
    """Generate a plain-text executive summary."""
    cm = outputs.contribution_margin_per_order
    cm_pct = (cm / inputs.aov * 100) if inputs.aov > 0 else 0
    breakeven = (
        f"{inputs.monthly_fixed_costs / cm:,.0f} orders/month"
        if cm > 0 and inputs.monthly_fixed_costs > 0
        else "N/A"
    )
    payback = (
        f"{outputs.payback_months:.1f} months"
        if outputs.payback_months < 999
        else "infinite"
    )

    return (
        f"Business type: {template_name}\n"
        f"Contribution margin: ${cm:,.2f}/order ({cm_pct:.1f}% of AOV)\n"
        f"LTV: ${outputs.ltv:,.2f}  |  LTV:CAC: {outputs.ltv_cac_ratio:.1f}x\n"
        f"Payback period: {payback}\n"
        f"Breakeven: {breakeven}\n"
        f"Health score: {outputs.health_score}/100"
    )


def generate_pdf(
    inputs: UnitEconInputs,
    outputs: UnitEconOutputs,
    tornado_df: pd.DataFrame,
    recommendations: List[str],
    template_name: str,
) -> bytes:
    """Generate a PDF playbook report. Returns bytes for download."""
    from fpdf import FPDF  # lazy import — fpdf2 is only needed for PDF export

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 15, "Unit Economics Playbook", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Business Type: {template_name}", ln=True, align="C")
    pdf.ln(10)

    # Key Metrics
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Key Metrics", ln=True)
    pdf.set_font("Helvetica", "", 11)

    cm = outputs.contribution_margin_per_order
    cm_pct = (cm / inputs.aov * 100) if inputs.aov > 0 else 0
    payback = f"{outputs.payback_months:.1f} mo" if outputs.payback_months < 999 else "N/A"

    metrics = [
        ("Average Order Value", f"${inputs.aov:,.2f}"),
        ("Gross Margin", f"{inputs.gross_margin_pct:.0%}"),
        ("Variable Cost / Order", f"${inputs.variable_cost_per_order:,.2f}"),
        ("CM / Order", f"${cm:,.2f} ({cm_pct:.1f}%)"),
        ("Blended CAC", f"${inputs.blended_cac:,.2f}"),
        ("LTV", f"${outputs.ltv:,.2f}"),
        ("LTV:CAC Ratio", f"{outputs.ltv_cac_ratio:.2f}x"),
        ("Payback Period", payback),
        ("Health Score", f"{outputs.health_score}/100"),
    ]

    col_w = 95
    for label, value in metrics:
        pdf.cell(col_w, 8, f"  {label}", border=1)
        pdf.cell(col_w, 8, value, border=1, ln=True, align="R")

    pdf.ln(8)

    # Lever ranking
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Most Sensitive Levers (10% improvement)", ln=True)
    pdf.set_font("Helvetica", "", 11)

    pdf.cell(col_w, 8, "  Lever", border=1)
    pdf.cell(col_w, 8, "LTV:CAC Impact", border=1, ln=True, align="R")
    for _, row in tornado_df.iterrows():
        pdf.cell(col_w, 8, f"  {row['lever']}", border=1)
        pdf.cell(col_w, 8, f"{row['pct_delta']:+.1f}%", border=1, ln=True, align="R")

    pdf.ln(8)

    # Recommendations
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Recommendations", ln=True)
    pdf.set_font("Helvetica", "", 11)

    for i, rec in enumerate(recommendations, 1):
        clean = rec.replace("**", "")
        pdf.multi_cell(0, 7, f"{i}. {clean}")
        pdf.ln(2)

    pdf.ln(6)

    # Inputs recap
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, f"Monthly churn: {inputs.monthly_churn_rate:.1%}  |  "
                    f"Orders/month: {inputs.orders_per_month:.1f}  |  "
                    f"Fixed costs: ${inputs.monthly_fixed_costs:,.0f}/mo", ln=True)

    return bytes(pdf.output())
