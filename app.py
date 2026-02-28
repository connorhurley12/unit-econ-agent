"""unit-econ-builder — Streamlit web app for unit economics modeling."""

import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from src.cohorts import build_cohort_table, find_payback_month
from src.export import cohort_to_csv, inputs_to_json, summary_to_json
from src.health import (
    SEVERITY_BG_COLORS,
    SEVERITY_COLORS,
    SEVERITY_ICONS,
    health_score_color,
    sort_flags,
)
from src.model import UnitEconInputs, compute
from src.sensitivity import LEVERS, sweep_lever, tornado_data

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Unit Econ Builder",
    page_icon="📊",
    layout="wide",
)

# ── Colors ────────────────────────────────────────────────────────────────────

PRIMARY = "#3B82F6"
RED = "#EF4444"
GREEN = "#10B981"
INDIGO = "#6366F1"
PLOTLY_TEMPLATE = "plotly_white"

# ── Example presets ───────────────────────────────────────────────────────────

EXAMPLES_DIR = Path("data")
PRESETS = {
    "Dark Store Delivery": EXAMPLES_DIR / "example_dark_store.json",
    "B2B SaaS": EXAMPLES_DIR / "example_saas.json",
}


def load_preset(name: str) -> dict:
    with open(PRESETS[name]) as f:
        return json.load(f)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📊 Unit Econ Builder")
    st.markdown("---")

    preset = st.selectbox("Load preset", list(PRESETS.keys()))
    defaults = load_preset(preset)

    st.subheader("Model Inputs")

    cac = st.number_input("Customer Acquisition Cost ($)", min_value=0.0, value=defaults["cac"], step=1.0, format="%.2f")
    aov = st.number_input("Avg Order Value ($)", min_value=0.01, value=defaults["aov"], step=1.0, format="%.2f")
    orders_per_month = st.number_input("Orders per Month", min_value=0.1, value=defaults["orders_per_month"], step=0.1, format="%.1f")
    gross_margin_pct = st.slider("Gross Margin %", min_value=0, max_value=100, value=int(defaults["gross_margin_pct"] * 100)) / 100.0
    variable_cost = st.number_input("Variable Cost per Order ($)", min_value=0.0, value=defaults["variable_cost_per_order"], step=0.10, format="%.2f")
    monthly_churn = st.slider("Monthly Churn %", min_value=0, max_value=50, value=int(defaults["monthly_churn_rate"] * 100)) / 100.0
    monthly_fixed = st.number_input("Monthly Fixed Costs ($)", min_value=0.0, value=defaults.get("monthly_fixed_costs", 0.0), step=100.0, format="%.0f")

    st.markdown("---")
    st.subheader("Discounting")
    discount_rate_pct = st.slider("Discount Rate %", min_value=0, max_value=30, value=10)
    annual_discount_rate = discount_rate_pct / 100.0

inputs = UnitEconInputs(
    cac=cac,
    aov=aov,
    orders_per_month=orders_per_month,
    gross_margin_pct=gross_margin_pct,
    variable_cost_per_order=variable_cost,
    monthly_churn_rate=monthly_churn,
    monthly_fixed_costs=monthly_fixed,
    annual_discount_rate=annual_discount_rate,
)

# ── Compute ───────────────────────────────────────────────────────────────────

outputs = compute(inputs)

# ── KPI Cards ─────────────────────────────────────────────────────────────────

st.markdown("## Key Metrics")

show_discounted = st.toggle("Show Discounted LTV", value=False)

if show_discounted:
    kpi_cols = st.columns(6)
else:
    kpi_cols = st.columns(5)

col_idx = 0
with kpi_cols[col_idx]:
    st.metric("LTV", f"${outputs.ltv:,.2f}")
col_idx += 1

if show_discounted:
    with kpi_cols[col_idx]:
        st.metric("Discounted LTV", f"${outputs.discounted_ltv:,.2f}")
    col_idx += 1

with kpi_cols[col_idx]:
    if show_discounted:
        st.metric("LTV : CAC", f"{outputs.ltv_cac_ratio:.2f}x")
        st.metric("Disc. LTV : CAC", f"{outputs.discounted_ltv_cac_ratio:.2f}x")
    else:
        st.metric("LTV : CAC", f"{outputs.ltv_cac_ratio:.2f}x")
col_idx += 1

with kpi_cols[col_idx]:
    payback_label = f"{outputs.payback_months:.1f} mo" if outputs.payback_months < 999 else "∞"
    st.metric("Payback Period", payback_label)
col_idx += 1
with kpi_cols[col_idx]:
    st.metric("Contribution / Order", f"${outputs.contribution_margin_per_order:,.2f}")
col_idx += 1
with kpi_cols[col_idx]:
    color = health_score_color(outputs.health_score)
    st.metric("Health Score", f"{outputs.health_score}/100")

# ── Health Flags ──────────────────────────────────────────────────────────────

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

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_cohort, tab_sensitivity, tab_export = st.tabs([
    "Cohort LTV Curve",
    "Sensitivity Analysis",
    "Export",
])

# ── Tab 1: Cohort LTV Curve ──────────────────────────────────────────────────

