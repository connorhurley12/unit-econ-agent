"""unit-econ-builder — Streamlit web app for unit economics modeling."""

import json
from pathlib import Path

import pandas as pd
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
from src.comparison import (
    COLOR_BG_HEX,
    COLOR_HEX,
    build_comparison_rows,
    cell_color,
    format_value,
    generate_verdict,
)
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
YELLOW = "#F59E0B"
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

    st.subheader("Acquisition Channels")

    default_channels = defaults.get("channels", [
        {"name": "Paid", "cac": 25.0, "pct_of_new_customers": 0.60},
        {"name": "Organic", "cac": 8.0, "pct_of_new_customers": 0.30},
        {"name": "Referral", "cac": 4.0, "pct_of_new_customers": 0.10},
    ])

    channel_df = pd.DataFrame(default_channels)
    channel_df["pct_of_new_customers"] = channel_df["pct_of_new_customers"] * 100
    channel_df = channel_df.rename(columns={
        "name": "Channel",
        "cac": "CAC ($)",
        "pct_of_new_customers": "% of New Cust.",
    })

    edited_df = st.data_editor(
        channel_df,
        num_rows="dynamic",
        column_config={
            "Channel": st.column_config.TextColumn(required=True),
            "CAC ($)": st.column_config.NumberColumn(min_value=0.0, format="%.2f", required=True),
            "% of New Cust.": st.column_config.NumberColumn(min_value=0.0, max_value=100.0, format="%.1f", required=True),
        },
        hide_index=True,
        key=f"channel_editor_{preset}",
    )

    channels = []
    for _, row in edited_df.iterrows():
        name = row.get("Channel", "")
        cac_val = row.get("CAC ($)", 0.0)
        pct_val = row.get("% of New Cust.", 0.0)
        if pd.isna(name) or str(name).strip() == "":
            continue
        channels.append({
            "name": str(name),
            "cac": float(cac_val) if not pd.isna(cac_val) else 0.0,
            "pct_of_new_customers": (float(pct_val) if not pd.isna(pct_val) else 0.0) / 100.0,
        })

    total_pct = sum(ch["pct_of_new_customers"] for ch in channels)
    if abs(total_pct - 1.0) > 0.001:
        st.warning(f"Channel percentages sum to {total_pct * 100:.1f}% — must equal 100%")

    blended_cac = sum(ch["cac"] * ch["pct_of_new_customers"] for ch in channels) if channels else 0.0
    st.caption(f"**Blended CAC: ${blended_cac:,.2f}**")

    st.markdown("---")
    st.subheader("Model Inputs")

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
    aov=aov,
    orders_per_month=orders_per_month,
    gross_margin_pct=gross_margin_pct,
    variable_cost_per_order=variable_cost,
    monthly_churn_rate=monthly_churn,
    monthly_fixed_costs=monthly_fixed,
    monthly_arpu_growth_rate=monthly_arpu_growth,
    annual_discount_rate=annual_discount_rate,
    channels=channels,
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

