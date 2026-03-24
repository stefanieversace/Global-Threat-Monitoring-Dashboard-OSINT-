import streamlit as st
import folium
from streamlit.components.v1 import html
from scripts.threat_monitor import generate_brief

st.set_page_config(page_title="OSINT Threat Monitor", layout="wide")

st.title("Global OSINT Threat Monitor")
st.caption("Open-source intelligence dashboard for real-time threat monitoring, risk assessment, and geospatial visualisation.")

selected_risks = st.multiselect(
    "Filter by risk level",
    ["HIGH", "MEDIUM", "LOW"],
    default=["HIGH", "MEDIUM", "LOW"]
)

if st.button("Generate Intelligence Brief"):
    try:
        brief, mapped_events, unmapped_articles = generate_brief()

        high_count = sum(1 for event in mapped_events if event["risk"] == "HIGH")
        medium_count = sum(1 for event in mapped_events if event["risk"] == "MEDIUM")
        low_count = sum(1 for event in mapped_events if event["risk"] == "LOW")

        col1, col2, col3 = st.columns(3)
        col1.metric("High Risk", high_count)
        col2.metric("Medium Risk", medium_count)
        col3.metric("Low Risk", low_count)

        st.subheader("Daily Intelligence Brief")
        st.text_area("Brief Output", brief, height=500)

        st.download_button(
            label="Download Intelligence Brief",
            data=brief,
            file_name="daily_intelligence_brief.txt",
            mime="text/plain"
        )

        st.subheader("Dynamic Global Threat Map")
        threat_map = folium.Map(location=[20, 0], zoom_start=2)

        filtered_events = []
        for event in mapped_events:
            if event["risk"] not in selected_risks:
                continue
            filtered_events.append(event)

            popup_text = (
                f"<b>{event['title']}</b><br>"
                f"Location: {event['location']}<br>"
                f"Risk: {event['risk']}<br>"
                f"Source: {event['source']}<br>"
                f"Published: {event['published_at']}<br>"
                f"<a href='{event['url']}' target='_blank'>Open article</a>"
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

        if filtered_events:
            html(threat_map._repr_html_(), height=500)
        else:
            st.warning("No mapped incidents match the selected risk filter.")

        if filtered_events:
            st.subheader("Mapped Incidents")
            st.dataframe([
                {
                    "Title": event["title"],
                    "Location": event["location"],
                    "Risk": event["risk"],
                    "Source": event["source"],
                    "Published": event["published_at"],
                    "URL": event["url"]
                }
                for event in filtered_events
            ])

        if unmapped_articles:
            st.subheader("Unmapped Articles")
            st.dataframe([
                {
                    "Title": article["title"],
                    "Source": article["source"],
                    "Risk": article["risk"],
                    "Detected Location": article["detected_location"],
                    "Published": article["published_at"],
                    "URL": article["url"]
                }
                for article in unmapped_articles
            ])

    except Exception as e:
        st.error(f"Error: {e}")
