import streamlit as st
import folium
from streamlit.components.v1 import html
from scripts.threat_monitor import generate_brief

st.set_page_config(page_title="OSINT Threat Monitor", layout="wide")

st.title("🌍 Global OSINT Threat Monitor")
st.markdown("Real-time monitoring of global security threats using open-source intelligence.")

if st.button("Generate Intelligence Brief"):
    try:
        brief, mapped_events, unmapped_articles = generate_brief()

        st.subheader("Daily Intelligence Brief")
        st.text_area("Brief Output", brief, height=500)

        st.subheader("🌍 Dynamic Global Threat Map")
        threat_map = folium.Map(location=[20, 0], zoom_start=2)

        if mapped_events:
            for event in mapped_events:
                popup_text = (
                    f"<b>{event['title']}</b><br>"
                    f"Location: {event['location']}<br>"
                    f"Risk: {event['risk']}<br>"
                    f"Source: {event['source']}"
                )

                if event["risk"] == "HIGH":
                    icon_colour = "red"
                elif event["risk"] == "MEDIUM":
                    icon_colour = "orange"
                else:
                    icon_colour = "green"

                folium.Marker(
                    location=[event["lat"], event["lon"]],
                    popup=folium.Popup(popup_text, max_width=300),
                    icon=folium.Icon(color=icon_colour)
                ).add_to(threat_map)

            html(threat_map._repr_html_(), height=500)
        else:
            st.warning("No article locations could be mapped from the current results.")

        if unmapped_articles:
            st.subheader("Unmapped Articles")
            for article in unmapped_articles:
                st.write(
                    f"**{article['title']}** | Source: {article['source']} | "
                    f"Risk: {article['risk']} | Detected location: {article['detected_location']}"
                )

    except Exception as e:
        st.error(f"Error: {e}")