with tab_cohort:
    cohort_df = build_cohort_table(inputs, n_months=36)
    payback_month = find_payback_month(cohort_df)

    # Cumulative contribution vs CAC threshold
    fig_ltv = go.Figure()
    fig_ltv.add_trace(go.Scatter(
        x=cohort_df["month"],
        y=cohort_df["cumulative_contribution"],
        mode="lines",
        name="Cumulative Contribution",
        line=dict(color=PRIMARY, width=3),
    ))
    if show_discounted:
        fig_ltv.add_trace(go.Scatter(
            x=cohort_df["month"],
            y=cohort_df["discounted_cumulative_contribution"],
            mode="lines",
            name="Discounted Cumulative Contribution",
            line=dict(color=INDIGO, width=3, dash="dot"),
        ))
    fig_ltv.add_trace(go.Scatter(
        x=cohort_df["month"],
        y=cohort_df["cac_threshold"],
        mode="lines",
        name="Total CAC",
        line=dict(color=RED, width=2, dash="dash"),
    ))
    if payback_month:
        fig_ltv.add_vline(
            x=payback_month,
            line_dash="dot",
            line_color=GREEN,
            line_width=2,
            annotation_text=f"Payback: month {payback_month}",
            annotation_position="top right",
            annotation_font_color=GREEN,
        )
    fig_ltv.update_layout(
        title="Cumulative Contribution vs CAC (1 000 customer cohort)",
        xaxis_title="Month",
        yaxis_title="Dollars ($)",
        template=PLOTLY_TEMPLATE,
        height=420,
    )
    st.plotly_chart(fig_ltv, use_container_width=True)

    if show_discounted:
        st.info(
            "**Discounted LTV** applies the time value of money. "
            "A dollar of customer revenue 3 years from now is worth less than a dollar today. "
            f"Using a {discount_rate_pct}% annual discount rate "
            f"(~{((1 + annual_discount_rate) ** (1/12) - 1) * 100:.2f}%/month)."
        )

    # Survivor % area chart + monthly revenue bar chart side by side
    col_surv, col_rev = st.columns(2)

    with col_surv:
        fig_surv = go.Figure()
        fig_surv.add_trace(go.Scatter(
            x=cohort_df["month"],
            y=cohort_df["survivor_pct"],
            fill="tozeroy",
            name="Survivor %",
            line=dict(color=INDIGO),
            fillcolor=f"rgba(99, 102, 241, 0.25)",
        ))
        fig_surv.update_layout(
            title="Cohort Survival Curve",
            xaxis_title="Month",
            yaxis_title="Surviving %",
            yaxis_tickformat=".0%",
            template=PLOTLY_TEMPLATE,
            height=350,
        )
        st.plotly_chart(fig_surv, use_container_width=True)

    with col_rev:
        fig_rev = go.Figure()
        fig_rev.add_trace(go.Bar(
            x=cohort_df["month"],
            y=cohort_df["monthly_revenue"],
            name="Monthly Revenue",
            marker_color=PRIMARY,
        ))
        fig_rev.update_layout(
            title="Monthly Revenue (cohort)",
            xaxis_title="Month",
            yaxis_title="Revenue ($)",
            template=PLOTLY_TEMPLATE,
            height=350,
        )
        st.plotly_chart(fig_rev, use_container_width=True)

# ── Tab 2: Sensitivity Analysis ──────────────────────────────────────────────

with tab_sensitivity:
    st.subheader("Lever Impact Ranking (10% improvement)")

    tornado_df = tornado_data(inputs, improvement_pct=0.10)

    fig_tornado = go.Figure()
    colors = [GREEN if d > 0 else RED for d in tornado_df["delta"]]
    fig_tornado.add_trace(go.Bar(
        x=tornado_df["pct_delta"],
        y=tornado_df["lever"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in tornado_df["pct_delta"]],
        textposition="outside",
    ))
    fig_tornado.update_layout(
        title="LTV:CAC % Change from 10% Improvement in Each Lever",
        xaxis_title="% Change in LTV:CAC",
        yaxis_title="",
        template=PLOTLY_TEMPLATE,
        height=350,
    )
    st.plotly_chart(fig_tornado, use_container_width=True)

    st.markdown("---")
    st.subheader("Single-Lever Sweep")

    lever_label = st.selectbox("Select lever to sweep", list(LEVERS.keys()))
    lever_field = LEVERS[lever_label]

    sweep_df = sweep_lever(inputs, lever_field, pct_range=0.40, n_points=41)

    fig_sweep = go.Figure()
    fig_sweep.add_trace(go.Scatter(
        x=sweep_df["pct_change"] * 100,
        y=sweep_df["ltv_cac"],
        mode="lines",
        line=dict(color=PRIMARY, width=3),
        name="LTV:CAC",
    ))
    # Mark baseline
    baseline_ratio = outputs.ltv_cac_ratio
    fig_sweep.add_hline(
        y=baseline_ratio,
        line_dash="dash",
        line_color=RED,
        annotation_text=f"Baseline: {baseline_ratio:.2f}x",
        annotation_position="top left",
    )
    fig_sweep.update_layout(
        title=f"LTV:CAC across ±40% change in {lever_label}",
        xaxis_title="% Change",
        yaxis_title="LTV:CAC Ratio",
        template=PLOTLY_TEMPLATE,
        height=400,
    )
    st.plotly_chart(fig_sweep, use_container_width=True)

# ── Tab 3: Export ─────────────────────────────────────────────────────────────

with tab_export:
    st.subheader("Download Results")

    col_json, col_csv = st.columns(2)

    with col_json:
        json_str = summary_to_json(inputs, outputs)
        st.download_button(
            label="Download JSON Summary",
            data=json_str,
            file_name="unit_econ_summary.json",
            mime="application/json",
        )

    with col_csv:
        cohort_df = build_cohort_table(inputs, n_months=36)
        csv_str = cohort_to_csv(cohort_df)
        st.download_button(
            label="Download LTV Curve CSV",
            data=csv_str,
            file_name="ltv_curve.csv",
            mime="text/csv",
        )

    st.markdown("---")
    st.subheader("Input Configuration (JSON)")
    st.code(inputs_to_json(inputs), language="json")
