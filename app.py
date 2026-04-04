import re
import random
from datetime import datetime, timedelta
from collections import Counter
from typing import Dict, List, Tuple, Any

import requests
import pandas as pd
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit.components.v1 import html

from scripts.threat_monitor import generate_brief, load_history

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
    page_title="Global Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# SESSION STATE
# =========================================================
if "selected_incident" not in st.session_state:
    st.session_state.selected_incident = None

if "incident_status" not in st.session_state:
    st.session_state.incident_status = {}

if "last_generated" not in st.session_state:
    st.session_state.last_generated = None


# =========================================================
# APPLE / MACOS STYLE UI
# =========================================================
st.markdown(
    """
    <style>
        :root {
            --bg: #f5f5f7;
            --panel: rgba(255,255,255,0.82);
            --panel-strong: rgba(255,255,255,0.92);
            --border: rgba(15, 23, 42, 0.08);
            --text: #111827;
            --muted: #6b7280;
            --muted-2: #94a3b8;
            --shadow: 0 12px 40px rgba(15, 23, 42, 0.06);
            --radius-xl: 24px;
            --radius-lg: 18px;
            --radius-md: 14px;
            --blue: #2563eb;
            --red: #ef4444;
            --orange: #f59e0b;
            --green: #16a34a;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255,255,255,0.65), transparent 30%),
                radial-gradient(circle at top right, rgba(226,232,240,0.6), transparent 35%),
                linear-gradient(180deg, #fbfbfc 0%, var(--bg) 100%);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", Inter, sans-serif;
        }

        .block-container {
            max-width: 1440px;
            padding-top: 1.35rem;
            padding-bottom: 2rem;
        }

        header, #MainMenu, footer {
            visibility: hidden;
        }

        section[data-testid="stSidebar"] {
            background: rgba(255,255,255,0.7);
            border-right: 1px solid rgba(15,23,42,0.06);
            backdrop-filter: blur(14px);
        }

        div[data-testid="stVerticalBlock"] > div {
            gap: 0.55rem;
        }

        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.84);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 0.95rem;
            box-shadow: var(--shadow);
            backdrop-filter: blur(14px);
        }

        .app-shell {
            margin-bottom: 1rem;
        }

        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            background: rgba(255,255,255,0.78);
            border: 1px solid var(--border);
            border-radius: 28px;
            padding: 1.35rem 1.4rem 1.2rem 1.4rem;
            backdrop-filter: blur(16px);
            box-shadow: 0 20px 50px rgba(15,23,42,0.06);
            margin-bottom: 1rem;
        }

        .topbar-title {
            font-size: 2.25rem;
            line-height: 1.05;
            letter-spacing: -0.04em;
            font-weight: 700;
            margin: 0;
            color: #0f172a;
        }

        .topbar-subtitle {
            margin-top: 0.45rem;
            color: var(--muted);
            font-size: 0.98rem;
            line-height: 1.5;
            max-width: 760px;
        }

        .topbar-meta {
            text-align: right;
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.5;
            white-space: nowrap;
        }

        .glass-card {
            background: rgba(255,255,255,0.8);
            border: 1px solid var(--border);
            border-radius: var(--radius-xl);
            padding: 1rem 1rem 1.05rem 1rem;
            box-shadow: var(--shadow);
            backdrop-filter: blur(16px);
        }

        .glass-card-tight {
            background: rgba(255,255,255,0.84);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 0.95rem;
            box-shadow: var(--shadow);
            backdrop-filter: blur(16px);
        }

        .section-kicker {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--muted-2);
            font-weight: 700;
            margin-bottom: 0.45rem;
        }

        .section-title {
            font-size: 1.08rem;
            font-weight: 650;
            letter-spacing: -0.02em;
            color: #0f172a;
            margin: 0 0 0.15rem 0;
        }

        .section-note {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 0.75rem;
        }

        .incident-chip {
            display: inline-block;
            padding: 0.35rem 0.72rem;
            border-radius: 999px;
            background: #eff6ff;
            color: #1d4ed8;
            font-size: 0.79rem;
            font-weight: 600;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
            border: 1px solid rgba(37, 99, 235, 0.12);
        }

        .queue-item {
            border: 1px solid rgba(15,23,42,0.06);
            background: rgba(248,250,252,0.72);
            border-radius: 16px;
            padding: 0.8rem 0.85rem;
            margin-bottom: 0.55rem;
        }

        .queue-priority {
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            color: var(--muted-2);
            font-weight: 700;
            margin-bottom: 0.28rem;
        }

        .queue-title {
            font-size: 0.92rem;
            font-weight: 600;
            color: #0f172a;
            line-height: 1.35;
            margin-bottom: 0.35rem;
        }

        .queue-meta {
            color: var(--muted);
            font-size: 0.8rem;
            line-height: 1.45;
        }

        .divider {
            height: 1px;
            background: rgba(15,23,42,0.07);
            margin: 0.9rem 0;
            border: 0;
        }

        .summary-text {
            color: #1e293b;
            font-size: 0.95rem;
            line-height: 1.75;
        }

        .brief-box, .ai-box, .investigation-box {
            background: rgba(255,255,255,0.64);
            border: 1px solid rgba(15,23,42,0.06);
            border-radius: 18px;
            padding: 0.95rem;
        }

        .timeline-item {
            border-left: 3px solid rgba(37, 99, 235, 0.95);
            background: rgba(248,250,252,0.78);
            border-radius: 12px;
            padding: 0.72rem 0.8rem;
            margin-bottom: 0.55rem;
            border-top: 1px solid rgba(15,23,42,0.04);
            border-right: 1px solid rgba(15,23,42,0.04);
            border-bottom: 1px solid rgba(15,23,42,0.04);
        }

        .timeline-time {
            font-size: 0.78rem;
            font-weight: 700;
            color: var(--muted-2);
            margin-bottom: 0.15rem;
        }

        .timeline-event {
            font-size: 0.9rem;
            color: #1e293b;
            line-height: 1.45;
        }

        .log-item {
            background: rgba(248,250,252,0.82);
            border-radius: 12px;
            padding: 0.72rem 0.8rem;
            margin-bottom: 0.5rem;
            border: 1px solid rgba(15,23,42,0.05);
            font-size: 0.86rem;
        }

        .log-high {
            border-left: 3px solid var(--red);
        }

        .log-medium {
            border-left: 3px solid var(--orange);
        }

        .log-low {
            border-left: 3px solid var(--blue);
        }

        .recommendation-item {
            background: rgba(248,250,252,0.86);
            border: 1px solid rgba(15,23,42,0.05);
            border-radius: 14px;
            padding: 0.72rem 0.85rem;
            margin-bottom: 0.5rem;
            color: #1e293b;
            font-size: 0.9rem;
            line-height: 1.45;
        }

        .alert-card {
            background: rgba(255,255,255,0.86);
            border: 1px solid rgba(15,23,42,0.06);
            border-radius: 16px;
            padding: 0.82rem 0.95rem;
            margin-bottom: 0.55rem;
        }

        .alert-critical {
            border-left: 4px solid var(--red);
        }

        .alert-warning {
            border-left: 4px solid var(--orange);
        }

        .alert-info {
            border-left: 4px solid var(--blue);
        }

        .news-card {
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(15,23,42,0.06);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 8px 24px rgba(15,23,42,0.04);
        }

        .news-title {
            font-size: 0.98rem;
            font-weight: 650;
            color: #0f172a;
            margin-bottom: 0.25rem;
            line-height: 1.35;
        }

        .news-meta {
            font-size: 0.8rem;
            color: var(--muted-2);
            margin-bottom: 0.45rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 18px;
            padding-bottom: 0.2rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border: none;
            color: var(--muted);
            font-weight: 600;
            padding: 0.15rem 0.05rem 0.6rem 0.05rem;
        }

        .stTabs [aria-selected="true"] {
            color: #0f172a !important;
            border-bottom: 2px solid #0f172a;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(15,23,42,0.07);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(15,23,42,0.03);
        }

        iframe {
            border-radius: 20px !important;
        }

        .status-pill {
            display: inline-block;
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background: rgba(15,23,42,0.06);
            color: #0f172a;
            font-size: 0.8rem;
            font-weight: 650;
        }
    </style>
    """,
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
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "domain": r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b",
    "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    "url": r"https?://[^\s]+",
    "sha256": r"\b[a-fA-F0-9]{64}\b",
    "md5": r"\b[a-fA-F0-9]{32}\b",
    "cve": r"\bCVE-\d{4}-\d{4,7}\b",
}

