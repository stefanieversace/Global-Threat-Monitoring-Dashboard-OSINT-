import re
from collections import Counter
from typing import Dict, List, Tuple, Any

import requests
import pandas as pd
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit.components.v1 import html

from scripts.threat_monitor import generate_brief, load_history

# Optional imports with graceful fallback
try:
    import spacy
except Exception:
    spacy = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Media & Events Intelligence Platform",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# STYLING — PALANTIR / BLOOMBERG-STYLE UI
# =========================================================
st.markdown(
    """
    <style>
        .stApp {
            background-color: #0b0f14;
            color: #e6edf3;
        }

        .main {
            padding-top: 0.6rem;
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }

        .elite-banner {
            background: linear-gradient(90deg, #111827 0%, #1f2937 100%);
            border: 1px solid #374151;
            color: #e5e7eb;
            padding: 1.25rem 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
        }

        .elite-banner h1 {
            margin: 0;
            font-size: 2rem;
            letter-spacing: 0.02em;
        }

        .elite-banner p {
            margin: 0.4rem 0 0 0;
            color: #9ca3af;
            font-size: 0.96rem;
        }

        .section-card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 1rem 1rem 0.75rem 1rem;
            margin-bottom: 1rem;
        }

        .summary-box {
            background: #111827;
            border-left: 4px solid #22c55e;
            padding: 1rem 1rem 0.75rem 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }

        .ops-box {
            background: #111827;
            border-left: 4px solid #f59e0b;
            padding: 1rem 1rem 0.75rem 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }

        .small-label {
            font-size: 0.75rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        section[data-testid="stSidebar"] {
            background-color: #020617;
            border-right: 1px solid #111827;
        }

        [data-testid="stMetric"] {
            background-color: #111827;
            border: 1px solid #1f2937;
            padding: 10px;
            border-radius: 10px;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid #1f2937;
            border-radius: 10px;
            overflow: hidden;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: #111827;
            border-radius: 8px;
            padding-left: 14px;
            padding-right: 14px;
            border: 1px solid #1f2937;
        }

        .news-card {
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 10px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.8rem;
        }

        .news-title {
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 0.35rem;
        }

        .news-meta {
            color: #94a3b8;
            font-size: 0.82rem;
            margin-bottom: 0.45rem;
        }

        .entity-chip {
            display: inline-block;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            margin: 0.15rem 0.2rem 0.15rem 0;
            font-size: 0.78rem;
            border: 1px solid #334155;
            background: #0f172a;
            color: #e2e8f0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# HEADER
# =========================================================
st.markdown(
    """
    <div class="elite-banner">
        <h1>Media &amp; Events Intelligence Platform</h1>
        <p>
            Operational threat monitoring for venues, productions, talent, brand reputation,
            digital operations, and public-facing experiences.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Live OSINT Monitoring • Risk Prioritisation • Intelligence Analysis • IOC Extraction • Entity Tracking")

st.markdown("## 🧾 Intelligence Snapshot")

st.markdown(
    """
    <div class="summary-box">
        <div class="small-label">Operational Context</div>
        <p style="margin-top:0.6rem;">
            This platform aggregates current open-source reporting to identify, prioritise,
            and assess emerging threats. Outputs are designed to support rapid decision-making
            across security, intelligence, venue operations, production environments,
            executive protection, and reputational monitoring.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 🎯 What this platform provides")
snapshot_col1, snapshot_col2, snapshot_col3 = st.columns(3)

with snapshot_col1:
    st.markdown(
        """
        **Threat Detection**
        - Identifies emerging incidents
        - Extracts locations and named entities
        - Surfaces watchlist-related reporting
        """
    )

with snapshot_col2:
    st.markdown(
        """
        **Risk Assessment**
        - Scores severity and confidence
        - Maps incidents to MITRE ATT&CK
        - Classifies threats by category
        """
    )

with snapshot_col3:
    st.markdown(
        """
        **Decision Support**
        - Produces executive-style briefs
        - Triggers SOC-style alerts
        - Highlights operational business impacts
        """
    )

st.divider()

# =========================================================
# CONFIG / SECRETS / CLIENTS
# =========================================================
NEWS_API_KEY = st.secrets.get("NEWS_API_KEY", None)
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)

openai_client = None
if OPENAI_API_KEY and OpenAI is not None:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        openai_client = None


# =========================================================
# NLP LOADER
# =========================================================
@st.cache_resource
def load_nlp():
    if spacy is None:
        return None
    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        return None


nlp = load_nlp()


# =========================================================
# CONSTANTS
# =========================================================
MITRE_MAPPING = {
    "phishing": {"technique": "T1566", "name": "Phishing"},
    "credential": {"technique": "T1003", "name": "Credential Dumping"},
    "malware": {"technique": "T1204", "name": "User Execution"},
    "ransomware": {"technique": "T1486", "name": "Data Encrypted for Impact"},
    "ddos": {"technique": "T1499", "name": "Endpoint Denial of Service"},
    "exploit": {"technique": "T1203", "name": "Exploitation for Client Execution"},
    "payload": {"technique": "T1105", "name": "Ingress Tool Transfer"},
    "persistence": {"technique": "T1547", "name": "Boot or Logon Autostart Execution"},
    "exfiltration": {"technique": "T1041", "name": "Exfiltration Over C2 Channel"},
    "powershell": {"technique": "T1059.001", "name": "PowerShell"},
}

IOC_PATTERNS = {
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "domain": r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b",
    "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    "url": r"https?://[^\s]+",
    "sha256": r"\b[a-fA-F0-9]{64}\b",
    "md5": r"\b[a-fA-F0-9]{32}\b",
    "cve": r"\bCVE-\d{4}-\d{4,7}\b",
}

DEFAULT_NEWS_QUERY = (
    '("cyber attack" OR protest OR conflict OR unrest OR ransomware OR breach OR explosion OR disruption OR venue OR concert OR stadium)'
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def safe_get(item: Dict[str, Any], key: str, default: Any = "") -> Any:
    return item.get(key, default) if isinstance(item, dict) else default


def normalise_datetime(value: Any) -> str:
    if not value:
        return "N/A"
    return str(value)


def map_to_mitre(text: str) -> str:
    text_lower = (text or "").lower()
    for keyword, value in MITRE_MAPPING.items():
        if keyword in text_lower:
            return f"{value['technique']} - {value['name']}"
    return "N/A"


def classify_threat_fallback(text: str) -> str:
    text_lower = (text or "").lower()

    cyber_terms = [
        "cyber", "phishing", "ransomware", "malware", "breach", "credential",
        "ddos", "exploit", "payload", "endpoint", "cve", "infostealer"
    ]
    physical_terms = [
        "shooting", "explosion", "fire", "stampede", "crowd", "venue",
        "stadium", "concert", "attack", "knife", "security incident"
    ]
    political_terms = [
        "protest", "election", "government", "minister", "sanction",
        "civil unrest", "riot", "political", "parliament", "demonstration"
    ]
    environmental_terms = [
        "storm", "flood", "earthquake", "wildfire", "heatwave", "weather",
        "evacuation", "hurricane", "cyclone"
    ]

    if any(term in text_lower for term in cyber_terms):
        return "Cyber"
    if any(term in text_lower for term in physical_terms):
        return "Physical"
    if any(term in text_lower for term in political_terms):
        return "Political"
    if any(term in text_lower for term in environmental_terms):
        return "Environmental"
    return "General"


def classify_threat_ai(text: str) -> str:
    if not openai_client:
        return classify_threat_fallback(text)

    prompt = f"""
Classify this threat into exactly one category:

- Cyber
- Physical
- Political
- Environmental
- General

Text:
{text}

Return only the category name.
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        result = response.choices[0].message.content.strip()
        allowed = {"Cyber", "Physical", "Political", "Environmental", "General"}
        return result if result in allowed else classify_threat_fallback(text)
    except Exception:
        return classify_threat_fallback(text)


def generate_ai_summary(articles: List[Dict[str, Any]]) -> str:
    if not articles:
        return (
            "### Key Developments\n"
            "- No significant live developments retrieved.\n\n"
            "### Risk Assessment\n"
            "- Overall Risk: Low\n"
            "- Rationale: No meaningful live reporting was available for synthesis.\n\n"
            "### Analyst Insight\n"
            "Maintain standard monitoring posture and continue scheduled review cycles."
        )

    if not openai_client:
        headlines = []
        for article in articles[:5]:
            title = safe_get(article, "title", "Untitled")
            source = safe_get(safe_get(article, "source", {}), "name", "Unknown source")
            headlines.append(f"- {title} ({source})")

        return (
            "### Key Developments\n"
            + "\n".join(headlines[:3])
            + "\n\n### Risk Assessment\n"
            "- Overall Risk: Medium\n"
            "- Rationale: Current live reporting indicates active developments requiring continued monitoring.\n\n"
            "### Analyst Insight\n"
            "Recent reporting suggests a mixed risk environment spanning operational, reputational, and digital concerns. "
            "Analysts should monitor geographic clustering, watchlist matches, and business impact indicators."
        )

    text_blob = "\n".join(
        [
            f"Title: {safe_get(a, 'title', '')}\n"
            f"Description: {safe_get(a, 'description', '')}\n"
            f"Source: {safe_get(safe_get(a, 'source', {}), 'name', '')}\n"
            for a in articles[:8]
        ]
    )

    prompt = f"""
You are an intelligence analyst supporting media, venue, event, and enterprise security operations.

Based on the reporting below, produce:

1. Key Developments (3 bullet points)
2. Risk Assessment (overall risk + short reason)
3. Analyst Insight (2-3 sentences, concise and professional)

Focus on operationally relevant impacts such as:
- venue disruption
- production disruption
- reputational risk
- executive or talent exposure
- digital operations

Reporting:
{text_blob}
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return (
            "### Key Developments\n"
            "- Live reporting was retrieved but the AI summary service was unavailable.\n\n"
            "### Risk Assessment\n"
            "- Overall Risk: Medium\n"
            "- Rationale: Live items are present and should be manually reviewed.\n\n"
            "### Analyst Insight\n"
            "Continue monitoring the latest reporting and review the live feed directly for time-sensitive developments."
        )


@st.cache_data(ttl=900)
def fetch_live_news(query: str = DEFAULT_NEWS_QUERY, page_size: int = 10) -> List[Dict[str, Any]]:
    if not NEWS_API_KEY:
        return []

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])
    except Exception:
        return []


def extract_iocs(text: str) -> Dict[str, List[str]]:
    if not text:
        return {k: [] for k in IOC_PATTERNS}

    found = {}
    for ioc_type, pattern in IOC_PATTERNS.items():
        matches = re.findall(pattern, text)
        cleaned = sorted(set(m.strip(".,);]}>\"'") for m in matches))
        found[ioc_type] = cleaned
    return found


def extract_entities(text: str) -> Dict[str, List[str]]:
    if not text:
        return {"people": [], "orgs": [], "locations": []}

    # spaCy path
    if nlp is not None:
        try:
            doc = nlp(text)
            people = sorted(set(ent.text for ent in doc.ents if ent.label_ == "PERSON"))
            orgs = sorted(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))
            locations = sorted(
                set(ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC", "FAC"])
            )
            return {"people": people, "orgs": orgs, "locations": locations}
        except Exception:
            pass

    # Basic fallback
    capitalised = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
    unique = sorted(set(capitalised))
    return {"people": unique[:5], "orgs": [], "locations": []}


def assign_business_impact(text: str) -> List[str]:
    text_lower = (text or "").lower()
    impacts = []

    if any(word in text_lower for word in ["arena", "stadium", "venue", "concert", "theatre", "crowd", "festival", "event"]):
        impacts.append("Venue Operations")

    if any(word in text_lower for word in ["broadcast", "studio", "filming", "production", "set", "tv", "streaming"]):
        impacts.append("Production Operations")

    if any(word in text_lower for word in ["executive", "celebrity", "artist", "talent", "vip", "presenter", "performer"]):
        impacts.append("Talent / Executive Protection")

    if any(word in text_lower for word in ["boycott", "controversy", "backlash", "viral", "brand", "reputation", "criticism"]):
        impacts.append("Reputational Risk")

    if any(word in text_lower for word in ["cyber", "phishing", "ransomware", "breach", "malware", "ddos", "credential"]):
        impacts.append("Digital Operations")

    return impacts or ["General Monitoring"]


def evaluate_alerts(brief: str, mapped_events: List[Dict[str, Any]], watchlist_matches: int) -> List[Dict[str, str]]:
    alerts = []

    high_risk_events = [e for e in mapped_events if safe_get(e, "risk") == "HIGH"]
    venue_impacts = [e for e in mapped_events if "Venue Operations" in safe_get(e, "business_impact", [])]
    exec_impacts = [e for e in mapped_events if "Talent / Executive Protection" in safe_get(e, "business_impact", [])]
    reputational_impacts = [e for e in mapped_events if "Reputational Risk" in safe_get(e, "business_impact", [])]
    cyber_impacts = [e for e in mapped_events if safe_get(e, "category") == "Cyber"]

    if len(high_risk_events) >= 3:
        alerts.append({"level": "CRITICAL", "message": "Multiple high-risk incidents detected across current reporting."})

    if watchlist_matches > 0:
        alerts.append({"level": "WARNING", "message": "Watchlist terms detected in current reporting."})

    if venue_impacts:
        alerts.append({"level": "WARNING", "message": "Potential venue or event disruption identified."})

    if exec_impacts:
        alerts.append({"level": "WARNING", "message": "High-profile individual or talent-related mention requires review."})

    if reputational_impacts:
        alerts.append({"level": "INFO", "message": "Reputationally sensitive reporting present in the current cycle."})

    if cyber_impacts or ("cyber" in (brief or "").lower()):
        alerts.append({"level": "INFO", "message": "Cyber-related activity detected in current reporting."})

    return alerts


def build_ioc_table(items: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for item in items:
        title = safe_get(item, "title", "Untitled")
        for ioc_type, values in safe_get(item, "iocs", {}).items():
            for value in values:
                rows.append(
                    {
                        "Title": title,
                        "IOC Type": ioc_type.upper(),
                        "Indicator": value,
                        "Risk": safe_get(item, "risk", "N/A"),
                        "Category": safe_get(item, "category", "N/A"),
                        "Source": safe_get(item, "source", "N/A"),
                        "Published": safe_get(item, "published_at", "N/A"),
                    }
                )
    return pd.DataFrame(rows)


def build_entity_summary(items: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    people_counter = Counter()
    org_counter = Counter()
    location_counter = Counter()

    for item in items:
        entities = safe_get(item, "entities", {})
        people_counter.update(entities.get("people", []))
        org_counter.update(entities.get("orgs", []))
        location_counter.update(entities.get("locations", []))

    people_df = pd.DataFrame(people_counter.items(), columns=["Entity", "Mentions"]).sort_values("Mentions", ascending=False) if people_counter else pd.DataFrame(columns=["Entity", "Mentions"])
    org_df = pd.DataFrame(org_counter.items(), columns=["Entity", "Mentions"]).sort_values("Mentions", ascending=False) if org_counter else pd.DataFrame(columns=["Entity", "Mentions"])
    location_df = pd.DataFrame(location_counter.items(), columns=["Entity", "Mentions"]).sort_values("Mentions", ascending=False) if location_counter else pd.DataFrame(columns=["Entity", "Mentions"])

    return people_df, org_df, location_df


def render_alerts(alerts: List[Dict[str, str]]) -> None:
    st.header("🚨 Active Alerts")
    if alerts:
        for alert in alerts:
            level = alert.get("level", "INFO")
            message = alert.get("message", "Alert triggered.")
            if level == "CRITICAL":
                st.error(f"🔴 {message}")
            elif level == "WARNING":
                st.warning(f"🟠 {message}")
            else:
                st.info(f"🔵 {message}")
    else:
        st.success("No active alerts in the current monitoring cycle.")


def add_enrichment_to_events(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched_items = []

    for item in items:
        enriched = dict(item)

        combined_text = " ".join(
            [
                str(safe_get(enriched, "title", "")),
                str(safe_get(enriched, "description", "")),
                str(safe_get(enriched, "source", "")),
                str(safe_get(enriched, "location", "")),
                str(safe_get(enriched, "detected_location", "")),
            ]
        ).strip()

        enriched["mitre"] = map_to_mitre(combined_text)
        enriched["category"] = classify_threat_ai(combined_text)
        enriched["iocs"] = extract_iocs(combined_text)
        enriched["entities"] = extract_entities(combined_text)
        enriched["business_impact"] = assign_business_impact(combined_text)

        enriched_items.append(enriched)

    return enriched_items


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("Controls")

    selected_risks = st.multiselect(
        "Filter by risk level",
        ["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM", "LOW"],
    )

    selected_categories = st.multiselect(
        "Threat category",
        ["Cyber", "Physical", "Political", "Environmental", "General"],
        default=["Cyber", "Physical", "Political", "Environmental", "General"],
    )

    watchlist_input = st.text_input(
        "Watchlist terms",
        placeholder="e.g. New York, London, protest, executive, venue",
    )

    max_articles = st.slider("Articles to analyse", 5, 30, 10)

    live_news_query = st.text_area(
        "Live news query",
        value=DEFAULT_NEWS_QUERY,
        height=110,
    )

    st.markdown("---")
    st.caption("Tip: clear the watchlist if you want the fullest map view.")

watchlist_terms = [term.strip() for term in watchlist_input.split(",") if term.strip()]


# =========================================================
# MAIN EXECUTION
# =========================================================
if st.button("Generate Intelligence Brief", use_container_width=True):
    try:
        # -------------------------------------------------
        # Core threat monitor pipeline
        # -------------------------------------------------
        brief, mapped_events, unmapped_articles, summary = generate_brief(
            max_articles=max_articles,
            watchlist_terms=watchlist_terms,
        )

        # -------------------------------------------------
        # Live news feed
        # -------------------------------------------------
        live_articles = fetch_live_news(query=live_news_query, page_size=max_articles)

        # -------------------------------------------------
        # Enrichment
        # -------------------------------------------------
        mapped_events = add_enrichment_to_events(mapped_events)
        unmapped_articles = add_enrichment_to_events(unmapped_articles)

        # -------------------------------------------------
        # AI summary
        # -------------------------------------------------
        ai_summary = generate_ai_summary(live_articles)

        # -------------------------------------------------
        # Summary values
        # -------------------------------------------------
        high_count = summary.get("high_count", 0)
        medium_count = summary.get("medium_count", 0)
        low_count = summary.get("low_count", 0)
        watchlist_matches = summary.get("watchlist_matches", 0)
        region_counts = summary.get("region_counts", {})
        key_judgements = summary.get("key_judgements", [])

        top_region = max(region_counts, key=region_counts.get) if region_counts else "N/A"
        total_events = len(mapped_events) + len(unmapped_articles)
        priority_score = len([e for e in mapped_events if e.get("risk") == "HIGH"]) * 10 + (watchlist_matches * 5)

        # -------------------------------------------------
        # Alerts
        # -------------------------------------------------
        alerts = evaluate_alerts(brief, mapped_events, watchlist_matches)

        # -------------------------------------------------
        # Alert posture summary
        # -------------------------------------------------
        if high_count >= 3:
            st.error("Elevated alert posture: multiple high-risk incidents identified in current reporting.")
        elif watchlist_matches > 0:
            st.warning("Watchlist alert: one or more watchlist terms matched current reporting.")
        else:
            st.success("No major alert threshold triggered in current reporting.")

        # -------------------------------------------------
        # Metrics
        # -------------------------------------------------
        metric_col1, metric_col2, metric_col3, metric_col4, metric_col5, metric_col6 = st.columns(6)
        metric_col1.metric("High Risk", high_count)
        metric_col2.metric("Medium Risk", medium_count)
        metric_col3.metric("Low Risk", low_count)
        metric_col4.metric("Watchlist Matches", watchlist_matches)
        metric_col5.metric("Top Region", top_region)
        metric_col6.metric("Threat Priority Score", priority_score)

        # -------------------------------------------------
        # Executive summary boxes
        # -------------------------------------------------
        st.markdown(
            """
            <div class="summary-box">
                <div class="small-label">Executive Summary</div>
                <p style="margin-top:0.6rem;">
                    This platform reviews current reporting, scores severity, extracts locations,
                    identifies entities, extracts indicators, classifies threats, and produces
                    intelligence-style outputs to support situational awareness and monitoring decisions.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="ops-box">
                <div class="small-label">Operations Desk Priority View</div>
                <p style="margin-top:0.6rem;">
                    Prioritises incidents that could affect venues, live events, productions,
                    corporate offices, brand reputation, digital operations, or high-profile personnel.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # -------------------------------------------------
        # Key judgements
        # -------------------------------------------------
        st.subheader("🧠 Key Intelligence Judgements")
        st.caption("Analyst-derived insights based on current reporting and risk scoring")

        if key_judgements:
            for idx, judgement in enumerate(key_judgements[:3], start=1):
                st.write(f"{idx}. {judgement}")
        else:
            st.info("No key judgements were returned for this cycle.")

        # -------------------------------------------------
        # Recommended actions
        # -------------------------------------------------
        st.subheader("📌 Recommended Actions")
        if high_count >= 3:
            st.markdown("- Increase monitoring and alert posture in high-risk regions.")
            st.markdown("- Review operational exposure in affected locations.")
            st.markdown("- Escalate relevant items to leadership or incident management workflows.")
        elif watchlist_matches > 0:
            st.markdown("- Monitor watchlist-related developments closely.")
            st.markdown("- Validate possible impact to assets, personnel, events, or reputation.")
        else:
            st.markdown("- Maintain standard monitoring posture.")
            st.markdown("- Continue scheduled review and watchlist enrichment.")

        # -------------------------------------------------
        # Active alerts
        # -------------------------------------------------
        render_alerts(alerts)

        # -------------------------------------------------
        # Filtering
        # -------------------------------------------------
        filtered_events = [
            event for event in mapped_events
            if event.get("risk") in selected_risks and event.get("category") in selected_categories
        ]

        filtered_unmapped = [
            article for article in unmapped_articles
            if article.get("risk") in selected_risks and article.get("category") in selected_categories
        ]

        # -------------------------------------------------
        # Tabs
        # -------------------------------------------------
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
            [
                "🌍 Operations Map",
                "🧾 Executive Brief",
                "🤖 AI Summary",
                "📊 Incident Data",
                "📈 Threat Trends",
                "🌐 Regional Analysis",
                "🧬 MITRE Mapping",
                "🔎 IOC Extraction",
                "👥 Entity Tracking",
            ]
        )

        # -------------------------------------------------
        # TAB 1 — MAP
        # -------------------------------------------------
        with tab1:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Dynamic Global Threat Map")

            threat_map = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
            marker_cluster = MarkerCluster().add_to(threat_map)

            for event in filtered_events:
                popup_text = (
                    f"<b>{event.get('title', 'Untitled')}</b><br>"
                    f"Location: {event.get('location', 'N/A')}<br>"
                    f"Region: {event.get('region', 'N/A')}<br>"
                    f"Risk: {event.get('risk', 'N/A')}<br>"
                    f"Score: {event.get('score', 'N/A')}<br>"
                    f"Confidence: {event.get('confidence', 'N/A')}<br>"
                    f"Category: {event.get('category', 'N/A')}<br>"
                    f"MITRE: {event.get('mitre', 'N/A')}<br>"
                    f"Business Impact: {', '.join(event.get('business_impact', []))}<br>"
                    f"Source: {event.get('source', 'N/A')}<br>"
                    f"Published: {event.get('published_at', 'N/A')}<br>"
                    f"<a href='{event.get('url', '#')}' target='_blank'>Open article</a>"
                )

                if event.get("risk") == "HIGH":
                    icon_colour = "red"
                elif event.get("risk") == "MEDIUM":
                    icon_colour = "orange"
                else:
                    icon_colour = "green"

                lat = event.get("lat")
                lon = event.get("lon")

                if lat is not None and lon is not None:
                    folium.Marker(
                        location=[lat, lon],
                        popup=folium.Popup(popup_text, max_width=360),
                        icon=folium.Icon(color=icon_colour),
                    ).add_to(marker_cluster)

            if filtered_events:
                html(threat_map._repr_html_(), height=580)
                st.caption(f"Showing {len(filtered_events)} mapped incidents from {total_events} analysed items.")
            else:
                st.warning("No mapped incidents match the selected filters.")
            st.markdown("</div>", unsafe_allow_html=True)

        # -------------------------------------------------
        # TAB 2 — EXECUTIVE BRIEF
        # -------------------------------------------------
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

        # -------------------------------------------------
        # TAB 3 — AI SUMMARY
        # -------------------------------------------------
        with tab3:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("🤖 AI Intelligence Summary")
            st.markdown(ai_summary)

            st.markdown("---")
            st.subheader("📰 Live OSINT Feed")

            if live_articles:
                for article in live_articles:
                    title = safe_get(article, "title", "Untitled")
                    description = safe_get(article, "description", "")
                    source_name = safe_get(safe_get(article, "source", {}), "name", "Unknown source")
                    published = normalise_datetime(safe_get(article, "publishedAt", "N/A"))
                    url = safe_get(article, "url", "#")

                    st.markdown(
                        f"""
                        <div class="news-card">
                            <div class="news-title">{title}</div>
                            <div class="news-meta">{source_name} • {published}</div>
                            <div>{description}</div>
                            <div style="margin-top:0.55rem;">
                                <a href="{url}" target="_blank">Read full article</a>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No live articles retrieved. Add a NewsAPI key in Streamlit secrets to enable this feed.")
            st.markdown("</div>", unsafe_allow_html=True)

        # -------------------------------------------------
        # TAB 4 — INCIDENT DATA
        # -------------------------------------------------
        with tab4:
            mapped_tab, unmapped_tab = st.tabs(["Mapped Incidents", "Unmapped Articles"])

            with mapped_tab:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                if filtered_events:
                    mapped_df = pd.DataFrame(
                        [
                            {
                                "Title": event.get("title"),
                                "Location": event.get("location"),
                                "Region": event.get("region"),
                                "Risk": event.get("risk"),
                                "Score": event.get("score"),
                                "Confidence": event.get("confidence"),
                                "Category": event.get("category"),
                                "MITRE": event.get("mitre"),
                                "Business Impact": ", ".join(event.get("business_impact", [])),
                                "Watchlist Match": event.get("watchlist_match"),
                                "Source": event.get("source"),
                                "Published": event.get("published_at"),
                                "URL": event.get("url"),
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
                if filtered_unmapped:
                    unmapped_df = pd.DataFrame(
                        [
                            {
                                "Title": article.get("title"),
                                "Source": article.get("source"),
                                "Risk": article.get("risk"),
                                "Score": article.get("score"),
                                "Confidence": article.get("confidence"),
                                "Category": article.get("category"),
                                "MITRE": article.get("mitre"),
                                "Detected Location": article.get("detected_location"),
                                "Business Impact": ", ".join(article.get("business_impact", [])),
                                "Published": article.get("published_at"),
                                "Watchlist Match": article.get("watchlist_match"),
                                "URL": article.get("url"),
                            }
                            for article in filtered_unmapped
                        ]
                    )
                    st.dataframe(unmapped_df, use_container_width=True, height=420)
                else:
                    st.info("No unmapped articles match the selected filters.")
                st.markdown("</div>", unsafe_allow_html=True)

        # -------------------------------------------------
        # TAB 5 — TRENDS
        # -------------------------------------------------
        with tab5:
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

        # -------------------------------------------------
        # TAB 6 — REGIONAL ANALYSIS
        # -------------------------------------------------
        with tab6:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Regional Analysis")

            region_df = pd.DataFrame(
                [{"Region": region, "Incidents": count} for region, count in region_counts.items()]
            )

            if not region_df.empty:
                region_df = region_df.sort_values("Incidents", ascending=False)
                st.bar_chart(region_df.set_index("Region"), height=360)
                st.dataframe(region_df, use_container_width=True, height=220)
            else:
                st.info("No regional breakdown available from current results.")
            st.markdown("</div>", unsafe_allow_html=True)

        # -------------------------------------------------
        # TAB 7 — MITRE MAPPING
        # -------------------------------------------------
        with tab7:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("🧬 MITRE ATT&CK Mapping")

            mitre_df = pd.DataFrame(
                [
                    {
                        "Threat": e.get("title"),
                        "Technique": e.get("mitre"),
                        "Risk": e.get("risk"),
                        "Category": e.get("category"),
                        "Source": e.get("source"),
                    }
                    for e in filtered_events
                    if e.get("mitre") != "N/A"
                ]
            )

            if not mitre_df.empty:
                st.dataframe(mitre_df, use_container_width=True, height=420)
            else:
                st.info("No MITRE techniques identified in the filtered dataset.")
            st.markdown("</div>", unsafe_allow_html=True)

        # -------------------------------------------------
        # TAB 8 — IOC EXTRACTION
        # -------------------------------------------------
        with tab8:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("🔎 Indicator Extraction")

            ioc_df = build_ioc_table(filtered_events + filtered_unmapped)

            if not ioc_df.empty:
                st.dataframe(ioc_df, use_container_width=True, height=420)
                st.caption("Automatically extracted indicators from current reporting.")
            else:
                st.info("No indicators extracted from current reporting.")
            st.markdown("</div>", unsafe_allow_html=True)

        # -------------------------------------------------
        # TAB 9 — ENTITY TRACKING
        # -------------------------------------------------
        with tab9:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("👥 Entity Tracking")

            people_df, org_df, location_df = build_entity_summary(filtered_events + filtered_unmapped)

            ent_col1, ent_col2, ent_col3 = st.columns(3)

            with ent_col1:
                st.markdown("**People**")
                if not people_df.empty:
                    st.dataframe(people_df.head(15), use_container_width=True, height=300)
                else:
                    st.info("No people detected.")

            with ent_col2:
                st.markdown("**Organisations**")
                if not org_df.empty:
                    st.dataframe(org_df.head(15), use_container_width=True, height=300)
                else:
                    st.info("No organisations detected.")

            with ent_col3:
                st.markdown("**Locations**")
                if not location_df.empty:
                    st.dataframe(location_df.head(15), use_container_width=True, height=300)
                else:
                    st.info("No locations detected.")

            st.markdown("---")
            st.markdown("**Entity Preview**")

            preview_entities = []
            for item in (filtered_events + filtered_unmapped)[:5]:
                title = item.get("title", "Untitled")
                entities = item.get("entities", {})
                people = entities.get("people", [])
                orgs = entities.get("orgs", [])
                locations = entities.get("locations", [])

                preview_entities.append(
                    {
                        "Title": title,
                        "People": ", ".join(people[:5]),
                        "Organisations": ", ".join(orgs[:5]),
                        "Locations": ", ".join(locations[:5]),
                    }
                )

            if preview_entities:
                preview_df = pd.DataFrame(preview_entities)
                st.dataframe(preview_df, use_container_width=True, height=260)
            else:
                st.info("No entity preview available.")
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("Use the controls in the sidebar, then click 'Generate Intelligence Brief' to load the platform.")
