"""Stage 1 — 'What's your business?' — Archetype selection."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from stages import go_next

ARCHETYPES_DIR = Path("data/archetypes")

ARCHETYPE_FILES = {
    "Delivery Marketplace": "delivery_marketplace.json",
    "SaaS Marketplace": "saas_marketplace.json",
    "Services Marketplace": "services_marketplace.json",
    "Custom": "custom.json",
}


def _load_archetype(name: str) -> dict:
    """Load an archetype JSON file."""
    path = ARCHETYPES_DIR / ARCHETYPE_FILES[name]
    with open(path) as f:
        return json.load(f)


def _select_archetype(name: str) -> None:
    """Callback: load archetype into session state and advance."""
    data = _load_archetype(name)
    st.session_state.template_name = name
    st.session_state.journey_inputs = data
    go_next()


def render() -> None:
    """Render Stage 1: business type selection."""
    st.markdown(
        '<h1 style="text-align:center;margin-bottom:0.2em;">What type of business are you building?</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="text-align:center;color:#6B7280;margin-bottom:2em;">'
        "Pick a template to start with sensible defaults. You can customize everything in the next step.</p>",
        unsafe_allow_html=True,
    )

    cols = st.columns(4, gap="large")

    for col, name in zip(cols, ARCHETYPE_FILES.keys()):
        data = _load_archetype(name)
        mi = data["model_inputs"]

        with col:
            st.markdown(
                f'<div style="text-align:center;font-size:2.5rem;">{data["icon"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(f"#### {name}")
            st.caption(data["description"])

            # Show key defaults
            st.markdown(
                f"AOV **${mi['aov']:,.0f}** &bull; "
                f"GM **{mi['gross_margin_pct']:.0%}** &bull; "
                f"Churn **{mi['monthly_churn_rate']:.0%}**/mo"
            )

            st.button(
                f"Select",
                key=f"select_{name}",
                on_click=_select_archetype,
                args=(name,),
                use_container_width=True,
                type="primary" if name != "Custom" else "secondary",
            )
