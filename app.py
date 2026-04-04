import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timezone

st.set_page_config(layout="wide")

# ==============================
# DATA
# ==============================
data = [
    ["INC-1", "London", 51.5074, -0.1278, "High", 80],
    ["INC-2", "New York", 40.7128, -74.0060, "Critical", 95],
    ["INC-3", "Sydney", -33.8688, 151.2093, "Medium", 60],
    ["INC-4", "Berlin", 52.52, 13.405, "Low", 40],
]

df = pd.DataFrame(data, columns=[
    "incident_id", "region", "lat", "lon", "severity", "risk_score"
])

# ==============================
# SIDEBAR
# ==============================
st.sidebar.title("Controls")
selected = st.sidebar.selectbox("Select Incident", df["incident_id"])

selected_row = df[df["incident_id"] == selected].iloc[0]

# ==============================
# HEADER
# ==============================
st.title("🛰️ Threat Intelligence Dashboard")

col1, col2, col3 = st.columns(3)

col1.metric("Incidents", len(df))
col2.metric("Highest Risk", df["risk_score"].max())
col3.metric("Selected", selected)

# ==============================
# MAP (GUARANTEED WORKING)
# ==============================
st.subheader("🌍 Live Map")

# rename for streamlit map
map_df = df.rename(columns={"lat": "latitude", "lon": "longitude"})

st.map(map_df)

# ==============================
# INCIDENT TABLE
# ==============================
st.subheader("📊 Incidents")

st.dataframe(df, use_container_width=True)

# ==============================
# INCIDENT DETAILS
# ==============================
st.subheader("🧠 Incident Details")

st.write(f"**ID:** {selected_row['incident_id']}")
st.write(f"**Region:** {selected_row['region']}")
st.write(f"**Severity:** {selected_row['severity']}")
st.write(f"**Risk Score:** {selected_row['risk_score']}")

# ==============================
# LIVE ALERT FEED
# ==============================
st.subheader("📡 Live Alerts")

if "alerts" not in st.session_state:
    st.session_state.alerts = []

def generate_alert():
    return {
        "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "alert": random.choice([
            "Phishing Campaign",
            "Credential Stuffing",
            "Malware Beacon",
            "Data Exfiltration"
        ]),
        "severity": random.choice(["Low", "Medium", "High", "Critical"])
    }

if st.button("Generate Alert"):
    st.session_state.alerts.insert(0, generate_alert())

for alert in st.session_state.alerts[:5]:
    st.write(f"{alert['time']} | {alert['alert']} | {alert['severity']}")

# ==============================
# SIMPLE GRAPH (SAFE VERSION)
# ==============================
st.subheader("🧬 Relationship Graph (Safe Mode)")

st.write("Incident → Actor → IOC")

for _, row in df.iterrows():
    st.write(f"{row['incident_id']} → Actor_{row['region']} → IOC_{row['region']}")
