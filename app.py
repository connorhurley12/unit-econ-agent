"""unit-econ-builder — Guided journey for unit economics modeling."""

import streamlit as st

from stages import navigate, render_progress_bar
from stages.stage1_archetype import render as render_stage1
from stages.stage2_assumptions import render as render_stage2
from stages.stage3_snapshot import render as render_stage3
from stages.stage4_whatif import render as render_stage4
from stages.stage5_playbook import render as render_stage5

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Unit Econ Builder",
    page_icon="📊",
    layout="wide",
)

# ── Session state defaults ────────────────────────────────────────────────────

if "stage" not in st.session_state:
    st.session_state.stage = 1
if "journey_inputs" not in st.session_state:
    st.session_state.journey_inputs = {}
if "template_name" not in st.session_state:
    st.session_state.template_name = None

# ── Stage renderers ──────────────────────────────────────────────────────────

STAGE_RENDERERS = {
    1: render_stage1,
    2: render_stage2,
    3: render_stage3,
    4: render_stage4,
    5: render_stage5,
}

# ── Main ──────────────────────────────────────────────────────────────────────

# Render progress bar
render_progress_bar(st.session_state.stage)

# Guard: stages 2+ require archetype selection
if st.session_state.stage > 1 and not st.session_state.journey_inputs:
    st.session_state.stage = 1

# Render current stage
renderer = STAGE_RENDERERS[st.session_state.stage]
renderer()

# Navigation (except stage 1 which handles its own via archetype selection)
if st.session_state.stage > 1:
    navigate(st.session_state.stage)
