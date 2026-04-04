import streamlit as st
import folium
import pandas as pd
from folium.plugins import MarkerCluster
from streamlit.components.v1 import html
from scripts.threat_monitor import generate_brief, load_history

st.set_page_config(
    page_title="Global OSINT Threat Monitor",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main {
            padding-top: 1.2rem;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        .elite-banner {
            background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
            color: white;
            padding: 1.25rem 1.5rem;
            border-radius: 14px;
            margin-bottom: 1rem;
        }
        .elite-banner h1 {
            margin: 0;
            font-size: 2rem;
        }
        .elite-banner p {
            margin: 0.35rem 0 0 0;
            color: #cbd5e1;
            font-size: 0.98rem;
        }
        .section-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 1rem 1rem 0.5rem 1rem;
            margin-bottom: 1rem;
        }
        .summary-box {
            background: #f8fafc;
            border-left: 5px solid #0f172a;
            padding: 1rem 1rem 0.75rem 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        .small-label {
            font-size: 0.8rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="elite-banner">
        <h1>Global OSINT Threat Monitor</h1>
        <p>
            Intelligence dashboard for real-time threat monitoring, risk assessment,
            analyst judgement, and geospatial visualisation.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Controls")

    selected_risks = st.multiselect(
        "Filter by risk level",
        ["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM", "LOW"],
    )

    watchlist_input = st.text_input(
        "Watchlist terms",
        placeholder="e.g. New York, London, protest, Israel",
    )

    max_articles = st.slider("Articles to analyse", 5, 20, 10)

    st.markdown("---")
    st.caption("Tip: clear the watchlist if you want the fullest map view.")

watchlist_terms = [term.strip() for term in watchlist_input.split(",") if term.strip()]

if st.button("Generate Intelligence Brief", use_container_width=True):
    try:
        brief, mapped_events, unmapped_articles, summary = generate_brief(
            max_articles=max_articles,
            watchlist_terms=watchlist_terms,
        )

        high_count = summary["high_count"]
        medium_count = summary["medium_count"]
        low_count = summary["low_count"]
        watchlist_matches = summary["watchlist_matches"]

        if high_count >= 3:
            st.error("Elevated alert posture: multiple high-risk incidents identified in current reporting.")
        elif watchlist_matches > 0:
            st.warning("Watchlist alert: one or more watchlist terms matched current reporting.")
        else:
            st.success("No major alert threshold triggered in current reporting.")

        top_region = "N/A"
        if summary["region_counts"]:
            top_region = max(summary["region_counts"], key=summary["region_counts"].get)

        total_events = len(mapped_events) + len(unmapped_articles)

        metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
        metric_col1.metric("High Risk", high_count)
        metric_col2.metric("Medium Risk", medium_count)
        metric_col3.metric("Low Risk", low_count)
        metric_col4.metric("Watchlist Matches", watchlist_matches)
        metric_col5.metric("Top Region", top_region)

        st.markdown(
            """
            <div class="summary-box">
                <div class="small-label">Executive Summary</div>
                <p style="margin-top:0.6rem;">
                    This dashboard reviews current open-source reporting, scores incident severity,
                    extracts locations, and produces intelligence-style outputs to support
                    situational awareness and monitoring decisions.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Top 3 Key Judgements")
        for idx, judgement in enumerate(summary["key_judgements"], start=1):
            st.write(f"{idx}. {judgement}")

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Map View", "Executive Brief", "Incident Tables", "Trends", "Regional Analysis"]
        )

        with tab1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Dynamic Global Threat Map")

            threat_map = folium.Map(location=[20, 0], zoom_start=2)
            marker_cluster = MarkerCluster().add_to(threat_map)

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
                ).add_to(marker_cluster)

            if filtered_events:
                html(threat_map._repr_html_(), height=560)
                st.caption(f"Showing {len(filtered_events)} mapped incidents from {total_events} analysed articles.")
            else:
                st.warning("No mapped incidents match the selected filters.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Executive Brief")

            st.download_button(
                label="Download Intelligence Brief",
                data=brief,
                file_name="daily_intelligence_brief.txt",
                mime="text/plain",
                use_container_width=False,
            )

            st.text_area("Brief Output", brief, height=520)
            st.markdown("</div>", unsafe_allow_html=True)

        with tab3:
            mapped_tab, unmapped_tab = st.tabs(["Mapped Incidents", "Unmapped Articles"])

            with mapped_tab:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
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
                    st.dataframe(mapped_df, use_container_width=True, height=420)
                else:
                    st.info("No mapped incidents to display.")
                st.markdown("</div>", unsafe_allow_html=True)

            with unmapped_tab:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                filtered_unmapped = [
                    article for article in unmapped_articles
                    if article["risk"] in selected_risks
                ]

                if filtered_unmapped:
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
                            for article in filtered_unmapped
                        ]
                    )
                    st.dataframe(unmapped_df, use_container_width=True, height=420)
                else:
                    st.info("No unmapped articles match the selected filters.")
                st.markdown("</div>", unsafe_allow_html=True)

        with tab4:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Threat Trends")

            history_df = load_history()
            if not history_df.empty:
                trend_df = (
                    history_df.groupby("date")[["high_count", "medium_count", "low_count"]]
                    .max()
                    .reset_index()
                )
                trend_df = trend_df.set_index("date")
                st.line_chart(trend_df, height=380)
                st.dataframe(history_df, use_container_width=True, height=220)
            else:
                st.info("No history available yet. Generate more briefs to build a trend line.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab5:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Regional Analysis")

            region_df = pd.DataFrame(
                [{"Region": region, "Incidents": count} for region, count in summary["region_counts"].items()]
            )

            if not region_df.empty:
                region_df = region_df.sort_values("Incidents", ascending=False)
                st.bar_chart(region_df.set_index("Region"), height=360)
                st.dataframe(region_df, use_container_width=True, height=220)
            else:
                st.info("No regional breakdown available from current results.")
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("Use the controls in the sidebar, then click 'Generate Intelligence Brief' to load the dashboard.")

import streamlit as st

st.title("🌍 Global Threat Intelligence Dashboard")

# 🚨 NEW SECTION — THIS IS THE UPGRADE
st.header("🧾 Daily Intelligence Brief")

st.subheader("🔴 Key Developments")
st.markdown("""
- Civil unrest reported in Paris affecting transport hubs  
- Cyber phishing campaign targeting financial institutions  
""")

st.subheader("⚠️ Risk Assessment")
st.markdown("""
- Operational Risk: **High**  
- Geographic Impact: **Europe**  
- Affected Sectors: **Media, Finance**  
""")

st.subheader("🧠 Analyst Insight")
st.markdown("""
Current developments may disrupt large-scale events and financial operations. 
Monitoring escalation patterns and response measures is recommended.
""")

st.divider()
