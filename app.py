import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🔥 MAP DEFINITIVE FIX")

# HARD-CODED DATA (no ambiguity)
df = pd.DataFrame({
    "incident": ["London", "New York"],
    "lat": [51.5074, 40.7128],
    "lon": [-0.1278, -74.0060]
})

# FORCE TYPES
df["lat"] = df["lat"].astype(float)
df["lon"] = df["lon"].astype(float)

st.write("DATA:")
st.write(df)

# 🔥 PLOTLY MAP (THIS WILL WORK)
fig = px.scatter_mapbox(
    df,
    lat="lat",
    lon="lon",
    hover_name="incident",
    zoom=1,
    height=500
)

fig.update_layout(mapbox_style="open-street-map")

st.plotly_chart(fig, use_container_width=True)
