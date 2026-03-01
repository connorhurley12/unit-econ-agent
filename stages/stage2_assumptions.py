"""Stage 2 — 'Set your assumptions' — Layer-by-layer input cards."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def _slider_with_range(
    label: str,
    value: float,
    min_val: float,
    max_val: float,
    step: float,
    typical_range: list,
    help_text: str,
    key: str,
    fmt: str = "%.2f",
    is_pct: bool = False,
) -> float:
    """Render a slider with typical-range annotation underneath."""
    display_value = value * 100 if is_pct else value
    display_min = min_val * 100 if is_pct else min_val
    display_max = max_val * 100 if is_pct else max_val
    display_step = step * 100 if is_pct else step
    display_typical = [t * 100 for t in typical_range] if is_pct else typical_range
    display_fmt = "%.0f" if is_pct else fmt

    result = st.slider(
        label + (" (%)" if is_pct else ""),
        min_value=display_min,
        max_value=display_max,
        value=display_value,
        step=display_step,
        format=display_fmt,
        key=key,
        help=help_text,
    )

    low, high = display_typical
    unit = "%" if is_pct else ""
    if is_pct:
        st.caption(f"Typical range: {low:.0f}{unit} \u2013 {high:.0f}{unit}")
    elif step >= 1.0:
        st.caption(f"Typical range: ${low:,.0f} \u2013 ${high:,.0f}")
    else:
        st.caption(f"Typical range: ${low:,.2f} \u2013 ${high:,.2f}")

    return result / 100 if is_pct else result


def render() -> None:
    """Render Stage 2: assumption input cards."""
    st.markdown(
        '<h1 style="margin-bottom:0.2em;">Set your assumptions</h1>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Walk through each layer of your unit economics stack. "
        "Adjust sliders \u2014 typical ranges are shown for reference."
    )

    journey = st.session_state.journey_inputs
    mi = journey["model_inputs"]
    layers = journey["layers"]

    # ── Card 1: Demand ────────────────────────────────────────────────────────
    with st.expander("**1. Demand** \u2014 How often do customers order and how much do they spend?", expanded=True):
        aov_meta = layers["demand"]["aov"]
        mi["aov"] = _slider_with_range(
            "Average Order Value ($)",
            value=mi["aov"],
            min_val=aov_meta["min"],
            max_val=aov_meta["max"],
            step=aov_meta["step"],
            typical_range=aov_meta["typical_range"],
            help_text=aov_meta["help"],
            key="s2_aov",
        )

        opm_meta = layers["demand"]["orders_per_month"]
        mi["orders_per_month"] = _slider_with_range(
            "Orders per Month",
            value=mi["orders_per_month"],
            min_val=opm_meta["min"],
            max_val=opm_meta["max"],
            step=opm_meta["step"],
            typical_range=opm_meta["typical_range"],
            help_text=opm_meta["help"],
            key="s2_orders_per_month",
        )

        # Show computed monthly revenue per customer
        monthly_rev = mi["aov"] * mi["orders_per_month"]
        st.info(f"Monthly revenue per customer: **${monthly_rev:,.2f}**")

    # ── Card 2: Revenue & Margins ─────────────────────────────────────────────
    with st.expander("**2. Revenue & Margins** \u2014 What percentage of revenue do you keep?"):
        gm_meta = layers["revenue"]["gross_margin_pct"]
        mi["gross_margin_pct"] = _slider_with_range(
            "Gross Margin",
            value=mi["gross_margin_pct"],
            min_val=gm_meta["min"],
            max_val=gm_meta["max"],
            step=gm_meta["step"],
            typical_range=gm_meta["typical_range"],
            help_text=gm_meta["help"],
            key="s2_gross_margin",
            is_pct=True,
        )

        gross_profit = mi["aov"] * mi["gross_margin_pct"]
        st.info(f"Gross profit per order: **${gross_profit:,.2f}**")

    # ── Card 3: Variable Costs ────────────────────────────────────────────────
    with st.expander("**3. Variable Costs** \u2014 What does it cost to fulfill each order?"):
        vc_meta = layers["costs"]["variable_cost_per_order"]
        mi["variable_cost_per_order"] = _slider_with_range(
            "Variable Cost per Order ($)",
            value=mi["variable_cost_per_order"],
            min_val=vc_meta["min"],
            max_val=vc_meta["max"],
            step=vc_meta["step"],
            typical_range=vc_meta["typical_range"],
            help_text=vc_meta["help"],
            key="s2_variable_cost",
        )

        cm = (mi["aov"] * mi["gross_margin_pct"]) - mi["variable_cost_per_order"]
        color = "#10B981" if cm > 0 else "#EF4444"
        st.markdown(
            f'<div style="padding:8px 12px;border-radius:6px;background:{color}20;'
            f'border-left:3px solid {color};font-size:0.95rem;">'
            f'Contribution margin per order: <strong>${cm:,.2f}</strong></div>',
            unsafe_allow_html=True,
        )

    # ── Card 4: Retention ─────────────────────────────────────────────────────
    with st.expander("**4. Retention** \u2014 How well do you keep customers?"):
        churn_meta = layers["retention"]["monthly_churn_rate"]
        mi["monthly_churn_rate"] = _slider_with_range(
            "Monthly Churn",
            value=mi["monthly_churn_rate"],
            min_val=churn_meta["min"],
            max_val=churn_meta["max"],
            step=churn_meta["step"],
            typical_range=churn_meta["typical_range"],
            help_text=churn_meta["help"],
            key="s2_churn",
            is_pct=True,
        )

        arpu_meta = layers["retention"]["monthly_arpu_growth_rate"]
        mi["monthly_arpu_growth_rate"] = _slider_with_range(
            "Monthly ARPU Growth",
            value=mi["monthly_arpu_growth_rate"],
            min_val=arpu_meta["min"],
            max_val=arpu_meta["max"],
            step=arpu_meta["step"],
            typical_range=arpu_meta["typical_range"],
            help_text=arpu_meta["help"],
            key="s2_arpu_growth",
            is_pct=True,
        )

        avg_lifetime = 1.0 / mi["monthly_churn_rate"] if mi["monthly_churn_rate"] > 0 else float("inf")
        if avg_lifetime < 100:
            st.info(f"Average customer lifetime: **{avg_lifetime:.1f} months**")
        else:
            st.info("Average customer lifetime: **very long** (low churn)")

    # ── Card 5: Fixed Costs & Acquisition ─────────────────────────────────────
    with st.expander("**5. Fixed Costs & Acquisition** \u2014 Overhead and customer acquisition channels"):
        fc_meta = layers["fixed_costs"]["monthly_fixed_costs"]
        mi["monthly_fixed_costs"] = st.number_input(
            "Monthly Fixed Costs ($)",
            min_value=fc_meta["min"],
            max_value=fc_meta["max"],
            value=mi["monthly_fixed_costs"],
            step=fc_meta["step"],
            help=fc_meta["help"],
            key="s2_fixed_costs",
        )
        low, high = fc_meta["typical_range"]
        st.caption(f"Typical range: ${low:,.0f} \u2013 ${high:,.0f}")

        st.markdown("---")
        st.markdown("**Acquisition Channels**")

        default_channels = mi.get("channels", [
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
            key="s2_channel_editor",
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

        mi["channels"] = channels

        total_pct = sum(ch["pct_of_new_customers"] for ch in channels)
        if abs(total_pct - 1.0) > 0.001:
            st.warning(f"Channel percentages sum to {total_pct * 100:.1f}% \u2014 should equal 100%")

        blended_cac = sum(ch["cac"] * ch["pct_of_new_customers"] for ch in channels) if channels else 0.0
        st.caption(f"**Blended CAC: ${blended_cac:,.2f}**")

    # Discount rate (advanced, hidden by default)
    with st.expander("Advanced: Discount Rate"):
        discount_pct = st.slider(
            "Annual Discount Rate (%)", 0, 30,
            value=int(mi.get("annual_discount_rate", 0.10) * 100),
            key="s2_discount_rate",
        )
        mi["annual_discount_rate"] = discount_pct / 100.0
        st.caption("Used for discounted LTV (NPV) calculations. 10% is typical.")

    # Store back
    st.session_state.journey_inputs = journey
