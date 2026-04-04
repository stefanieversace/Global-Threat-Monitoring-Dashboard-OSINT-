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
    page_title="Global Intelligence Briefing",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# PREMIUM UI STYLING
# =========================================================
st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
            color: #0f172a;
        }

        .block-container {
            max-width: 1280px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e2e8f0;
        }

        .main-title-card {
            background: rgba(255,255,255,0.88);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(226,232,240,0.9);
            border-radius: 24px;
            padding: 1.7rem 1.8rem;
            box-shadow: 0 10px 35px rgba(15, 23, 42, 0.06);
            margin-bottom: 1.1rem;
        }

        .main-title-card h1 {
            margin: 0;
            font-size: 2.15rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: #0f172a;
        }

        .main-title-card p {
            margin: 0.55rem 0 0 0;
            color: #475569;
            font-size: 1rem;
            line-height: 1.5;
        }

        .glass-card {
            background: rgba(255,255,255,0.92);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(226,232,240,0.95);
            border-radius: 22px;
            padding: 1.2rem 1.25rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
            margin-bottom: 1rem;
        }

        .soft-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 1.2rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
            margin-bottom: 1rem;
        }

        .muted-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 1.2rem;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
            margin-bottom: 1rem;
        }

        .section-label {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            color: #64748b;
            margin-bottom: 0.45rem;
            font-weight: 600;
        }

        .metric-note {
            color: #64748b;
            font-size: 0.9rem;
            margin-top: -0.15rem;
            margin-bottom: 1rem;
        }

        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.92);
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 1rem 0.95rem;
            box-shadow: 0 8px 25px rgba(15, 23, 42, 0.04);
        }

        .alert-card {
            border-radius: 18px;
            padding: 0.95rem 1rem;
            margin-bottom: 0.7rem;
            border: 1px solid #e2e8f0;
            background: #ffffff;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }

        .alert-critical {
            border-left: 5px solid #dc2626;
        }

        .alert-warning {
            border-left: 5px solid #f59e0b;
        }

        .alert-info {
            border-left: 5px solid #2563eb;
        }

        .brief-content {
            font-size: 0.97rem;
            line-height: 1.75;
            color: #1e293b;
        }

        .ai-content {
            font-size: 0.96rem;
            line-height: 1.75;
            color: #1e293b;
        }

        .pill {
            display: inline-block;
            padding: 0.32rem 0.7rem;
            border-radius: 999px;
            background: #eef2ff;
            color: #3730a3;
            font-size: 0.8rem;
            font-weight: 600;
            margin-right: 0.4rem;
            margin-bottom: 0.4rem;
        }

        .news-card {
            background: rgba(255,255,255,0.95);
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.9rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }

        .news-title {
            font-size: 1rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.28rem;
        }

        .news-meta {
            font-size: 0.82rem;
            color: #64748b;
            margin-bottom: 0.55rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 16px;
            padding-bottom: 0.35rem;
        }

        .stTabs [data-baseweb="tab"] {
            color: #64748b;
            font-weight: 600;
            padding: 0.25rem 0.1rem 0.55rem 0.1rem;
            background: transparent;
            border: none;
        }

        .stTabs [aria-selected="true"] {
            color: #0f172a !important;
            border-bottom: 2px solid #0f172a;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }

        .small-caption {
            font-size: 0.9rem;
            color: #64748b;
            margin-top: -0.1rem;
            margin-bottom: 1rem;
        }

        .sidebar-tip {
            font-size: 0.84rem;
            color: #64748b;
            line-height: 1.5;
        }

        .recommendation-item {
            padding: 0.65rem 0.8rem;
            border-radius: 14px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            margin-bottom: 0.55rem;
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
    <div class="main-title-card">
        <h1>Global Intelligence Briefing</h1>
        <p>
            Operational intelligence for risk monitoring, event security, reputational awareness,
            and decision support across fast-moving global developments.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="small-caption">Live monitoring • risk prioritisation • analyst outputs • executive-ready briefing</div>',
    unsafe_allow_html=True,
)


# =========================================================
# SECRETS / CLIENTS
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
    "ipv4": r"\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b",
    "domain": r"\\b(?:[a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,}\\b",
    "email": r"\\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}\\b",
    "url": r"https?://[^\\s]+",
    "sha256": r"\\b[a-fA-F0-9]{64}\\b",
    "md5": r"\\b[a-fA-F0-9]{32}\\b",
    "cve": r"\\bCVE-\\d{4}-\\d{4,7}\\b",
}

DEFAULT_NEWS_QUERY = (
    '("cyber attack" OR protest OR conflict OR unrest OR ransomware OR breach OR explosion OR disruption OR venue OR concert OR stadium)'
)


# =========================================================
# HELPERS
# =========================================================
def safe_get(item: Dict[str, Any], key: str, default: Any = "") -> Any:
    return item.get(key, default) if isinstance(item, dict) else default


def normalise_datetime(value: Any) -> str:
    return str(value) if value else "N/A"


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
            "Key Developments\n"
            "• No significant live developments retrieved.\n\n"
            "Risk Assessment\n"
            "Overall Risk: Low\n"
            "Drivers: No meaningful live reporting was available for synthesis.\n\n"
            "Analyst Insight\n"
            "Maintain standard monitoring posture and continue routine review cycles."
        )

    if not openai_client:
        return (
            "Key Developments\n"
            "• Live reporting was retrieved but the AI summary service was unavailable.\n\n"
            "Risk Assessment\n"
            "Overall Risk: Medium\n"
            "Drivers: Live items are present and should be manually reviewed.\n\n"
            "Analyst Insight\n"
            "Continue monitoring the latest reporting and review the live feed directly for time-sensitive developments."
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
You are a senior intelligence analyst supporting operational security teams.

Write a concise, professional intelligence briefing.

Do NOT use markdown symbols.

Format EXACTLY like this:

Key Developments
• bullet
• bullet
• bullet

Risk Assessment
Overall Risk: High/Medium/Low
Drivers: short explanation

Analyst Insight
2-3 sentences max, clear and confident

Focus on:
- operational disruption
- venue or event risk
- reputational impact
- cyber threats

Data:
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
            "Key Developments\n"
            "• Live reporting was retrieved but the AI summary service was unavailable.\n\n"
            "Risk Assessment\n"
            "Overall Risk: Medium\n"
            "Drivers: Live items are present and should be manually reviewed.\n\n"
            "Analyst Insight\n"
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

    if nlp is not None:
        try:
            doc = nlp(text)
            people = sorted(set(ent.text for ent in doc.ents if ent.label_ == "PERSON"))
            orgs = sorted(set(ent.text for ent in doc.ents if ent.label_ == "ORG"))
            locations = sorted(set(ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC", "FAC"]))
            return {"people": people, "orgs": orgs, "locations": locations}
        except Exception:
            pass

    capitalised = re.findall(r"\\b[A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*\\b", text)
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
        alerts.append({"level": "WARNING", "message": "High-profile individual or executive-related reporting requires review."})

    if reputational_impacts:
        alerts.append({"level": "INFO", "message": "Reputationally sensitive reporting is present in the current cycle."})

    if cyber_impacts or ("cyber" in (brief or "").lower()):
        alerts.append({"level": "INFO", "message": "Cyber-related reporting is present in current monitoring."})

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


def generate_recommendations(mapped_events, high_count, watchlist_matches):
    actions = []

    if high_count >= 3:
        actions.append("Increase monitoring posture across high-risk regions")
        actions.append("Review exposure to affected locations and operations")
        actions.append("Escalate relevant items to security leadership or incident response")

    if watchlist_matches > 0:
        actions.append("Monitor watchlist-related developments closely")
        actions.append("Assess potential impact to assets, personnel, or events")

    venue_risks = [e for e in mapped_events if "Venue Operations" in e.get("business_impact", [])]
    if venue_risks:
        actions.append("Review upcoming events in affected locations")
        actions.append("Coordinate with venue security teams where necessary")

    cyber_risks = [e for e in mapped_events if e.get("category") == "Cyber"]
    if cyber_risks:
        actions.append("Increase monitoring for phishing, intrusion, or cyber disruption activity")
        actions.append("Validate current digital security controls and response readiness")

    if not actions:
        actions.append("Maintain standard monitoring posture")
        actions.append("Continue routine intelligence review cycle")

    return list(dict.fromkeys(actions))[:5]


def render_alerts(alerts: List[Dict[str, str]]) -> None:
    if not alerts:
        return

    st.markdown("### Alerts")
    for alert in alerts:
        level = alert.get("level", "INFO")
        message = alert.get("message", "Alert triggered.")

        css_class = "alert-info"
        icon = "🔵"

        if level == "CRITICAL":
            css_class = "alert-critical"
            icon = "🔴"
        elif level == "WARNING":
            css_class = "alert-warning"
            icon = "🟠"

        st.markdown(
            f"""
            <div class="alert-card {css_class}">
                {icon} <strong>{message}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )


def format_ai_output(text: str) -> str:
    if not text:
        return ""

    html_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html_text = html_text.replace("\n", "<br>")

    html_text = html_text.replace("Key Developments", "<strong>Key Developments</strong>")
    html_text = html_text.replace("Risk Assessment", "<strong>Risk Assessment</strong>")
    html_text = html_text.replace("Analyst Insight", "<strong>Analyst Insight</strong>")

    return html_text


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("Controls")

    selected_risks = st.multiselect(
        "Risk level",
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
        placeholder="e.g. London, protest, executive, venue",
    )

    max_articles = st.slider("Articles to analyse", 5, 30, 10)

    live_news_query = st.text_area(
        "Live news query",
        value=DEFAULT_NEWS_QUERY,
        height=120,
    )

    st.markdown("---")
    st.markdown(
        '<div class="sidebar-tip">Use the filters to narrow the monitoring view, then generate a fresh intelligence cycle.</div>',
        unsafe_allow_html=True,
    )

watchlist_terms = [term.strip() for term in watchlist_input.split(",") if term.strip()]


# =========================================================
# MAIN
# =========================================================
if st.button("Generate Intelligence Brief", use_container_width=True):
    try:
        brief, mapped_events, unmapped_articles, summary = generate_brief(
            max_articles=max_articles,
            watchlist_terms=watchlist_terms,
        )

        live_articles = fetch_live_news(query=live_news_query, page_size=max_articles)

        mapped_events = add_enrichment_to_events(mapped_events)
        unmapped_articles = add_enrichment_to_events(unmapped_articles)

        ai_summary = generate_ai_summary(live_articles)

        high_count = summary.get("high_count", 0)
        medium_count = summary.get("medium_count", 0)
        low_count = summary.get("low_count", 0)
        watchlist_matches = summary.get("watchlist_matches", 0)
        region_counts = summary.get("region_counts", {})
        key_judgements = summary.get("key_judgements", [])

        top_region = max(region_counts, key=region_counts.get) if region_counts else "N/A"
        priority_score = len([e for e in mapped_events if e.get("risk") == "HIGH"]) * 10 + (watchlist_matches * 5)

        confidence = "Medium"
        if high_count >= 3:
            confidence = "High"
        elif len(mapped_events) < 3:
            confidence = "Low"

        alerts = evaluate_alerts(brief, mapped_events, watchlist_matches)
        actions = generate_recommendations(mapped_events, high_count, watchlist_matches)

        # Metrics
        st.markdown("### Monitoring Snapshot")
        st.markdown('<div class="metric-note">A quick view of current reporting volume, severity, and priority.</div>', unsafe_allow_html=True)

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("High Risk", high_count)
        m2.metric("Medium Risk", medium_count)
        m3.metric("Low Risk", low_count)
        m4.metric("Priority Score", priority_score)
        m5.metric("Top Region", top_region)
        m6.metric("Confidence", confidence)

        st.markdown("")

        # Alerts
        render_alerts(alerts)

        # Brief + AI Summary
        left_col, right_col = st.columns([1.15, 1], gap="large")

        with left_col:
            st.markdown("### Intelligence Brief")
            st.markdown(
                f"""
                <div class="soft-card brief-content">
                    {brief.replace(chr(10), "<br>")}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right_col:
            st.markdown("### AI Summary")
            st.markdown(
                f"""
                <div class="muted-card ai-content">
                    {format_ai_output(ai_summary)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Recommendations + Judgements
        lower_left, lower_right = st.columns([1, 1], gap="large")

        with lower_left:
            st.markdown("### Recommended Actions")
            st.markdown('<div class="soft-card">', unsafe_allow_html=True)
            for action in actions:
                st.markdown(f'<div class="recommendation-item">• {action}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with lower_right:
            st.markdown("### Key Judgements")
            st.markdown('<div class="soft-card">', unsafe_allow_html=True)
            if key_judgements:
                for idx, judgement in enumerate(key_judgements[:3], start=1):
                    st.markdown(f"**{idx}.** {judgement}")
            else:
                st.markdown("No key judgements were returned for this cycle.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Filtered events
        filtered_events = [
            event for event in mapped_events
            if event.get("risk") in selected_risks and event.get("category") in selected_categories
        ]

        filtered_unmapped = [
            article for article in unmapped_articles
            if article.get("risk") in selected_risks and article.get("category") in selected_categories
        ]

        # Map
        st.markdown("### Global Map")
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        threat_map = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")
        marker_cluster = MarkerCluster().add_to(threat_map)

        for event in filtered_events:
            popup_text = (
                f"<b>{event.get('title', 'Untitled')}</b><br>"
                f"Location: {event.get('location', 'N/A')}<br>"
                f"Region: {event.get('region', 'N/A')}<br>"
                f"Risk: {event.get('risk', 'N/A')}<br>"
                f"Score: {event.get('score', 'N/A')}<br>"
                f"Category: {event.get('category', 'N/A')}<br>"
                f"MITRE: {event.get('mitre', 'N/A')}<br>"
                f"Business Impact: {', '.join(event.get('business_impact', []))}<br>"
                f"Source: {event.get('source', 'N/A')}<br>"
                f"<a href='{event.get('url', '#')}' target='_blank'>Open article</a>"
            )

            if event.get("risk") == "HIGH":
                color = "#dc2626"
            elif event.get("risk") == "MEDIUM":
                color = "#f59e0b"
            else:
                color = "#16a34a"

            lat = event.get("lat")
            lon = event.get("lon")

            if lat is not None and lon is not None:
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=6,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.75,
                    popup=folium.Popup(popup_text, max_width=360),
                ).add_to(marker_cluster)

        html(threat_map._repr_html_(), height=530)
        st.caption(f"Showing {len(filtered_events)} mapped incidents after filters.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Incidents", "MITRE", "IOC", "Entities", "Live Feed"]
        )

        with tab1:
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
                        "Business Impact": ", ".join(event.get("business_impact", [])),
                        "Source": event.get("source"),
                        "Published": event.get("published_at"),
                    }
                    for event in filtered_events
                ]
            )

            if not mapped_df.empty:
                st.dataframe(mapped_df, use_container_width=True, height=430)
            else:
                st.info("No incidents match the selected filters.")

        with tab2:
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
                st.dataframe(mitre_df, use_container_width=True, height=430)
            else:
                st.info("No MITRE mappings identified.")

        with tab3:
            ioc_df = build_ioc_table(filtered_events + filtered_unmapped)
            if not ioc_df.empty:
                st.dataframe(ioc_df, use_container_width=True, height=430)
            else:
                st.info("No indicators extracted from current reporting.")

        with tab4:
            people_df, org_df, location_df = build_entity_summary(filtered_events + filtered_unmapped)

            c1, c2, c3 = st.columns(3, gap="large")

            with c1:
                st.markdown("**People**")
                if not people_df.empty:
                    st.dataframe(people_df.head(15), use_container_width=True, height=300)
                else:
                    st.info("No people detected.")

            with c2:
                st.markdown("**Organisations**")
                if not org_df.empty:
                    st.dataframe(org_df.head(15), use_container_width=True, height=300)
                else:
                    st.info("No organisations detected.")

            with c3:
                st.markdown("**Locations**")
                if not location_df.empty:
                    st.dataframe(location_df.head(15), use_container_width=True, height=300)
                else:
                    st.info("No locations detected.")

        with tab5:
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
                            <div style="margin-top:0.65rem;">
                                <a href="{url}" target="_blank">Read full article</a>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No live articles retrieved. Add a NewsAPI key in Streamlit secrets to enable this feed.")

        # Trend line
        history_df = load_history()
        if not history_df.empty:
            st.markdown("### Threat Trends")
            trend_df = (
                history_df.groupby("date")[["high_count", "medium_count", "low_count"]]
                .max()
                .reset_index()
            )
            trend_df = trend_df.set_index("date")
            st.line_chart(trend_df, height=270)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.markdown(
        """
        <div class="glass-card">
            <div class="section-label">Ready</div>
            <div style="font-size:1rem; color:#334155; line-height:1.7;">
                Use the controls in the sidebar, then click <strong>Generate Intelligence Brief</strong>
                to run a fresh monitoring cycle.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