DEFAULT_NEWS_QUERY = '("cyber attack" OR protest OR conflict OR unrest OR ransomware OR breach OR explosion OR disruption OR venue OR concert OR stadium)'

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


def format_ai_output(text: str) -> str:
    if not text:
        return ""

    html_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html_text = html_text.replace("\n", "<br>")
    replacements = [
        "Key Developments",
        "Risk Assessment",
        "Analyst Insight",
        "Profile Summary",
        "Likely Objectives",
        "Observed Techniques",
        "Assessment",
    ]
    for item in replacements:
        html_text = html_text.replace(item, f"<strong>{item}</strong>")
    return html_text


def render_alerts(alerts: List[Dict[str, str]]) -> None:
    if not alerts:
        return

    st.markdown('<div class="section-kicker">Signals</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Active alerts</div>', unsafe_allow_html=True)
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


def build_triage_queue(events):
    rows = []

    for event in events:
        risk = event.get("risk", "LOW")
        category = event.get("category", "General")
        impacts = event.get("business_impact", [])
        title = event.get("title", "Untitled")

        score = 0

        if risk == "HIGH":
            score += 50
        elif risk == "MEDIUM":
            score += 30
        else:
            score += 10

        if category == "Cyber":
            score += 15
        elif category == "Physical":
            score += 12
        elif category == "Political":
            score += 10
        elif category == "Environmental":
            score += 8

        if "Venue Operations" in impacts:
            score += 15
        if "Talent / Executive Protection" in impacts:
            score += 12
        if "Reputational Risk" in impacts:
            score += 10
        if "Digital Operations" in impacts:
            score += 10

        if event.get("watchlist_match"):
            score += 10

        if score >= 80:
            priority = "P1"
        elif score >= 60:
            priority = "P2"
        elif score >= 40:
            priority = "P3"
        else:
            priority = "P4"

        rows.append(
            {
                "Priority": priority,
                "Priority Score": score,
                "Title": title,
                "Risk": risk,
                "Category": category,
                "Region": event.get("region", "N/A"),
                "Location": event.get("location", "N/A"),
                "Business Impact": ", ".join(impacts),
                "Source": event.get("source", "N/A"),
            }
        )

    triage_df = pd.DataFrame(rows)
    if not triage_df.empty:
        priority_order = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
        triage_df["Priority Rank"] = triage_df["Priority"].map(priority_order)
        triage_df = triage_df.sort_values(
            by=["Priority Rank", "Priority Score"],
            ascending=[True, False]
        ).drop(columns=["Priority Rank"])

    return triage_df


