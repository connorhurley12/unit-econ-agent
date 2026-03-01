"""Stage 3 — 'Your unit economics snapshot' — Waterfall chart + headline KPIs."""

from __future__ import annotations

import streamlit as st

from src.health import (
    SEVERITY_BG_COLORS,
    SEVERITY_COLORS,
    SEVERITY_ICONS,
    sort_flags,
)
from src.model import UnitEconInputs, compute
from src.waterfall import build_waterfall_data, create_waterfall_figure


def _build_inputs(journey: dict) -> UnitEconInputs:
    """Build UnitEconInputs from journey state."""
    mi = journey["model_inputs"]
    return UnitEconInputs(
        aov=mi["aov"],
        orders_per_month=mi["orders_per_month"],
        gross_margin_pct=mi["gross_margin_pct"],
        variable_cost_per_order=mi["variable_cost_per_order"],
        monthly_churn_rate=mi["monthly_churn_rate"],
        monthly_fixed_costs=mi.get("monthly_fixed_costs", 0.0),
        monthly_arpu_growth_rate=mi.get("monthly_arpu_growth_rate", 0.0),
        annual_discount_rate=mi.get("annual_discount_rate", 0.10),
        channels=mi.get("channels", []),
    )


def render() -> None:
    """Render Stage 3: unit economics snapshot."""
    st.markdown(
        '<h1 style="margin-bottom:0.2em;">Your Unit Economics Snapshot</h1>',
        unsafe_allow_html=True,
    )
    st.caption("Here's where the money goes on every order.")

    journey = st.session_state.journey_inputs
    inputs = _build_inputs(journey)
    outputs = compute(inputs)

    # Store for stages 4 and 5
    st.session_state.inputs = inputs
    st.session_state.outputs = outputs

    # ── Headline KPIs ─────────────────────────────────────────────────────────
    cm = outputs.contribution_margin_per_order
    cm_pct = (cm / inputs.aov * 100) if inputs.aov > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("CM / Order", f"${cm:,.2f}")
    with col2:
        st.metric("CM %", f"{cm_pct:.1f}%")
    with col3:
        if cm > 0 and inputs.monthly_fixed_costs > 0:
            orders_be = inputs.monthly_fixed_costs / cm
            st.metric("Orders to Break Even", f"{orders_be:,.0f} / month")
        elif cm <= 0:
            st.metric("Orders to Break Even", "Never (negative margin)")
        else:
            st.metric("Orders to Break Even", "N/A (no fixed costs)")

    # ── Waterfall chart ───────────────────────────────────────────────────────
    data = build_waterfall_data(inputs)
    fig = create_waterfall_figure(data, title="Unit Economics per Order")
    st.plotly_chart(fig, use_container_width=True)

    # ── Plain-English summary ─────────────────────────────────────────────────
    if cm > 0:
        st.success(
            f"You make **${cm:.2f}** on every order after variable costs. "
            f"That's **{cm_pct:.1f}%** of your AOV."
        )
    elif cm == 0:
        st.warning("You're breaking even on every order — no margin to cover fixed costs.")
    else:
        st.error(
            f"You **lose ${abs(cm):.2f}** on every order. "
            f"Fix margins before scaling acquisition."
        )

    # ── Additional metrics ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Full Model Outputs")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("LTV", f"${outputs.ltv:,.2f}")
    with m2:
        st.metric("LTV : CAC", f"{outputs.ltv_cac_ratio:.2f}x")
    with m3:
        payback = f"{outputs.payback_months:.1f} mo" if outputs.payback_months < 999 else "N/A"
        st.metric("Payback Period", payback)
    with m4:
        st.metric("Health Score", f"{outputs.health_score}/100")

    # ── Health flags ──────────────────────────────────────────────────────────
    flags = sort_flags(outputs.health_flags)
    if flags:
        st.markdown("### Diagnostics")
        for flag in flags:
            icon = SEVERITY_ICONS[flag.severity]
            bg = SEVERITY_BG_COLORS[flag.severity]
            fg = SEVERITY_COLORS[flag.severity]
            st.markdown(
                f'<div style="padding:10px 16px;border-radius:8px;background:{bg};'
                f'border-left:4px solid {fg};margin-bottom:8px;font-size:0.95rem;">'
                f'{icon} <strong>{flag.severity.upper()}</strong>: {flag.message}</div>',
                unsafe_allow_html=True,
            )
