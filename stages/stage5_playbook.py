"""Stage 5 — 'Your playbook' — Executive summary, tornado chart, recommendations, export."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.cohorts import build_cohort_table
from src.export import cohort_to_csv, summary_to_json
from src.playbook import generate_executive_summary, generate_pdf, generate_recommendations
from src.sensitivity import tornado_data

# ── Colors ────────────────────────────────────────────────────────────────────

GREEN = "#10B981"
RED = "#EF4444"
PLOTLY_TEMPLATE = "plotly_white"


def render() -> None:
    """Render Stage 5: the playbook."""
    st.markdown(
        '<h1 style="margin-bottom:0.2em;">Your Playbook</h1>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Your model summary, most sensitive levers, and recommended moves \u2014 "
        "all in one place. Export as PDF to share."
    )

    inputs = st.session_state.inputs
    outputs = st.session_state.outputs
    template_name = st.session_state.get("template_name", "Custom")

    # ── Executive summary ─────────────────────────────────────────────────────
    st.subheader("Model Overview")
    st.markdown(f"**Business type:** {template_name}")

    col_in, col_out = st.columns(2)

    with col_in:
        st.markdown("**Key Inputs**")
        st.markdown(f"- AOV: **${inputs.aov:,.2f}**")
        st.markdown(f"- Orders/month: **{inputs.orders_per_month:.1f}**")
        st.markdown(f"- Gross margin: **{inputs.gross_margin_pct:.0%}**")
        st.markdown(f"- Variable cost/order: **${inputs.variable_cost_per_order:,.2f}**")
        st.markdown(f"- Monthly churn: **{inputs.monthly_churn_rate:.0%}**")
        st.markdown(f"- Blended CAC: **${inputs.blended_cac:,.2f}**")
        st.markdown(f"- Fixed costs: **${inputs.monthly_fixed_costs:,.0f}/mo**")

    with col_out:
        st.markdown("**Key Outputs**")
        m1, m2 = st.columns(2)
        with m1:
            st.metric("LTV", f"${outputs.ltv:,.2f}")
            payback = f"{outputs.payback_months:.1f} mo" if outputs.payback_months < 999 else "N/A"
            st.metric("Payback", payback)
        with m2:
            st.metric("LTV:CAC", f"{outputs.ltv_cac_ratio:.2f}x")
            st.metric("Health Score", f"{outputs.health_score}/100")

    # ── Tornado chart ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Most Sensitive Levers")
    st.caption("Which inputs swing your margin the most? A 10% improvement in each lever:")

    t_df = tornado_data(inputs, improvement_pct=0.10)

    fig_tornado = go.Figure()
    colors = [GREEN if d > 0 else RED for d in t_df["delta"]]
    fig_tornado.add_trace(go.Bar(
        x=t_df["pct_delta"],
        y=t_df["lever"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in t_df["pct_delta"]],
        textposition="outside",
    ))
    fig_tornado.update_layout(
        title="LTV:CAC % Change from 10% Improvement",
        xaxis_title="% Change in LTV:CAC",
        yaxis_title="",
        template=PLOTLY_TEMPLATE,
        height=350,
    )
    st.plotly_chart(fig_tornado, use_container_width=True)

    # ── Recommendations ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Recommended Moves")

    recommendations = generate_recommendations(inputs, outputs, t_df)
    for i, rec in enumerate(recommendations, 1):
        st.markdown(f"**{i}.** {rec}")

    # ── Export ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Export")

    col_pdf, col_json, col_csv = st.columns(3)

    with col_pdf:
        pdf_bytes = generate_pdf(inputs, outputs, t_df, recommendations, template_name)
        st.download_button(
            label="Download PDF Playbook",
            data=pdf_bytes,
            file_name="unit_econ_playbook.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with col_json:
        json_str = summary_to_json(inputs, outputs)
        st.download_button(
            label="Download JSON Summary",
            data=json_str,
            file_name="unit_econ_summary.json",
            mime="application/json",
            use_container_width=True,
        )

    with col_csv:
        cohort_df = build_cohort_table(inputs, n_months=36)
        csv_str = cohort_to_csv(cohort_df)
        st.download_button(
            label="Download LTV Curve CSV",
            data=csv_str,
            file_name="ltv_curve.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ── Full text summary ─────────────────────────────────────────────────────
    with st.expander("View text summary"):
        summary = generate_executive_summary(inputs, outputs, template_name)
        st.code(summary, language=None)