def build_mitre_heatmap(events):
    rows = []
    for event in events:
        mitre_value = event.get("mitre", "N/A")
        if mitre_value == "N/A":
            continue
        rows.append(
            {
                "Technique": mitre_value,
                "Category": event.get("category", "General"),
                "Count": 1,
            }
        )

    if not rows:
        return pd.DataFrame()

    mitre_df = pd.DataFrame(rows)
    return mitre_df.pivot_table(
        index="Technique",
        columns="Category",
        values="Count",
        aggfunc="sum",
        fill_value=0
    )


def generate_timeline(incident):
    timeline = []
    now = datetime.utcnow()

    timeline.append({
        "time": (now - timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "event": "Initial reporting detected via OSINT sources"
    })

    if incident.get("category") == "Cyber":
        timeline.append({
            "time": (now - timedelta(minutes=40)).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "event": "Suspicious cyber-related indicators identified in reporting"
        })
        timeline.append({
            "time": (now - timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "event": "Potential compromise pattern observed and mapped to MITRE techniques"
        })

    if incident.get("risk") == "HIGH":
        timeline.append({
            "time": (now - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "event": "Escalation threshold reached due to high-risk indicators"
        })

    timeline.append({
        "time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "event": "Incident under active analyst investigation"
    })

    return timeline


def generate_logs(incident):
    logs = []
    now = datetime.utcnow()

    log_templates = [
        {
            "message": "Multiple failed authentication attempts detected",
            "mitre": "T1110 - Brute Force",
            "base_severity": "MEDIUM"
        },
        {
            "message": "Suspicious PowerShell execution",
            "mitre": "T1059.001 - PowerShell",
            "base_severity": "HIGH"
        },
        {
            "message": "Outbound connection to flagged domain",
            "mitre": "T1071 - Application Layer Protocol",
            "base_severity": "HIGH"
        },
        {
            "message": "Phishing email detected",
            "mitre": "T1566 - Phishing",
            "base_severity": "MEDIUM"
        },
        {
            "message": "Unusual login from new geolocation",
            "mitre": "T1078 - Valid Accounts",
            "base_severity": "MEDIUM"
        },
        {
            "message": "File flagged by endpoint protection",
            "mitre": "T1204 - User Execution",
            "base_severity": "LOW"
        }
    ]

    for i in range(6):
        template = random.choice(log_templates)
        timestamp = (now - timedelta(minutes=i * 5)).strftime("%Y-%m-%d %H:%M:%S UTC")
        logs.append({
            "time": timestamp,
            "log": template["message"],
            "mitre": template["mitre"],
            "severity": template["base_severity"]
        })

    return logs


def calculate_incident_severity(logs):
    score = 0
    for log in logs:
        if log["severity"] == "HIGH":
            score += 3
        elif log["severity"] == "MEDIUM":
            score += 2
        else:
            score += 1

    if score >= 12:
        return "CRITICAL"
    elif score >= 8:
        return "HIGH"
    elif score >= 5:
        return "MEDIUM"
    return "LOW"


def generate_threat_actor_profile(incident):
    text = " ".join([
        str(incident.get("title", "")),
        str(incident.get("description", "")),
        str(incident.get("category", "")),
        str(incident.get("mitre", "")),
        str(", ".join(incident.get("business_impact", []))),
    ])

    if not openai_client:
        return f"""
Profile Summary
This incident appears most consistent with a {incident.get("category", "General").lower()} threat scenario.

Likely Objectives
• Disruption of operations
• Reputational or security impact
• Increased operational pressure

Observed Techniques
• {incident.get("mitre", "No MITRE mapping available")}

Assessment
This profile is auto-generated from incident context and should be treated as a working analytical hypothesis rather than confirmed attribution.
""".strip()

    prompt = f"""
You are a threat intelligence analyst.

Based on the incident context below, generate a concise threat actor profile.

Do NOT use markdown symbols.

Format exactly like this:

Profile Summary
[2 sentences]

Likely Objectives
• objective
• objective
• objective

Observed Techniques
• technique
• technique

Assessment
[2 sentences max]

Incident Context:
{text}
"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Threat actor profile generation unavailable."


def generate_kql_detections(incident):
    category = incident.get("category", "General")
    title = incident.get("title", "")
    location = incident.get("location", "")
    mitre = incident.get("mitre", "N/A")

    detections = []

    if category == "Cyber":
        detections.append({
            "name": "Suspicious PowerShell Execution",
            "severity": "High",
            "mitre": "T1059.001 - PowerShell",
            "kql": """
DeviceProcessEvents
| where Timestamp > ago(24h)
| where FileName =~ "powershell.exe"
| where ProcessCommandLine has_any ("Invoke-WebRequest", "IEX", "DownloadString")
| project Timestamp, DeviceName, AccountName, ProcessCommandLine
""".strip()
        })
        detections.append({
            "name": "Phishing Link Click Followed by Login",
            "severity": "Medium",
            "mitre": "T1566 - Phishing",
            "kql": """
EmailEvents
| where Timestamp > ago(24h)
| where ThreatTypes has "Phish"
| join kind=inner (
    SigninLogs
    | where TimeGenerated > ago(24h)
) on $left.RecipientEmailAddress == $right.UserPrincipalName
| project Timestamp, RecipientEmailAddress, UserPrincipalName, IPAddress
""".strip()
        })

    if category == "Physical":
        detections.append({
            "name": "Venue Threat Escalation Monitoring",
            "severity": "High",
            "mitre": mitre,
            "kql": f"""
SecurityAlert
| where TimeGenerated > ago(24h)
| where AlertName has_any ("crowd", "venue", "incident", "perimeter")
| extend Location = "{location}"
| project TimeGenerated, AlertName, Severity, Location
""".strip()
        })

    if category == "Political":
        detections.append({
            "name": "Protest Activity Monitoring",
            "severity": "Medium",
            "mitre": mitre,
            "kql": f"""
ThreatIntelligenceIndicator
| where TimeGenerated > ago(24h)
| where Description has_any ("protest", "civil unrest", "demonstration")
| extend IncidentTitle = "{title}"
| project TimeGenerated, Description, ConfidenceScore, IncidentTitle
""".strip()
        })

    if category == "Environmental":
        detections.append({
            "name": "Operational Disruption Watch",
            "severity": "Medium",
            "mitre": mitre,
            "kql": f"""
Heartbeat
| where TimeGenerated > ago(24h)
| summarize LastSeen=max(TimeGenerated) by Computer
| extend IncidentContext = "{title}"
| project Computer, LastSeen, IncidentContext
""".strip()
        })

    if not detections:
        detections.append({
            "name": "General Incident Monitoring Rule",
            "severity": "Low",
            "mitre": mitre,
            "kql": f"""
SecurityEvent
| where TimeGenerated > ago(24h)
| extend IncidentTitle = "{title}"
| project TimeGenerated, Computer, Account, IncidentTitle
""".strip()
        })

    return detections


# =========================================================
# HEADER
# =========================================================
last_run = st.session_state.last_generated or "Not run yet"
st.markdown(
    f"""
    <div class="topbar">
        <div>
            <div class="topbar-title">Global Intelligence</div>
            <div class="topbar-subtitle">
                Real-time monitoring and decision support for fast-moving incidents, operational risk, and emerging threat activity.
            </div>
        </div>
        <div class="topbar-meta">
            <div><strong>Mode</strong> — Operational</div>
            <div><strong>Last run</strong> — {last_run}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# CONTROL BAR
# =========================================================
with st.container():
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1.2, 2, 0.95], gap="small")

    selected_risks = c1.multiselect(
        "Risk",
        ["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM", "LOW"],
        label_visibility="visible",
    )

    selected_categories = c2.multiselect(
        "Category",
        ["Cyber", "Physical", "Political", "Environmental", "General"],
        default=["Cyber", "Physical", "Political", "Environmental", "General"],
        label_visibility="visible",
    )

    watchlist_input = c3.text_input(
        "Watchlist",
        placeholder="e.g. London, executive, venue",
    )

    live_news_query = c4.text_input(
        "Topics",
        value="cyber attack, protest, conflict, ransomware, breach, disruption",
    )

    max_articles = c5.slider("Articles", 5, 30, 10)

watchlist_terms = [term.strip() for term in watchlist_input.split(",") if term.strip()]
news_query = " OR ".join([q.strip() for q in live_news_query.split(",") if q.strip()]) or DEFAULT_NEWS_QUERY

# =========================================================
# RUN
# =========================================================
if st.button("Generate Intelligence Cycle", use_container_width=True):
    try:
        brief, mapped_events, unmapped_articles, summary = generate_brief(
            max_articles=max_articles,
            watchlist_terms=watchlist_terms,
        )

        st.session_state.last_generated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        live_articles = fetch_live_news(query=news_query, page_size=max_articles)

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

        filtered_events = [
            event for event in mapped_events
            if event.get("risk") in selected_risks and event.get("category") in selected_categories
        ]

        filtered_unmapped = [
            article for article in unmapped_articles
            if article.get("risk") in selected_risks and article.get("category") in selected_categories
        ]

        triage_df = build_triage_queue(filtered_events)

        if st.session_state.selected_incident is None and filtered_events:
            st.session_state.selected_incident = filtered_events[0]

        # =================================================
        # METRICS
        # =================================================
        m1, m2, m3, m4, m5, m6 = st.columns(6, gap="small")
        m1.metric("High Risk", high_count)
        m2.metric("Medium Risk", medium_count)
        m3.metric("Low Risk", low_count)
        m4.metric("Priority Score", priority_score)
        m5.metric("Top Region", top_region)
        m6.metric("Confidence", confidence)

        st.markdown("<div style='height:0.65rem'></div>", unsafe_allow_html=True)
        render_alerts(alerts)
        st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)

        # =================================================
        # COMMAND CENTER
        # =================================================
        left, center, right = st.columns([1.05, 2.15, 1.25], gap="large")

        with left:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="section-kicker">Queue</div>
                    <div class="section-title">Triage queue</div>
                    <div class="section-note">Prioritised incidents ready for analyst review.</div>
                """,
                unsafe_allow_html=True,
            )

            if not triage_df.empty:
                for i, event in enumerate(filtered_events[:14]):
                    risk = event.get("risk", "LOW")
                    priority_row = triage_df[triage_df["Title"] == event.get("title", "")]
                    priority = priority_row.iloc[0]["Priority"] if not priority_row.empty else "P4"

                    st.markdown(
                        f"""
                        <div class="queue-item">
                            <div class="queue-priority">{priority} • {risk}</div>
                            <div class="queue-title">{event.get("title", "Untitled")[:90]}</div>
                            <div class="queue-meta">{event.get("location", "N/A")} • {event.get("category", "General")}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        f"Open incident {i+1}",
                        key=f"queue_open_{i}",
                        use_container_width=True
                    ):
                        st.session_state.selected_incident = event
            else:
                st.info("No incidents available for triage.")

            st.markdown("</div>", unsafe_allow_html=True)

        with center:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="section-kicker">Operations</div>
                    <div class="section-title">Live map</div>
                    <div class="section-note">Geospatial view of filtered incident activity.</div>
                """,
                unsafe_allow_html=True,
            )

            threat_map = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")
            marker_cluster = MarkerCluster().add_to(threat_map)

            for event in filtered_events:
                lat = event.get("lat")
                lon = event.get("lon")
                if lat is None or lon is None:
                    continue

                popup_text = (
                    f"<b>{event.get('title', 'Untitled')}</b><br>"
                    f"Location: {event.get('location', 'N/A')}<br>"
                    f"Region: {event.get('region', 'N/A')}<br>"
                    f"Risk: {event.get('risk', 'N/A')}<br>"
                    f"Category: {event.get('category', 'N/A')}<br>"
                    f"MITRE: {event.get('mitre', 'N/A')}<br>"
                    f"Source: {event.get('source', 'N/A')}"
                )

                if event.get("risk") == "HIGH":
                    color = "#ef4444"
                elif event.get("risk") == "MEDIUM":
                    color = "#f59e0b"
                else:
                    color = "#2563eb"

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=5,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.72,
                    popup=folium.Popup(popup_text, max_width=360),
                ).add_to(marker_cluster)

            html(threat_map._repr_html_(), height=610)
            st.caption(f"Showing {len(filtered_events)} mapped incidents after filters.")
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            incident = st.session_state.selected_incident

            st.markdown(
                """
                <div class="glass-card">
                    <div class="section-kicker">Investigation</div>
                    <div class="section-title">Active incident</div>
                    <div class="section-note">Live analyst view for the selected incident.</div>
                """,
                unsafe_allow_html=True,
            )

            if incident:
                logs = generate_logs(incident)
                severity_level = calculate_incident_severity(logs)
                profile = generate_threat_actor_profile(incident)
                incident_id = incident.get("title", "Untitled")
                current_status = st.session_state.incident_status.get(incident_id, "New")

                st.markdown(
                    f"""
                    <div class="investigation-box">
                        <div style="font-size:1rem; font-weight:650; line-height:1.4; margin-bottom:0.5rem;">
                            {incident.get("title", "Untitled")}
                        </div>
                        <div style="color:#6b7280; font-size:0.9rem; line-height:1.6;">
                            <strong>Location:</strong> {incident.get("location", "N/A")}<br>
                            <strong>Region:</strong> {incident.get("region", "N/A")}<br>
                            <strong>Risk:</strong> {incident.get("risk", "N/A")}<br>
                            <strong>Category:</strong> {incident.get("category", "N/A")}<br>
                            <strong>Severity:</strong> {severity_level}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
                st.markdown(f"<span class='status-pill'>{current_status}</span>", unsafe_allow_html=True)
                st.markdown("<div style='height:0.55rem'></div>", unsafe_allow_html=True)

                b1, b2, b3 = st.columns(3, gap="small")
                if b1.button("Investigate", key=f"investigate_{incident_id}", use_container_width=True):
                    st.session_state.incident_status[incident_id] = "Investigating"
                if b2.button("Escalate", key=f"escalate_{incident_id}", use_container_width=True):
                    st.session_state.incident_status[incident_id] = "Escalated"
                if b3.button("Resolve", key=f"resolve_{incident_id}", use_container_width=True):
                    st.session_state.incident_status[incident_id] = "Resolved"

                st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                st.markdown("**MITRE**")
                st.markdown(incident.get("mitre", "N/A"))

                st.markdown("**Business impact**")
                impacts = incident.get("business_impact", [])
                if impacts:
                    for impact in impacts:
                        st.markdown(f"<span class='incident-chip'>{impact}</span>", unsafe_allow_html=True)
                else:
                    st.markdown("No business impact tags available.")

                st.markdown("**Indicators**")
                iocs = incident.get("iocs", {})
                has_ioc = False
                for key, values in iocs.items():
                    if values:
                        has_ioc = True
                        st.markdown(f"**{key.upper()}**")
                        for value in values[:3]:
                            st.markdown(f"- {value}")
                if not has_ioc:
                    st.markdown("No indicators extracted.")

                st.markdown("**Source**")
                st.markdown(f"[Open article]({incident.get('url', '#')})")

                st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                st.markdown("**Threat actor profile**")
                st.markdown(
                    f"""
                    <div class="ai-box summary-text">
                        {format_ai_output(profile)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.info("Select an incident from the queue.")
            st.markdown("</div>", unsafe_allow_html=True)

        # =================================================
        # SUMMARY + TIMELINE
        # =================================================
        st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
        mid_left, mid_right = st.columns([1.3, 1], gap="large")

        with mid_left:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="section-kicker">Briefing</div>
                    <div class="section-title">Intelligence brief</div>
                    <div class="section-note">Structured analyst output for the current cycle.</div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="brief-box summary-text">
                    {brief.replace(chr(10), "<br>")}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)
            st.markdown("**Recommended actions**")
            for action in actions:
                st.markdown(f"<div class='recommendation-item'>• {action}</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with mid_right:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="section-kicker">Analysis</div>
                    <div class="section-title">AI summary</div>
                    <div class="section-note">Executive-style synthesis of current live reporting.</div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="ai-box summary-text">
                    {format_ai_output(ai_summary)}
                </div>
                """,
                unsafe_allow_html=True,
            )

            incident = st.session_state.selected_incident
            if incident:
                st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)
                st.markdown("**Timeline**")
                for item in generate_timeline(incident):
                    st.markdown(
                        f"""
                        <div class="timeline-item">
                            <div class="timeline-time">{item['time']}</div>
                            <div class="timeline-event">{item['event']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown("**Logs**")
                logs = generate_logs(incident)
                for log in logs:
                    log_class = "log-low"
                    if log["severity"] == "HIGH":
                        log_class = "log-high"
                    elif log["severity"] == "MEDIUM":
                        log_class = "log-medium"

                    st.markdown(
                        f"""
                        <div class="log-item {log_class}">
                            <strong>{log['time']}</strong><br>
                            {log['log']}<br>
                            <span style="color:#94a3b8;">MITRE: {log['mitre']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown("</div>", unsafe_allow_html=True)

        # =================================================
        # LOWER DATA LAYER
        # =================================================
        st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            ["Incidents", "MITRE", "IOC", "Entities", "Detections", "Live Feed"]
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
                st.dataframe(mapped_df, use_container_width=True, height=380)
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
                st.dataframe(mitre_df, use_container_width=True, height=240)
            else:
                st.info("No MITRE mappings identified.")

            st.markdown("### MITRE heatmap")
            heatmap_df = build_mitre_heatmap(filtered_events)
            if not heatmap_df.empty:
                st.dataframe(heatmap_df, use_container_width=True, height=240)
            else:
                st.info("No MITRE heatmap data available.")

        with tab3:
            ioc_df = build_ioc_table(filtered_events + filtered_unmapped)
            if not ioc_df.empty:
                st.dataframe(ioc_df, use_container_width=True, height=380)
            else:
                st.info("No indicators extracted from current reporting.")

        with tab4:
            people_df, org_df, location_df = build_entity_summary(filtered_events + filtered_unmapped)
            e1, e2, e3 = st.columns(3, gap="large")

            with e1:
                st.markdown("**People**")
                if not people_df.empty:
                    st.dataframe(people_df.head(15), use_container_width=True, height=280)
                else:
                    st.info("No people detected.")

            with e2:
                st.markdown("**Organisations**")
                if not org_df.empty:
                    st.dataframe(org_df.head(15), use_container_width=True, height=280)
                else:
                    st.info("No organisations detected.")

            with e3:
                st.markdown("**Locations**")
                if not location_df.empty:
                    st.dataframe(location_df.head(15), use_container_width=True, height=280)
                else:
                    st.info("No locations detected.")

        with tab5:
            incident = st.session_state.selected_incident
            if incident:
                detections = generate_kql_detections(incident)
                for detection in detections:
                    st.markdown(
                        f"""
                        <div class="glass-card-tight">
                            <div class="section-kicker">{detection['severity']} severity</div>
                            <div class="section-title">{detection['name']}</div>
                            <div class="section-note"><strong>MITRE:</strong> {detection['mitre']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.code(detection["kql"], language="kql")
            else:
                st.info("Select an incident to view simulated SIEM detections.")

        with tab6:
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
                            <div style="color:#475569; line-height:1.55;">{description}</div>
                            <div style="margin-top:0.6rem;">
                                <a href="{url}" target="_blank">Read full article</a>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No live articles retrieved. Add a NewsAPI key in Streamlit secrets to enable this feed.")

        # =================================================
        # TRENDS
        # =================================================
        history_df = load_history()
        if not history_df.empty:
            st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)
            st.markdown("### Threat trends")
            trend_df = (
                history_df.groupby("date")[["