if monthly_arpu_growth > 0:
    st.info("Negative churn active — expansion revenue is outpacing lost customers")

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_cohort, tab_sensitivity, tab_comparison, tab_export = st.tabs([
    "Cohort LTV Curve",
    "Sensitivity Analysis",
    "⚖️ Segment Comparison",
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
    if inputs.monthly_arpu_growth_rate > 0:
        # Annotate the expansion effect on the curve
        mid_month = len(cohort_df) // 2
        fig_ltv.add_annotation(
            x=cohort_df["month"].iloc[mid_month],
            y=cohort_df["cumulative_contribution"].iloc[mid_month],
            text=f"Expansion: +{inputs.monthly_arpu_growth_rate:.0%}/mo ARPU growth",
            showarrow=True,
            arrowhead=2,
            arrowcolor=GREEN,
            font=dict(color=GREEN, size=12),
            ax=40,
            ay=-40,
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

    # ── Per-channel LTV:CAC bar chart ────────────────────────────────────────
    if inputs.channels:
        st.markdown("### LTV : CAC by Channel")

        ch_names = []
        ch_ratios = []
        ch_colors = []
        for ch in inputs.channels:
            ratio = outputs.ltv / ch["cac"] if ch["cac"] > 0 else float("inf")
            ch_names.append(ch["name"])
            ch_ratios.append(ratio)
            if ratio >= 3.0:
                ch_colors.append(GREEN)
            elif ratio >= 1.0:
                ch_colors.append(YELLOW)
            else:
                ch_colors.append(RED)

        fig_ch = go.Figure()
        fig_ch.add_trace(go.Bar(
            y=ch_names,
            x=ch_ratios,
            orientation="h",
            marker_color=ch_colors,
            text=[f"{r:.2f}x" for r in ch_ratios],
            textposition="outside",
        ))
        fig_ch.add_vline(
            x=3.0, line_dash="dot", line_color=GREEN, line_width=1,
            annotation_text="3x", annotation_position="top",
        )
        fig_ch.add_vline(
            x=1.0, line_dash="dot", line_color=RED, line_width=1,
            annotation_text="1x", annotation_position="top",
        )
        fig_ch.update_layout(
            title="LTV : CAC Ratio by Acquisition Channel",
            xaxis_title="LTV : CAC",
            yaxis_title="",
            template=PLOTLY_TEMPLATE,
            height=max(250, len(inputs.channels) * 60 + 100),
        )
        st.plotly_chart(fig_ch, use_container_width=True)

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

# ── Tab 3: Segment Comparison ────────────────────────────────────────────

with tab_comparison:
    st.subheader("Segment Comparison")
    st.caption("Compare two customer segments side by side. Each segment is computed independently.")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Segment A")
        seg_a_cac = st.number_input("CAC ($)", min_value=0.0, value=inputs.cac, step=1.0, format="%.2f", key="seg_a_cac")
        seg_a_aov = st.number_input("AOV ($)", min_value=0.01, value=inputs.aov, step=1.0, format="%.2f", key="seg_a_aov")
        seg_a_orders = st.number_input("Orders / month", min_value=0.1, value=inputs.orders_per_month, step=0.1, format="%.1f", key="seg_a_orders")
        seg_a_gm = st.slider("Gross Margin %", min_value=0, max_value=100, value=int(inputs.gross_margin_pct * 100), key="seg_a_gm") / 100.0
        seg_a_vc = st.number_input("Variable Cost / Order ($)", min_value=0.0, value=inputs.variable_cost_per_order, step=0.10, format="%.2f", key="seg_a_vc")
        seg_a_churn = st.slider("Monthly Churn %", min_value=0, max_value=50, value=int(inputs.monthly_churn_rate * 100), key="seg_a_churn") / 100.0

    with col_b:
        st.markdown("#### Segment B")
        # Default B to a contrasting profile: higher CAC, lower churn (enterprise-like)
        default_b_cac = round(inputs.cac * 2.5, 2)
        default_b_aov = round(inputs.aov * 1.8, 2)
        default_b_churn = max(1, int(inputs.monthly_churn_rate * 100) // 2)
        seg_b_cac = st.number_input("CAC ($)", min_value=0.0, value=default_b_cac, step=1.0, format="%.2f", key="seg_b_cac")
        seg_b_aov = st.number_input("AOV ($)", min_value=0.01, value=default_b_aov, step=1.0, format="%.2f", key="seg_b_aov")
        seg_b_orders = st.number_input("Orders / month", min_value=0.1, value=inputs.orders_per_month, step=0.1, format="%.1f", key="seg_b_orders")
        seg_b_gm = st.slider("Gross Margin %", min_value=0, max_value=100, value=int(inputs.gross_margin_pct * 100), key="seg_b_gm") / 100.0
        seg_b_vc = st.number_input("Variable Cost / Order ($)", min_value=0.0, value=inputs.variable_cost_per_order, step=0.10, format="%.2f", key="seg_b_vc")
        seg_b_churn = st.slider("Monthly Churn %", min_value=0, max_value=50, value=default_b_churn, key="seg_b_churn") / 100.0

    # Build independent inputs for each segment
    seg_a_inputs = UnitEconInputs(
        cac=seg_a_cac, aov=seg_a_aov, orders_per_month=seg_a_orders,
        gross_margin_pct=seg_a_gm, variable_cost_per_order=seg_a_vc,
        monthly_churn_rate=seg_a_churn,
    )
    seg_b_inputs = UnitEconInputs(
        cac=seg_b_cac, aov=seg_b_aov, orders_per_month=seg_b_orders,
        gross_margin_pct=seg_b_gm, variable_cost_per_order=seg_b_vc,
        monthly_churn_rate=seg_b_churn,
    )

    seg_a_out = compute(seg_a_inputs)
    seg_b_out = compute(seg_b_inputs)

    # ── Comparison table ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Metric Comparison")

    rows = build_comparison_rows(seg_a_out, seg_b_out)
    # Inject actual CAC values (since we have them directly)
    for row in rows:
        if row.label == "CAC":
            row.value_a = seg_a_cac
            row.value_b = seg_b_cac

    header = "| Metric | Segment A | Segment B |"
    sep = "|:-------|:---------:|:---------:|"
    table_lines = [header, sep]
    for row in rows:
        val_a = format_value(row.fmt, row.value_a)
        val_b = format_value(row.fmt, row.value_b)
        color_a = cell_color(row.label, row.value_a)
        color_b = cell_color(row.label, row.value_b)
        hex_a = COLOR_HEX[color_a]
        hex_b = COLOR_HEX[color_b]
        bg_a = COLOR_BG_HEX[color_a]
        bg_b = COLOR_BG_HEX[color_b]
        cell_a = f'<span style="color:{hex_a};background:{bg_a};padding:2px 8px;border-radius:4px;font-weight:600">{val_a}</span>'
        cell_b = f'<span style="color:{hex_b};background:{bg_b};padding:2px 8px;border-radius:4px;font-weight:600">{val_b}</span>'
        table_lines.append(f"| **{row.label}** | {cell_a} | {cell_b} |")

    st.markdown("\n".join(table_lines), unsafe_allow_html=True)

    # ── Grouped bar chart ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Side-by-Side Metrics")

    chart_metrics = ["LTV", "CAC", "LTV:CAC", "Payback (mo)", "CM / Order", "Health Score"]
    vals_a = [seg_a_out.ltv, seg_a_cac, seg_a_out.ltv_cac_ratio, seg_a_out.payback_months, seg_a_out.contribution_margin_per_order, seg_a_out.health_score]
    vals_b = [seg_b_out.ltv, seg_b_cac, seg_b_out.ltv_cac_ratio, seg_b_out.payback_months, seg_b_out.contribution_margin_per_order, seg_b_out.health_score]

    # Cap infinite payback for display
    vals_a = [v if v != float("inf") else 0 for v in vals_a]
    vals_b = [v if v != float("inf") else 0 for v in vals_b]

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Bar(
        name="Segment A",
        x=chart_metrics,
        y=vals_a,
        marker_color=PRIMARY,
        text=[f"{v:,.1f}" for v in vals_a],
        textposition="outside",
    ))
    fig_cmp.add_trace(go.Bar(
        name="Segment B",
        x=chart_metrics,
        y=vals_b,
        marker_color=INDIGO,
        text=[f"{v:,.1f}" for v in vals_b],
        textposition="outside",
    ))
    fig_cmp.update_layout(
        barmode="group",
        template=PLOTLY_TEMPLATE,
        height=450,
        yaxis_title="Value",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

    # ── Verdict ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Verdict")

    verdicts = generate_verdict(seg_a_inputs, seg_b_inputs, seg_a_out, seg_b_out)
    for v in verdicts:
        st.markdown(f"- {v}")

# ── Tab 4: Export ─────────────────────────────────────────────────────────────

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
