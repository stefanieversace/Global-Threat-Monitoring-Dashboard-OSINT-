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
# SESSION STATE
# =========================================================
if "selected_incident" not in st.session_state:
    st.session_state.selected_incident = None

if "incident_status" not in st.session_state:
    st.session_state.incident_status = {}

# =========================================================
# PREMIUM DARK UI
# =========================================================
st.markdown(
    """
    <style>
        .stApp {
            background-color: #0b0f14;
            color: #e5e7eb;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
        }

        .block-container {
            max-width: 1280px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        header, #MainMenu, footer {
            visibility: hidden;
        }

        section[data-testid="stSidebar"] {
            background: #0f172a;
            border-right: 1px solid #1f2937;
        }

        .hero-card {
            background: linear-gradient(135deg, #111827 0%, #0f172a 100%);
            border: 1px solid #1f2937;
            border-radius: 24px;
            padding: 1.6rem 1.7rem;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.28);
            margin-bottom: 1rem;
        }

        .hero-card h1 {
            margin: 0;
            font-size: 2.1rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: #f9fafb;
        }

        .hero-card p {
            margin: 0.55rem 0 0 0;
            color: #94a3b8;
            font-size: 1rem;
            line-height: 1.5;
        }

        .subtle-caption {
            color: #94a3b8;
            font-size: 0.92rem;
            margin-top: -0.1rem;
            margin-bottom: 1rem;
        }

        .panel {
            background: rgba(17, 24, 39, 0.92);
            border: 1px solid #1f2937;
            border-radius: 20px;
            padding: 1.15rem 1.2rem;
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.24);
            margin-bottom: 1rem;
        }

        .panel-soft {
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid #1e293b;
            border-radius: 20px;
            padding: 1.15rem 1.2rem;
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.20);
            margin-bottom: 1rem;
        }

        .section-kicker {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            color: #94a3b8;
            margin-bottom: 0.45rem;
            font-weight: 700;
        }

        .brief-content, .ai-content {
            font-size: 0.96rem;
            line-height: 1.75;
            color: #e5e7eb;
        }

        [data-testid="stMetric"] {
            background: rgba(17, 24, 39, 0.95);
            border: 1px solid #1f2937;
            border-radius: 18px;
            padding: 0.95rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
        }

        .alert-card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 16px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.65rem;
        }

        .alert-critical {
            border-left: 4px solid #ef4444;
        }

        .alert-warning {
            border-left: 4px solid #f59e0b;
        }

        .alert-info {
            border-left: 4px solid #3b82f6;
        }

        .recommendation-item {
            padding: 0.72rem 0.85rem;
            border-radius: 14px;
            background: #0f172a;
            border: 1px solid #1f2937;
            margin-bottom: 0.55rem;
            color: #e5e7eb;
        }

        .queue-button-wrap {
            margin-bottom: 0.45rem;
        }

        .timeline-item {
            background: #0f172a;
            border: 1px solid #1f2937;
            border-left: 4px solid #3b82f6;
            border-radius: 14px;
            padding: 0.8rem 0.9rem;
            margin-bottom: 0.6rem;
        }

        .log-item {
            background: #0f172a;
            border: 1px solid #1f2937;
            border-radius: 14px;
            padding: 0.8rem 0.9rem;
            margin-bottom: 0.5rem;
            font-size: 0.88rem;
        }

        .log-high {
            border-left: 4px solid #ef4444;
        }

        .log-medium {
            border-left: 4px solid #f59e0b;
        }

        .log-low {
            border-left: 4px solid #3b82f6;
        }

        .news-card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 18px;
            padding: 1rem;
            margin-bottom: 0.8rem;
        }

        .news-title {
            font-size: 1rem;
            font-weight: 700;
            color: #f9fafb;
            margin-bottom: 0.25rem;
        }

        .news-meta {
            font-size: 0.82rem;
            color: #94a3b8;
            margin-bottom: 0.5rem;
        }

        .pill {
            display: inline-block;
            padding: 0.28rem 0.68rem;
            border-radius: 999px;
            background: #172554;
            border: 1px solid #1d4ed8;
            color: #dbeafe;
            font-size: 0.78rem;
            font-weight: 600;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 16px;
            padding-bottom: 0.25rem;
        }

        .stTabs [data-baseweb="tab"] {
            color: #94a3b8;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 0.2rem 0.05rem 0.55rem 0.05rem;
        }

        .stTabs [aria-selected="true"] {
            color: #f9fafb !important;
            border-bottom: 2px solid #3b82f6;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid #1f2937;
            border-radius: 16px;
            overflow: hidden;
        }

        iframe {
            border-radius: 18px !important;
        }

        .sidebar-note {
            font-size: 0.84rem;
            color: #94a3b8;
            line-height: 1.5;
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
    <div class="hero-card">
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
    '<div class="subtle-caption">Live monitoring • triage • MITRE mapping • IOC extraction • incident workflow</div>',
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
    html_text = html_text.replace("Key Developments", "<strong>Key Developments</strong>")
    html_text = html_text.replace("Risk Assessment", "<strong>Risk Assessment</strong>")
    html_text = html_text.replace("Analyst Insight", "<strong>Analyst Insight</strong>")
    html_text = html_text.replace("Profile Summary", "<strong>Profile Summary</strong>")
    html_text = html_text.replace("Likely Objectives", "<strong>Likely Objectives</strong>")
    html_text = html_text.replace("Observed Techniques", "<strong>Observed Techniques</strong>")
    html_text = html_text.replace("Assessment", "<strong>Assessment</strong>")
    return html_text

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

        category = event.get("category", "General")
        rows.append(
            {
                "Technique": mitre_value,
                "Category": category,
                "Count": 1,
            }
        )

    if not rows:
        return pd.DataFrame()

    mitre_df = pd.DataFrame(rows)
    heatmap_df = mitre_df.pivot_table(
        index="Technique",
        columns="Category",
        values="Count",
        aggfunc="sum",
        fill_value=0
    )

    return heatmap_df

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
    else:
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

    live_news_query = st.text_input(
        "Search topics",
        value="cyber attack, protest, conflict, ransomware, breach, disruption",
    )

    st.markdown("---")
    st.markdown(
        '<div class="sidebar-note">Refine the monitoring scope, then generate a fresh intelligence cycle.</div>',
        unsafe_allow_html=True,
    )

watchlist_terms = [term.strip() for term in watchlist_input.split(",") if term.strip()]
news_query = " OR ".join([q.strip() for q in live_news_query.split(",") if q.strip()]) or DEFAULT_NEWS_QUERY

# =========================================================
# MAIN
# =========================================================
if st.button("Generate Intelligence Brief", use_container_width=True):
    try:
        brief, mapped_events, unmapped_articles, summary = generate_brief(
            max_articles=max_articles,
            watchlist_terms=watchlist_terms,
        )

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

        # =================================================
        # SNAPSHOT
        # =================================================
        st.markdown("### Monitoring Snapshot")
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        s1.metric("High Risk", high_count)
        s2.metric("Medium Risk", medium_count)
        s3.metric("Low Risk", low_count)
        s4.metric("Priority Score", priority_score)
        s5.metric("Top Region", top_region)
        s6.metric("Confidence", confidence)

        st.markdown("")
        render_alerts(alerts)

        # =================================================
        # BRIEF / AI SUMMARY
        # =================================================
        top_left, top_right = st.columns([1.15, 1], gap="large")

        with top_left:
            st.markdown("### Intelligence Brief")
            st.markdown(
                f"""
                <div class="panel brief-content">
                    {brief.replace(chr(10), "<br>")}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with top_right:
            st.markdown("### AI Summary")
            st.markdown(
                f"""
                <div class="panel-soft ai-content">
                    {format_ai_output(ai_summary)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        lower_left, lower_right = st.columns([1, 1], gap="large")

        with lower_left:
            st.markdown("### Recommended Actions")
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            for action in actions:
                st.markdown(f'<div class="recommendation-item">• {action}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with lower_right:
            st.markdown("### Key Judgements")
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            if key_judgements:
                for idx, judgement in enumerate(key_judgements[:3], start=1):
                    st.markdown(f"**{idx}.** {judgement}")
            else:
                st.markdown("No key judgements were returned for this cycle.")
            st.markdown("</div>", unsafe_allow_html=True)

        # =================================================
        # MAP
        # =================================================
        st.markdown("### Global Map")
        st.markdown('<div class="panel">', unsafe_allow_html=True)

        threat_map = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
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
                color = "#ef4444"
            elif event.get("risk") == "MEDIUM":
                color = "#f59e0b"
            else:
                color = "#3b82f6"

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

        # =================================================
        # TABS
        # =================================================
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
            [
                "Queue",
                "Incidents",
                "MITRE",
                "IOC",
                "Entities",
                "Live Feed",
                "Timeline",
                "Detections",
            ]
        )

        # -------------------------------------------------
        # TAB 1 — QUEUE + DRILL-DOWN
        # -------------------------------------------------
        with tab1:
            st.markdown("### Alert Triage Queue")
            triage_df = build_triage_queue(filtered_events)

            queue_col, detail_col = st.columns([1, 1.6], gap="large")

            with queue_col:
                if not triage_df.empty:
                    st.dataframe(triage_df, use_container_width=True, height=320)

                    st.markdown("### Open Incident")
                    for i, event in enumerate(filtered_events[:12]):
                        risk = event.get("risk", "LOW")
                        emoji = "🟢"
                        if risk == "HIGH":
                            emoji = "🔴"
                        elif risk == "MEDIUM":
                            emoji = "🟠"

                        label = f"{emoji} {event.get('title', 'Untitled')[:80]}"
                        if st.button(label, key=f"triage_open_{i}", use_container_width=True):
                            st.session_state.selected_incident = event
                else:
                    st.info("No incidents available for triage.")

            with detail_col:
                st.markdown("### Investigation Panel")
                incident = st.session_state.selected_incident

                if incident:
                    logs = generate_logs(incident)
                    severity_level = calculate_incident_severity(logs)
                    profile = generate_threat_actor_profile(incident)
                    incident_id = incident.get("title", "Untitled")

                    st.markdown(
                        f"""
                        <div class="panel">
                            <div class="section-kicker">Overview</div>
                            <div><strong>{incident.get("title", "Untitled")}</strong></div><br>
                            <div><strong>Location:</strong> {incident.get("location", "N/A")}</div>
                            <div><strong>Region:</strong> {incident.get("region", "N/A")}</div>
                            <div><strong>Risk:</strong> {incident.get("risk", "N/A")}</div>
                            <div><strong>Category:</strong> {incident.get("category", "N/A")}</div>
                            <div><strong>Confidence:</strong> {incident.get("confidence", "N/A")}</div>
                            <div><strong>Calculated Severity:</strong> {severity_level}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("#### Incident Workflow")
                    current_status = st.session_state.incident_status.get(incident_id, "New")
                    st.markdown(f"**Status:** {current_status}")

                    w1, w2, w3 = st.columns(3)
                    if w1.button("Investigate", key=f"investigate_{incident_id}"):
                        st.session_state.incident_status[incident_id] = "Investigating"
                    if w2.button("Escalate", key=f"escalate_{incident_id}"):
                        st.session_state.incident_status[incident_id] = "Escalated"
                    if w3.button("Resolve", key=f"resolve_{incident_id}"):
                        st.session_state.incident_status[incident_id] = "Resolved"

                    st.markdown("#### MITRE Mapping")
                    st.markdown(f"• {incident.get('mitre', 'N/A')}")

                    st.markdown("#### Business Impact")
                    impacts = incident.get("business_impact", [])
                    if impacts:
                        for impact in impacts:
                            st.markdown(f'<span class="pill">{impact}</span>', unsafe_allow_html=True)
                    else:
                        st.markdown("No business impact tags available.")

                    st.markdown("#### Indicators of Compromise")
                    iocs = incident.get("iocs", {})
                    has_iocs = False
                    for k, v in iocs.items():
                        if v:
                            has_iocs = True
                            st.markdown(f"**{k.upper()}**")
                            for item in v[:3]:
                                st.markdown(f"- {item}")
                    if not has_iocs:
                        st.markdown("No indicators extracted from current incident context.")

                    st.markdown("#### Entities")
                    entities = incident.get("entities", {})
                    has_entities = False
                    for group in ["people", "orgs", "locations"]:
                        if entities.get(group):
                            has_entities = True
                            st.markdown(f"**{group.capitalize()}**")
                            for entity in entities[group][:3]:
                                st.markdown(f"- {entity}")
                    if not has_entities:
                        st.markdown("No entities extracted from this incident.")

                    st.markdown("#### Threat Actor Profile")
                    st.markdown(
                        f"""
                        <div class="panel-soft ai-content">
                            {format_ai_output(profile)}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("#### Recommended Actions")
                    drill_actions = generate_recommendations([incident], 1, 0)
                    for action in drill_actions:
                        st.markdown(f"• {action}")

                    st.markdown("#### Source")
                    st.markdown(f"[Open Article]({incident.get('url', '#')})")
                else:
                    st.info("Select an incident from the queue to begin investigation.")

        # -------------------------------------------------
        # TAB 2 — INCIDENTS
        # -------------------------------------------------
        with tab2:
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

        # -------------------------------------------------
        # TAB 3 — MITRE
        # -------------------------------------------------
        with tab3:
            st.markdown("### MITRE Mapping")

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
                st.dataframe(mitre_df, use_container_width=True, height=280)
            else:
                st.info("No MITRE mappings identified.")

            st.markdown("### MITRE Heatmap")
            heatmap_df = build_mitre_heatmap(filtered_events)
            if not heatmap_df.empty:
                st.dataframe(heatmap_df, use_container_width=True, height=260)
            else:
                st.info("No MITRE heatmap data available.")

        # -------------------------------------------------
        # TAB 4 — IOC
        # -------------------------------------------------
        with tab4:
            ioc_df = build_ioc_table(filtered_events + filtered_unmapped)
            if not ioc_df.empty:
                st.dataframe(ioc_df, use_container_width=True, height=430)
            else:
                st.info("No indicators extracted from current reporting.")

        # -------------------------------------------------
        # TAB 5 — ENTITIES
        # -------------------------------------------------
        with tab5:
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

        # -------------------------------------------------
        # TAB 6 — LIVE FEED
        # -------------------------------------------------
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

        # -------------------------------------------------
        # TAB 7 — TIMELINE
        # -------------------------------------------------
        with tab7:
            incident = st.session_state.selected_incident
            if incident:
                st.markdown("### Incident Timeline")
                timeline = generate_timeline(incident)

                for step in timeline:
                    st.markdown(
                        f"""
                        <div class="timeline-item">
                            <strong>{step['time']}</strong><br>
                            {step['event']}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown("### Event Logs")
                logs = generate_logs(incident)
                severity_level = calculate_incident_severity(logs)
                st.markdown(f"**Calculated Severity:** {severity_level}")

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
            else:
                st.info("Select an incident from the queue to view timeline and logs.")

        # -------------------------------------------------
        # TAB 8 — DETECTIONS
        # -------------------------------------------------
        with tab8:
            st.markdown("### SIEM Detections")

            if st.session_state.selected_incident:
                detections = generate_kql_detections(st.session_state.selected_incident)

                for detection in detections:
                    st.markdown(
                        f"""
                        <div class="panel-soft">
                            <div class="section-kicker">{detection['severity']} Severity</div>
                            <strong>{detection['name']}</strong><br><br>
                            <strong>MITRE:</strong> {detection['mitre']}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.code(detection["kql"], language="kql")
            else:
                st.info("Select an incident from the queue to view simulated SIEM detections.")

        # -------------------------------------------------
        # TRENDS
        # -------------------------------------------------
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
        <div class="panel">
            <div class="section-kicker">Ready</div>
            <div style="font-size:1rem; color:#cbd5e1; line-height:1.7;">
                Use the controls in the sidebar, then click <strong>Generate Intelligence Brief</strong>
                to run a fresh monitoring cycle.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
