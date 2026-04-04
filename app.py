import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🌍 Threat Intelligence Map")

df = pd.DataFrame({
    "incident": ["London", "New York", "Sydney", "Berlin"],
    "lat": [51.5074, 40.7128, -33.8688, 52.52],
    "lon": [-0.1278, -74.0060, 151.2093, 13.405],
    "severity": ["High", "Critical", "Medium", "Low"],
    "risk": [80, 95, 60, 40]
})

# 🎯 Size + color logic
fig = px.scatter_mapbox(
    df,
    lat="lat",
    lon="lon",
    size="risk",
    color="severity",
    hover_name="incident",
    zoom=1.2,
    height=600,
    color_discrete_map={
        "Critical": "#ff4d6d",
        "High": "#ff8c42",
        "Medium": "#ffd166",
        "Low": "#06d6a0"
    }
)

# 🖤 DARK PROFESSIONAL STYLE
fig.update_layout(
    mapbox_style="carto-darkmatter",
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="#0b0f14",
    plot_bgcolor="#0b0f14",
)

# ✨ Glow effect (soft halo)
fig.update_traces(
    marker=dict(
        opacity=0.9,
        sizemode="area",
        sizeref=2.*max(df["risk"])/(40.**2),
        line=dict(width=1, color="white")
    )
)

st.plotly_chart(fig, use_container_width=True)
