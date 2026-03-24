import folium
from streamlit.components.v1 import html
import streamlit as st
from scripts.threat_monitor import generate_brief

st.set_page_config(page_title="OSINT Threat Monitor", layout="wide")

st.title("🌍 Global OSINT Threat Monitor")

st.markdown("Real-time monitoring of global security threats using open-source intelligence.")

if st.button("Generate Intelligence Brief"):
    brief = generate_brief()
    st.text_area("Daily Intelligence Brief", brief, height=500)
st.subheader("🌍 Global Threat Map")

def show_map():
    # world map
    m = folium.Map(location=[20, 0], zoom_start=2)

    # sample threat locations (you can improve later)
    folium.Marker([48.8566, 2.3522], popup="Protest Activity - Paris").add_to(m)
    folium.Marker([40.7128, -74.0060], popup="Security Alert - New York").add_to(m)
    folium.Marker([33.3152, 44.3661], popup="Conflict Zone - Baghdad").add_to(m)

    return m

map_obj = show_map()
html(map_obj._repr_html_(), height=500)
