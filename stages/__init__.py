"""Journey stage navigation infrastructure."""

from __future__ import annotations

import streamlit as st


STAGE_LABELS = [
    "Business Type",
    "Assumptions",
    "Snapshot",
    "What If?",
    "Playbook",
]


def render_progress_bar(current: int) -> None:
    """Render a horizontal 5-step progress indicator."""
    cols = st.columns(5)
    for i, (col, label) in enumerate(zip(cols, STAGE_LABELS), start=1):
        with col:
            if i < current:
                st.markdown(
                    f'<div style="text-align:center;padding:8px 0;">'
                    f'<span style="color:#10B981;font-size:1.3rem;">&#10003;</span><br>'
                    f'<span style="font-size:0.85rem;color:#6B7280;">{label}</span></div>',
                    unsafe_allow_html=True,
                )
            elif i == current:
                st.markdown(
                    f'<div style="text-align:center;padding:8px 0;">'
                    f'<span style="color:#3B82F6;font-size:1.3rem;">&#9679;</span><br>'
                    f'<span style="font-size:0.85rem;font-weight:700;color:#3B82F6;">{label}</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="text-align:center;padding:8px 0;">'
                    f'<span style="color:#D1D5DB;font-size:1.3rem;">&#9675;</span><br>'
                    f'<span style="font-size:0.85rem;color:#D1D5DB;">{label}</span></div>',
                    unsafe_allow_html=True,
                )
    st.markdown("---")


def go_next() -> None:
    """Advance to the next stage."""
    st.session_state.stage = min(st.session_state.stage + 1, 5)


def go_back() -> None:
    """Return to the previous stage."""
    st.session_state.stage = max(st.session_state.stage - 1, 1)


def go_to(stage: int) -> None:
    """Jump to a specific stage."""
    st.session_state.stage = max(1, min(stage, 5))


def navigate(current: int) -> None:
    """Render back/next navigation buttons at the bottom of a stage."""
    st.markdown("---")
    left, _, right = st.columns([1, 6, 1])

    if current > 1:
        with left:
            st.button("Back", on_click=go_back, use_container_width=True)

    if current < 5:
        with right:
            st.button("Next", on_click=go_next, type="primary", use_container_width=True)
    else:
        with right:
            st.button("Start Over", on_click=lambda: go_to(1), use_container_width=True)
