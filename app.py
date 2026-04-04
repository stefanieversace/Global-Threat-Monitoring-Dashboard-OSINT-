import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("TEST MAP DEBUG")

# Simple data
df = pd.DataFrame({
    "latitude": [51.5074, 40.7128],
    "longitude": [-0.1278, -74.0060]
})

st.write("DATA:")
st.write(df)

st.write("MAP BELOW:")

# Force render
st.map(df)

st.write("DONE")
