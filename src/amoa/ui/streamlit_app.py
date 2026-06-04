"""
AMOA Streamlit demo UI.
Four panels: scenario selector, agent assessments, resolver decision, failure log.
Run: uv run streamlit run src/amoa/ui/streamlit_app.py
"""
import asyncio
import streamlit as st
from amoa.graph import build_graph, run_demo
from amoa.state import MissionState

st.set_page_config(page_title="AMOA — Mission Operations", layout="wide")
st.title("AMOA — Autonomous Mission Operations Agent")

scenario = st.selectbox(
    "Select scenario",
    ["high_risk", "medium_risk", "low_risk"],
    index=0,
)

if st.button("Run Mission Assessment"):
    with st.spinner("Running agents..."):
        state = asyncio.run(run_demo())

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Safety Pilot")
        if state.safety_assessment:
            a = state.safety_assessment
            st.metric("Risk Level", a.risk_level.value)
            st.metric("PC", f"{a.pc:.2e}")
            st.metric("Miss Distance", f"{a.miss_distance_m:.1f} m")
            st.write(f"**Action:** {a.recommended_action.value}")
            st.write(f"**Reasoning:** {a.reasoning}")
        else:
            st.error("Safety Pilot failed")

    with col2:
        st.subheader("Health Guard")
        if state.health_assessment:
            h = state.health_assessment
            st.metric("Severity", h.severity.value)
            st.metric("Anomaly Detected", str(h.anomaly_detected))
            st.write(f"**Channels:** {', '.join(h.affected_channels) or 'None'}")
            st.write(f"**Reasoning:** {h.reasoning}")
        else:
            st.error("Health Guard failed")

    with col3:
        st.subheader("Payload Scientist")
        if state.payload_assessment:
            p = state.payload_assessment
            st.metric("Cloud Cover", f"{p.cloud_coverage_pct:.1f}%")
            st.metric("Image Quality", p.image_quality.value)
            st.metric("Obs. Value", f"{p.observation_value:.2f}")
            st.write(f"**Reasoning:** {p.reasoning}")
        else:
            st.error("Payload Scientist failed")

    st.divider()
    st.subheader("Conflict Resolver Decision")
    if state.supervisor_decision:
        d = state.supervisor_decision
        st.metric("Priority Action", d.priority_action)
        st.metric("Confidence", f"{d.confidence:.0%}")
        if d.degraded_mode:
            st.warning("Degraded mode — one or more agents failed")
        st.write(f"**Reasoning:** {d.reasoning}")

    if state.failure_log:
        st.divider()
        st.subheader("Failure Log")
        for f in state.failure_log:
            st.error(f"**{f.agent}** — {f.category}: {f.error}")