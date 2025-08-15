
import streamlit as st
import pandas as pd
import numpy as np
from battery_guardian.data import sample_catalog, generate_synthetic_usage
from battery_guardian.model import train_model
from battery_guardian.simulate import simulate_curves
from battery_guardian.utils import compute_savings
from battery_guardian.assistant import generate_tips, chatbot_reply

st.set_page_config(page_title="AI Battery Guardian", page_icon="🔋", layout="wide")
st.title("🔋 AI Battery Guardian — On-Device Intelligent Battery Optimization (Simulated)")
st.markdown("Privacy-first, adaptive optimization with explainable tips and a chat assistant.")

# ---- Sidebar controls ----
with st.sidebar:
    st.header("Simulation Controls")
    catalog = sample_catalog()
    app_names = [a.name for a in catalog]
    selected = st.selectbox("Target App", app_names, index=0)
    hours_total = st.slider("Total Simulation Hours", 4, 24, 12, step=1)
    aggressiveness = st.slider("Optimization Aggressiveness", 0.1, 1.0, 0.6, step=0.05)
    seed = st.number_input("Random Seed", 0, 9999, 42, step=1)
    st.markdown("---")
    st.subheader("Real-time Mode (Simulated)")
    st.caption("Advance time to simulate live monitoring.")
    if "t" not in st.session_state:
        st.session_state.t = 1
    colx1, colx2, colx3 = st.columns([1,1,1])
    with colx1:
        if st.button("⏮ Reset"):
            st.session_state.t = 1
    with colx2:
        if st.button("⏭ Next Tick (+1h)"):
            st.session_state.t = min(st.session_state.t + 1, hours_total)
    with colx3:
        st.write(f"Current hour: **{st.session_state.t} / {hours_total}**")
    st.markdown("---")
    show_actions = st.checkbox("Show actions table", value=True)
    st.markdown("---")
    st.caption("Tip: Increase hours & aggressiveness to see bigger impact.")

# ---- Generate data & train ----
profile = next(p for p in sample_catalog() if p.name == selected)
df_usage = generate_synthetic_usage(profile, hours=hours_total, seed=int(seed))
model = train_model(df_usage)

# Slice up to the current time tick for 'live' feel
current_hours = int(st.session_state.t)
df_now = df_usage.head(current_hours)

# Simulate curves
sim_df = simulate_curves(model, df_now, start_battery=100.0, hours=current_hours, aggressiveness=float(aggressiveness))

# Compute metrics
metrics = compute_savings(sim_df)
current_battery = float(sim_df["optimized_battery_pct"].iloc[-1]) if not sim_df.empty else 100.0

tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "💡 AI Tips", "💬 Assistant"])

with tab1:
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.subheader("Battery % Over Time — Baseline vs Optimized")
        chart_df = sim_df[["hour", "baseline_battery_pct", "optimized_battery_pct"]].set_index("hour")
        st.line_chart(chart_df)

    with col2:
        st.subheader("Drain Rate — % per Hour")
        chart_df2 = sim_df[["hour", "baseline_drain_pct_per_h", "optimized_drain_pct_per_h"]].set_index("hour")
        st.line_chart(chart_df2)

    st.markdown("### 📊 Impact Metrics")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Battery Saved (%) so far", f"{metrics['battery_saved_pct']}%")
    with c2:
        st.metric("Extra Hours Above 20%", f"{metrics['extra_hours_above_20pct']} hrs")
    with c3:
        st.metric("Current Battery (Optimized)", f"{current_battery:.1f}%")

    st.markdown("### 🧠 Applied Optimizations (Explainability)")
    if show_actions:
        rows = []
        for i, acts in enumerate(sim_df["actions"]):
            if isinstance(acts, list) and acts:
                for a in acts:
                    rows.append({"hour": int(sim_df['hour'].iloc[i]), **a})
            else:
                rows.append({"hour": int(sim_df['hour'].iloc[i]), "agent": "-", "description": "No action", "est_saving_pct": 0.0})
        st.dataframe(pd.DataFrame(rows))

    with st.expander("See Synthetic Usage Inputs (up to current hour)"):
        st.dataframe(df_now)

with tab2:
    st.subheader("Context-Aware Battery Saving Tips")
    if current_hours >= 1:
        row_now = df_now.iloc[-1]
        drain_before = float(sim_df["baseline_drain_pct_per_h"].iloc[-1])
        drain_after = float(sim_df["optimized_drain_pct_per_h"].iloc[-1])
        tips = generate_tips(row_now, drain_before, drain_after, current_battery)
        if tips:
            for tip in tips:
                with st.container(border=True):
                    st.markdown(f"**{tip['title']}**  \n{tip['reason']}  \n*Estimated extra time:* **{tip['est_gain']}**")
        else:
            st.info("No tips right now — usage looks efficient.")
    else:
        st.info("Advance the simulation to get tips.")

with tab3:
    st.subheader("Ask the Battery Assistant")
    st.caption("Example: 'How can I save battery now?' or 'Is background sync draining power?'")
    user_msg = st.text_input("Your message", value="How can I save battery now?")
    if st.button("Send"):
        ctx = {
            "app": selected,
            "battery": current_battery,
            "extra_hours": metrics['extra_hours_above_20pct']
        }
        reply = chatbot_reply(user_msg, ctx)
        st.success(reply)

st.markdown("---")
st.caption("This is a simulation to showcase on-device, privacy-preserving battery optimization with modular agents and an intelligent assistant.")
