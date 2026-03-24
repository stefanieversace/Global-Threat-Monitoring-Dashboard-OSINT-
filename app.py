import streamlit as st
from scripts.threat_monitor import generate_brief

st.set_page_config(page_title="OSINT Threat Monitor", layout="wide")

st.title("🌍 Global OSINT Threat Monitor")

st.markdown("Real-time monitoring of global security threats using open-source intelligence.")

if st.button("Generate Intelligence Brief"):
    brief = generate_brief()
    st.text_area("Daily Intelligence Brief", brief, height=500)
