st.subheader("🌍 Live Map")

map_df = df.copy()

# 🔥 FORCE CORRECT TYPES
map_df["latitude"] = pd.to_numeric(map_df["lat"], errors="coerce")
map_df["longitude"] = pd.to_numeric(map_df["lon"], errors="coerce")

# 🔥 DEBUG (leave this in for now)
st.write("DATA TYPES:")
st.write(map_df.dtypes)

st.write("MAP DATA:")
st.write(map_df[["latitude", "longitude"]])

# 🔥 ONLY pass clean columns
st.map(map_df[["latitude", "longitude"]])
