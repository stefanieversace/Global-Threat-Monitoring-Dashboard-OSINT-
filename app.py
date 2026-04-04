import streamlit as st
import pandas as pd

st.title("MAP FIX TEST")

df = pd.DataFrame({
    "lat": [51.5074, 40.7128],
    "lon": [-0.1278, -74.0060]
})

# 🔥 FORCE CORRECT FORMAT
map_df = pd.DataFrame({
    "latitude": pd.to_numeric(df["lat"], errors="coerce"),
    "longitude": pd.to_numeric(df["lon"], errors="coerce"),
})

st.write(map_df.dtypes)
st.write(map_df)

st.map(map_df)
