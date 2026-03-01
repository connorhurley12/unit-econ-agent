"""Stage 4 — 'What if?' — Scenario simulation with side-by-side waterfalls."""

from __future__ import annotations

import streamlit as st

from src.model import compute
from src.scenarios import (
    Scenario,
    apply_scenario,
    generate_impact_summary,
    get_default_scenarios,
)
from src.sensitivity import LEVERS, tweak_input
from src.waterfall import build_waterfall_data, create_waterfall_figure


def render() -> None:
    """Render Stage 4: what-if scenario explorer."""
    st.markdown(
        '<h1 style="margin-bottom:0.2em;">What If?</h1>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Pull one lever at a time and see how it changes your unit economics. "
        "Pick a pre-built scenario or build your own."
    )

    inputs = st.session_state.inputs
    outputs = st.session_state.outputs

    # ── Pre-built scenario buttons ────────────────────────────────────────────
    st.subheader("Quick Scenarios")

    scenarios = get_default_scenarios()

    # Initialize active scenario tracking
    if "active_scenario_idx" not in st.session_state:
        st.session_state.active_scenario_idx = None
    if "custom_scenario_active" not in st.session_state:
        st.session_state.custom_scenario_active = False

    cols = st.columns(3)
    for i, scenario in enumerate(scenarios):
        with cols[i % 3]:
            if st.button(
                scenario.name,
                key=f"scenario_{i}",
                help=scenario.description,
                use_container_width=True,
            ):
                st.session_state.active_scenario_idx = i
                st.session_state.custom_scenario_active = False

    # ── Custom lever builder ──────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Or Build Your Own")

    lever_label = st.selectbox("Select a lever", list(LEVERS.keys()), key="s4_lever")
    lever_field = LEVERS[lever_label]

    pct_change = st.slider(
        "% Change",
        min_value=-50,
        max_value=50,
        value=10,
        step=5,
        key="s4_pct_change",
        format="%+d%%",
    )

    if st.button("Apply Custom Scenario", key="apply_custom"):
        st.session_state.custom_scenario_active = True
        st.session_state.active_scenario_idx = None

    # ── Determine the active scenario ─────────────────────────────────────────
    tweaked_inputs = None
    scenario_label = None

    if st.session_state.active_scenario_idx is not None:
        idx = st.session_state.active_scenario_idx
        scenario = scenarios[idx]
        tweaked_inputs, tweaked_outputs = apply_scenario(inputs, scenario)
        scenario_label = scenario.name

    elif st.session_state.custom_scenario_active:
        tweaked_inputs = tweak_input(inputs, lever_field, pct_change / 100.0)
        tweaked_outputs = compute(tweaked_inputs)
        scenario_label = f"{lever_label} {pct_change:+d}%"

    # ── Side-by-side comparison ───────────────────────────────────────────────
    if tweaked_inputs is not None:
        st.markdown("---")
        st.subheader(f"Scenario: {scenario_label}")

        col_before, col_after = st.columns(2)

        with col_before:
            st.markdown("#### Current")
            fig_before = create_waterfall_figure(
                build_waterfall_data(inputs),
                title="Before",
                height=380,
            )
            st.plotly_chart(fig_before, use_container_width=True)

            st.metric("CM / Order", f"${outputs.contribution_margin_per_order:,.2f}")
            st.metric("LTV:CAC", f"{outputs.ltv_cac_ratio:.2f}x")

        with col_after:
            st.markdown("#### After Scenario")
            fig_after = create_waterfall_figure(
                build_waterfall_data(tweaked_inputs),
                title="After",
                height=380,
            )
            st.plotly_chart(fig_after, use_container_width=True)

            st.metric(
                "CM / Order",
                f"${tweaked_outputs.contribution_margin_per_order:,.2f}",
                delta=f"${tweaked_outputs.contribution_margin_per_order - outputs.contribution_margin_per_order:,.2f}",
            )
            st.metric(
                "LTV:CAC",
                f"{tweaked_outputs.ltv_cac_ratio:.2f}x",
                delta=f"{tweaked_outputs.ltv_cac_ratio - outputs.ltv_cac_ratio:,.2f}x",
            )

        # ── Impact narrative ──────────────────────────────────────────────────
        st.markdown("---")
        summary = generate_impact_summary(inputs, outputs, tweaked_inputs, tweaked_outputs)
        st.info(f"**Impact:** {summary}")
    else:
        st.markdown("---")
        st.markdown(
            '<div style="text-align:center;padding:40px;color:#9CA3AF;">'
            "Select a scenario above to see the impact on your unit economics."
            "</div>",
            unsafe_allow_html=True,
        )
