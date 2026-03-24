import streamlit as st
import folium
import pandas as pd
from streamlit.components.v1 import html
from scripts.threat_monitor import generate_brief, load_history

st.set_page_config(page_title="OSINT Threat Monitor", layout="wide")

st.title("Global OSINT Threat Monitor")
st.caption(
    "Open-source intelligence dashboard for real-time threat monitoring, "
    "risk assessment, and geospatial visualisation."
)

with st.sidebar:
    st.header("Dashboard Controls")

    selected_risks = st.multiselect(
        "Filter by risk level",
        ["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM", "LOW"],
    )

    watchlist_input = st.text_input(
        "Watchlist locations/keywords",
        placeholder="e.g. New York, London, protest, Israel",
    )

    max_articles = st.slider("Number of articles to analyse", 5, 20, 10)

watchlist_terms = [term.strip() for term in watchlist_input.split(",") if term.strip()]

if st.button("Generate Intelligence Brief"):
    try:
        brief, mapped_events, unmapped_articles, summary = generate_brief(
            max_articles=max_articles,
            watchlist_terms=watchlist_terms,
        )

        st.write(f"Mapped events found: {len(mapped_events)}")
        st.write(f"Unmapped articles found: {len(unmapped_articles)}")

        if summary["high_count"] >= 3:
            st.error("Alert: Multiple high-risk incidents identified in current reporting.")
        elif summary["watchlist_matches"] > 0:
            st.warning("Alert: One or more watchlist terms matched current reporting.")
        else:
            st.success("No major alert threshold triggered in current reporting.")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("High Risk", summary["high_count"])
        col2.metric("Medium Risk", summary["medium_count"])
        col3.metric("Low Risk", summary["low_count"])
        col4.metric("Watchlist Matches", summary["watchlist_matches"])

        st.subheader("Top 3 Key Judgements")
        for idx, judgement in enumerate(summary["key_judgements"], start=1):
            st.write(f"{idx}. {judgement}")

        st.subheader("Regional Breakdown")
        region_df = pd.DataFrame(
            [{"Region": region, "Incidents": count} for region, count in summary["region_counts"].items()]
        )
        if not region_df.empty:
            st.dataframe(region_df, use_container_width=True)
        else:
            st.info("No regional breakdown available from current results.")

        st.subheader("Daily Intelligence Brief")
        st.text_area("Brief Output", brief, height=450)

        st.download_button(
            label="Download Intelligence Brief",
            data=brief,
            file_name="daily_intelligence_brief.txt",
            mime="text/plain",
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
                f"Region: {event['region']}<br>"
                f"Risk: {event['risk']}<br>"
                f"Score: {event['score']}<br>"
                f"Confidence: {event['confidence']}<br>"
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
                popup=folium.Popup(popup_text, max_width=320),
                icon=folium.Icon(color=icon_colour),
            ).add_to(threat_map)

        if filtered_events:
            html(threat_map._repr_html_(), height=500)
        else:
            st.warning("No mapped incidents match the selected filters.")

        st.subheader("Mapped Incidents")
        if filtered_events:
            mapped_df = pd.DataFrame(
                [
                    {
                        "Title": event["title"],
                        "Location": event["location"],
                        "Region": event["region"],
                        "Risk": event["risk"],
                        "Score": event["score"],
                        "Confidence": event["confidence"],
                        "Source": event["source"],
                        "Published": event["published_at"],
                        "Watchlist Match": event["watchlist_match"],
                        "URL": event["url"],
                    }
                    for event in filtered_events
                ]
            )
            st.dataframe(mapped_df, use_container_width=True)
        else:
            st.info("No mapped incidents to display.")

        st.subheader("Unmapped Articles")
        if unmapped_articles:
            unmapped_df = pd.DataFrame(
                [
                    {
                        "Title": article["title"],
                        "Source": article["source"],
                        "Risk": article["risk"],
                        "Score": article["score"],
                        "Confidence": article["confidence"],
                        "Detected Location": article["detected_location"],
                        "Published": article["published_at"],
                        "Watchlist Match": article["watchlist_match"],
                        "URL": article["url"],
                    }
                    for article in unmapped_articles
                    if article["risk"] in selected_risks
                ]
            )

            if not unmapped_df.empty:
                st.dataframe(unmapped_df, use_container_width=True)
            else:
                st.info("No unmapped articles match the selected filters.")
        else:
            st.info("No unmapped articles.")

        st.subheader("Threat Trends")
        history_df = load_history()
        if not history_df.empty:
            trend_df = (
                history_df.groupby("date")[["high_count", "medium_count", "low_count"]]
                .max()
                .reset_index()
            )
            trend_df = trend_df.set_index("date")
            st.line_chart(trend_df)
        else:
            st.info("No history available yet. Generate more briefs to build a trend line.")

    except Exception as e:
        st.error(f"Error: {e}")
