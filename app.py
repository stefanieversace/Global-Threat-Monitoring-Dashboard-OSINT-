import os
import re
import math
import json
import textwrap
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import pydeck as pdk
import requests
import streamlit as st

NEWSAPI_KEY = st.secrets.get("NEWSAPI_KEY") or os.getenv("NEWSAPI_KEY")

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Global Threat Monitoring Dashboard",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# STYLING
# =========================================================
st.markdown(
    """
    <style>
    :root {
        --bg: #0a0a0f;
        --panel: #11131a;
        --panel-2: #161923;
        --panel-3: rgba(255,255,255,0.04);
        --text: #f5f7fb;
        --muted: #98a2b3;
        --border: rgba(255,255,255,0.08);
        --accent: #8ab4ff;
        --accent-2: #6ea8fe;
        --danger: #ff6b6b;
        --warn: #ffd166;
        --success: #7bd389;
    }

    html, body, [class*="css"] {
        background: linear-gradient(180deg, #08090c 0%, #0d1017 100%);
        color: var(--text);
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(138,180,255,0.08), transparent 30%),
            radial-gradient(circle at top right, rgba(123,211,137,0.05), transparent 22%),
            linear-gradient(180deg, #08090c 0%, #0d1017 100%);
    }

    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        margin-bottom: 0.15rem;
    }

    .sub-title {
        color: var(--muted);
        font-size: 1rem;
        margin-bottom: 1.3rem;
    }

    .glass-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.02));
        border: 1px solid var(--border);
        border-radius: 22px;
        padding: 1rem 1.1rem;
        box-shadow: 0 12px 28px rgba(0,0,0,0.24);
        backdrop-filter: blur(10px);
    }

    .metric-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.02));
        border: 1px solid var(--border);
        border-radius: 22px;
        padding: 1rem 1.1rem;
        min-height: 110px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }

    .metric-label {
        color: var(--muted);
        font-size: 0.82rem;
        margin-bottom: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.04em;
    }

    .metric-sub {
        color: var(--muted);
        font-size: 0.88rem;
        margin-top: 0.25rem;
    }

    .pill {
        display: inline-block;
        padding: 0.25rem 0.55rem;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 600;
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.04);
        margin-right: 0.3rem;
        margin-bottom: 0.35rem;
    }

    .pill-high {
        color: #ffd7d7;
        background: rgba(255,107,107,0.14);
        border: 1px solid rgba(255,107,107,0.28);
    }

    .pill-medium {
        color: #ffebbf;
        background: rgba(255,209,102,0.14);
        border: 1px solid rgba(255,209,102,0.26);
    }

    .pill-low {
        color: #d8ffe4;
        background: rgba(123,211,137,0.14);
        border: 1px solid rgba(123,211,137,0.26);
    }

    .section-title {
        font-size: 1.15rem;
        font-weight: 650;
        margin-bottom: 0.8rem;
        letter-spacing: -0.02em;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #0b0f15 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(180deg, #1a1f2a, #121720);
        color: white !important;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        font-weight: 600;
        padding: 0.62rem 1rem;
        box-shadow: 0 6px 16px rgba(0,0,0,0.18);
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: rgba(138,180,255,0.35);
        color: white !important;
    }

    div[data-baseweb="select"] > div,
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stMultiSelect [data-baseweb="tag"],
    .stNumberInput input {
        background: #121720 !important;
        color: white !important;
        border-radius: 12px !important;
    }

    .small-muted {
        color: var(--muted);
        font-size: 0.85rem;
    }

    .log-box {
        background: #0f131b;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 0.85rem 1rem;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.84rem;
        white-space: pre-wrap;
        line-height: 1.5;
    }

    .divider-space {
        height: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CONFIG / ENV
# =========================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

NEWS_QUERY_DEFAULT = (
    '("cyber attack" OR breach OR ransomware OR hack OR malware OR '
    '"civil unrest" OR protest OR riot OR terrorism OR "supply chain" OR '
    '"data leak" OR espionage OR sabotage OR violence OR kidnapping)'
)

MAX_ARTICLES_DEFAULT = 80

COUNTRY_COORDS: Dict[str, Tuple[float, float, str]] = {
    "united states": (37.0902, -95.7129, "North America"),
    "usa": (37.0902, -95.7129, "North America"),
    "new york": (40.7128, -74.0060, "North America"),
    "washington": (38.9072, -77.0369, "North America"),
    "california": (36.7783, -119.4179, "North America"),
    "united kingdom": (55.3781, -3.4360, "Europe"),
    "uk": (55.3781, -3.4360, "Europe"),
    "england": (52.3555, -1.1743, "Europe"),
    "london": (51.5072, -0.1276, "Europe"),
    "france": (46.2276, 2.2137, "Europe"),
    "paris": (48.8566, 2.3522, "Europe"),
    "germany": (51.1657, 10.4515, "Europe"),
    "berlin": (52.5200, 13.4050, "Europe"),
    "italy": (41.8719, 12.5674, "Europe"),
    "rome": (41.9028, 12.4964, "Europe"),
    "ukraine": (48.3794, 31.1656, "Europe"),
    "russia": (61.5240, 105.3188, "Europe/Asia"),
    "moscow": (55.7558, 37.6173, "Europe"),
    "israel": (31.0461, 34.8516, "Middle East"),
    "gaza": (31.3547, 34.3088, "Middle East"),
    "iran": (32.4279, 53.6880, "Middle East"),
    "tehran": (35.6892, 51.3890, "Middle East"),
    "saudi arabia": (23.8859, 45.0792, "Middle East"),
    "uae": (23.4241, 53.8478, "Middle East"),
    "dubai": (25.2048, 55.2708, "Middle East"),
    "china": (35.8617, 104.1954, "Asia-Pacific"),
    "beijing": (39.9042, 116.4074, "Asia-Pacific"),
    "taiwan": (23.6978, 120.9605, "Asia-Pacific"),
    "japan": (36.2048, 138.2529, "Asia-Pacific"),
    "tokyo": (35.6762, 139.6503, "Asia-Pacific"),
    "south korea": (35.9078, 127.7669, "Asia-Pacific"),
    "seoul": (37.5665, 126.9780, "Asia-Pacific"),
    "india": (20.5937, 78.9629, "Asia-Pacific"),
    "delhi": (28.6139, 77.2090, "Asia-Pacific"),
    "pakistan": (30.3753, 69.3451, "Asia-Pacific"),
    "afghanistan": (33.9391, 67.7100, "Asia-Pacific"),
    "australia": (-25.2744, 133.7751, "Asia-Pacific"),
    "sydney": (-33.8688, 151.2093, "Asia-Pacific"),
    "melbourne": (-37.8136, 144.9631, "Asia-Pacific"),
    "singapore": (1.3521, 103.8198, "Asia-Pacific"),
    "indonesia": (-0.7893, 113.9213, "Asia-Pacific"),
    "jakarta": (-6.2088, 106.8456, "Asia-Pacific"),
    "philippines": (12.8797, 121.7740, "Asia-Pacific"),
    "manila": (14.5995, 120.9842, "Asia-Pacific"),
    "nigeria": (9.0820, 8.6753, "Africa"),
    "sudan": (12.8628, 30.2176, "Africa"),
    "south africa": (-30.5595, 22.9375, "Africa"),
    "johannesburg": (-26.2041, 28.0473, "Africa"),
    "kenya": (-0.0236, 37.9062, "Africa"),
    "somalia": (5.1521, 46.1996, "Africa"),
    "brazil": (-14.2350, -51.9253, "Latin America"),
    "rio de janeiro": (-22.9068, -43.1729, "Latin America"),
    "mexico": (23.6345, -102.5528, "Latin America"),
    "mexico city": (19.4326, -99.1332, "Latin America"),
    "canada": (56.1304, -106.3468, "North America"),
    "toronto": (43.6532, -79.3832, "North America"),
}

THREAT_ACTOR_MAP = {
    "apt29": {
        "aliases": ["cozy bear", "midnight blizzard"],
        "motivation": "espionage",
        "typical_targets": "government, diplomatic, strategic sectors",
        "ttps": ["credential theft", "phishing", "cloud abuse", "persistence"],
    },
    "apt28": {
        "aliases": ["fancy bear", "forest blizzard"],
        "motivation": "espionage / influence operations",
        "typical_targets": "government, defence, media",
        "ttps": ["phishing", "credential access", "malware deployment"],
    },
    "lazarus": {
        "aliases": ["hidden cobra"],
        "motivation": "financial theft / espionage",
        "typical_targets": "crypto, financial, software supply chain",
        "ttps": ["malware", "social engineering", "crypto compromise"],
    },
    "lockbit": {
        "aliases": [],
        "motivation": "financial extortion",
        "typical_targets": "enterprise, public sector, critical infrastructure",
        "ttps": ["ransomware", "data theft", "double extortion"],
    },
    "cl0p": {
        "aliases": ["clop"],
        "motivation": "financial extortion",
        "typical_targets": "large enterprises via file transfer vulnerabilities",
        "ttps": ["mass exploitation", "data theft", "extortion"],
    },
    "scattered spider": {
        "aliases": ["octo tempest", "0ktapus"],
        "motivation": "financial theft / disruptive intrusion",
        "typical_targets": "identity providers, telecom, BPO, hospitality",
        "ttps": ["help-desk social engineering", "MFA bypass", "ransomware enablement"],
    },
    "sandworm": {
        "aliases": [],
        "motivation": "disruption / destructive operations",
        "typical_targets": "critical infrastructure, energy, government",
        "ttps": ["ICS targeting", "wipers", "destructive malware"],
    },
    "anonymous": {
        "aliases": [],
        "motivation": "hacktivism",
        "typical_targets": "public-facing targets",
        "ttps": ["DDoS", "defacement", "data leakage"],
    },
    "hamas": {
        "aliases": [],
        "motivation": "militant / political violence",
        "typical_targets": "civilian / state targets",
        "ttps": ["kinetic attacks", "propaganda"],
    },
    "isis": {
        "aliases": ["isil", "daesh"],
        "motivation": "terrorism",
        "typical_targets": "civilian / state targets",
        "ttps": ["terror attacks", "propaganda"],
    },
}

MITRE_MAP = {
    "ransomware": ["TA0040 Impact", "T1486 Data Encrypted for Impact"],
    "phishing": ["TA0001 Initial Access", "T1566 Phishing"],
    "credential": ["TA0006 Credential Access", "T1110 Brute Force", "T1078 Valid Accounts"],
    "malware": ["TA0002 Execution", "TA0003 Persistence", "T1059 Command and Scripting Interpreter"],
    "ddos": ["TA0040 Impact", "T1498 Network Denial of Service"],
    "data leak": ["TA0010 Exfiltration", "T1041 Exfiltration Over C2 Channel"],
    "exploit": ["TA0001 Initial Access", "T1190 Exploit Public-Facing Application"],
    "social engineering": ["TA0001 Initial Access", "T1566 Phishing"],
    "protest": ["Physical / Operational Risk", "Crowd disruption / movement risk"],
    "riot": ["Physical / Operational Risk", "Civil disorder"],
    "terror": ["Physical Security Threat", "Mass casualty / high-impact incident"],
    "espionage": ["TA0009 Collection", "TA0010 Exfiltration"],
    "supply chain": ["TA0001 Initial Access", "T1195 Supply Chain Compromise"],
}


# =========================================================
# HELPERS
# =========================================================
def utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def safe_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", utc=True)


def clean_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def shorten(text: str, width: int = 180) -> str:
    return textwrap.shorten(clean_text(text), width=width, placeholder="...")


def normalize_lower(text: str) -> str:
    return clean_text(text).lower()


def parse_source_name(source: dict) -> str:
    if isinstance(source, dict):
        return clean_text(source.get("name", "Unknown Source"))
    return "Unknown Source"


def article_text_blob(row: pd.Series) -> str:
    return " ".join(
        [
            clean_text(row.get("title")),
            clean_text(row.get("description")),
            clean_text(row.get("content")),
            clean_text(row.get("source")),
        ]
    ).strip()


def get_risk_score_and_label(text: str) -> Tuple[int, str]:
    t = normalize_lower(text)
    score = 10

    high_terms = {
        "terror": 42,
        "terrorist": 42,
        "explosion": 38,
        "missile": 34,
        "airstrike": 36,
        "hostage": 38,
        "kidnap": 36,
        "shooting": 38,
        "dead": 24,
        "killed": 24,
        "wounded": 18,
        "riot": 26,
        "civil unrest": 24,
        "ransomware": 28,
        "critical infrastructure": 30,
        "wiper": 30,
        "breach": 26,
        "data leak": 24,
        "exfiltration": 28,
        "espionage": 24,
        "sabotage": 30,
        "lockbit": 28,
        "lazarus": 28,
        "apt29": 25,
        "apt28": 25,
        "sandworm": 30,
    }
    medium_terms = {
        "phishing": 14,
        "malware": 16,
        "cyber attack": 20,
        "attack": 16,
        "hack": 16,
        "ddos": 15,
        "exploit": 16,
        "vulnerability": 12,
        "credential": 12,
        "protest": 12,
        "disruption": 12,
        "fraud": 10,
        "social engineering": 14,
        "outage": 10,
    }
    low_terms = {
        "advisory": 2,
        "warning": 4,
        "monitoring": 3,
        "investigation": 4,
    }

    for term, points in high_terms.items():
        if term in t:
            score += points
    for term, points in medium_terms.items():
        if term in t:
            score += points
    for term, points in low_terms.items():
        if term in t:
            score += points

    if re.search(r"\b\d+\s+(dead|killed|injured|wounded)\b", t):
        score += 18

    score = max(1, min(score, 100))

    if score >= 70:
        return score, "High"
    if score >= 40:
        return score, "Medium"
    return score, "Low"


def detect_primary_category(text: str) -> str:
    t = normalize_lower(text)
    category_keywords = {
        "Cyber": [
            "cyber", "breach", "ransomware", "phishing", "malware", "ddos", "exploit",
            "vulnerability", "credential", "data leak", "exfiltration", "intrusion"
        ],
        "Civil Unrest": ["protest", "riot", "civil unrest", "demonstration", "clashes"],
        "Terrorism / Violence": ["terror", "terrorist", "shooting", "explosion", "hostage", "kidnap"],
        "Espionage": ["espionage", "spy", "intelligence operation"],
        "Supply Chain": ["supply chain", "vendor compromise", "third-party"],
        "Disinformation / Influence": ["disinformation", "influence operation", "propaganda"],
    }
    for category, keywords in category_keywords.items():
        if any(k in t for k in keywords):
            return category
    return "General Threat"


def extract_threat_actors(text: str) -> List[str]:
    t = normalize_lower(text)
    found = []
    for actor, profile in THREAT_ACTOR_MAP.items():
        names = [actor] + profile.get("aliases", [])
        if any(name in t for name in names):
            found.append(actor.title())
    return found


def build_actor_profile(actors: List[str]) -> str:
    if not actors:
        return "No named threat actor identified from the article text. Monitor for tradecraft, victimology, and campaign overlap."
    blocks = []
    for actor in actors[:3]:
        key = actor.lower()
        data = THREAT_ACTOR_MAP.get(key, {})
        aliases = ", ".join(data.get("aliases", [])) if data.get("aliases") else "None listed"
        blocks.append(
            f"**{actor}**\n"
            f"- Aliases: {aliases}\n"
            f"- Motivation: {data.get('motivation', 'Unknown')}\n"
            f"- Typical targets: {data.get('typical_targets', 'Unknown')}\n"
            f"- Likely TTPs: {', '.join(data.get('ttps', [])) if data.get('ttps') else 'Unknown'}"
        )
    return "\n\n".join(blocks)


def extract_location(text: str) -> Tuple[Optional[str], Optional[float], Optional[float], str]:
    t = normalize_lower(text)
    matches = []

    for place, (lat, lon, region) in COUNTRY_COORDS.items():
        pattern = r"\b" + re.escape(place) + r"\b"
        if re.search(pattern, t):
            matches.append((place.title(), lat, lon, region))

    if matches:
        matches = sorted(matches, key=lambda x: len(x[0]), reverse=True)
        return matches[0]

    # simple title-case heuristic fallback
    title_case_hits = re.findall(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})\b", text)
    filtered_hits = [
        h for h in title_case_hits
        if h.lower() not in {"The", "Breaking", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
    ]
    if filtered_hits:
        return filtered_hits[0], None, None, "Unknown"
    return None, None, None, "Unknown"


def extract_keywords(text: str) -> List[str]:
    t = normalize_lower(text)
    terms = [
        "ransomware", "phishing", "malware", "ddos", "credential theft", "exploit",
        "data leak", "breach", "civil unrest", "riot", "terrorism", "espionage",
        "supply chain", "social engineering", "cloud", "critical infrastructure",
        "disinformation", "wiper", "hostage", "explosion"
    ]
    found = [term for term in terms if term in t]
    return found[:8]


def map_mitre(text: str) -> List[str]:
    t = normalize_lower(text)
    findings = []
    for key, mapped in MITRE_MAP.items():
        if key in t:
            findings.extend(mapped)
    deduped = []
    for item in findings:
        if item not in deduped:
            deduped.append(item)
    return deduped[:6]


def generate_simulated_logs(row: pd.Series) -> List[str]:
    title = clean_text(row.get("title"))
    source = clean_text(row.get("source"))
    severity = clean_text(row.get("risk"))
    score = row.get("risk_score", 0)
    detected_at = row.get("published_dt")
    detected_str = detected_at.strftime("%Y-%m-%d %H:%M:%S UTC") if pd.notna(detected_at) else utc_now_str()
    category = clean_text(row.get("category"))
    location = clean_text(row.get("location")) or "Unknown"
    mitre = row.get("mitre", [])

    lines = [
        f"[{detected_str}] INFO  Feed ingest completed | source={source}",
        f"[{detected_str}] INFO  Article normalized | category={category} | geo={location}",
        f"[{detected_str}] WARN  Threat scoring engine triggered | score={score} | severity={severity}",
    ]

    if "Cyber" in category:
        lines.extend([
            f"[{detected_str}] ALERT Detection matched suspicious external reporting pattern",
            f"[{detected_str}] ALERT IOC enrichment simulated | status=partial | confidence=medium",
        ])
    if "Civil Unrest" in category or "Terrorism" in category:
        lines.extend([
            f"[{detected_str}] ALERT Physical security watchlist hit | travel_risk=elevated",
            f"[{detected_str}] ALERT Event disruption logic triggered | posture=review",
        ])

    if mitre:
        for m in mitre[:3]:
            lines.append(f"[{detected_str}] INFO  MITRE mapped | technique={m}")

    lines.append(f"[{detected_str}] INFO  Case stub created | title={shorten(title, 90)}")
    return lines


def build_kql_queries(row: pd.Series) -> str:
    category = clean_text(row.get("category"))
    keywords = row.get("keywords", [])
    actors = row.get("threat_actors", [])
    risk = clean_text(row.get("risk"))
    location = clean_text(row.get("location"))

    base_queries = []

    if category == "Cyber":
        base_queries.append(
            """// Suspicious sign-ins with geolocation anomaly
SigninLogs
| where TimeGenerated > ago(24h)
| where ResultType != 0
| summarize FailedAttempts=count() by UserPrincipalName, IPAddress, Location, bin(TimeGenerated, 1h)
| where FailedAttempts >= 5
| order by FailedAttempts desc"""
        )
        base_queries.append(
            """// Potential phishing / malicious URL activity
EmailUrlInfo
| where TimeGenerated > ago(24h)
| where Url has_any ("login", "verify", "reset", "secure", "auth")
| summarize Count=count() by UrlDomain, NetworkMessageId
| order by Count desc"""
        )
        base_queries.append(
            """// Endpoint execution anomalies
DeviceProcessEvents
| where TimeGenerated > ago(24h)
| where ProcessCommandLine has_any ("powershell", "cmd.exe", "wscript", "rundll32", "certutil")
| project TimeGenerated, DeviceName, InitiatingProcessAccountName, FileName, ProcessCommandLine
| order by TimeGenerated desc"""
        )

    if "phishing" in keywords or "credential theft" in keywords:
        base_queries.append(
            """// MFA fatigue / account takeover signals
SigninLogs
| where TimeGenerated > ago(24h)
| summarize Attempts=count(), Countries=dcount(Location) by UserPrincipalName
| where Attempts > 10 or Countries > 2
| order by Attempts desc"""
        )

    if "ransomware" in keywords:
        base_queries.append(
            """// Mass file modification / encryption-like activity
DeviceFileEvents
| where TimeGenerated > ago(12h)
| summarize FileOps=count() by DeviceName, InitiatingProcessAccountName, bin(TimeGenerated, 15m)
| where FileOps > 500
| order by FileOps desc"""
        )

    if category in {"Civil Unrest", "Terrorism / Violence"}:
        base_queries.append(
            f"""// Travel / facility risk watchlist correlation
SecurityAlert
| where TimeGenerated > ago(48h)
| extend RegionHint = "{location}"
| project TimeGenerated, AlertName, Severity, Entities, RegionHint
| order by TimeGenerated desc"""
        )

    if actors:
        actor_hint = ", ".join(actors)
        base_queries.append(
            f"""// Threat intel hunt using actor context
ThreatIntelligenceIndicator
| where TimeGenerated > ago(30d)
| extend ActorContext = "{actor_hint}"
| project TimeGenerated, Description, ThreatType, ConfidenceScore, ActorContext
| order by TimeGenerated desc"""
        )

    if risk == "High":
        base_queries.append(
            """// Escalation-ready high-severity alerts
SecurityAlert
| where TimeGenerated > ago(24h)
| where Severity in ("High", "Medium")
| project TimeGenerated, AlertName, Severity, CompromisedEntity, VendorName
| order by TimeGenerated desc"""
        )

    if not base_queries:
        base_queries.append(
            """// General threat hunting pivot
SecurityEvent
| where TimeGenerated > ago(24h)
| summarize EventCount=count() by Computer, EventID, bin(TimeGenerated, 1h)
| order by EventCount desc"""
        )

    return "\n\n".join(base_queries[:5])


def generate_local_incident_report(row: pd.Series) -> str:
    title = clean_text(row.get("title"))
    source = clean_text(row.get("source"))
    risk = clean_text(row.get("risk"))
    score = row.get("risk_score")
    category = clean_text(row.get("category"))
    location = clean_text(row.get("location")) or "Unknown"
    actors = row.get("threat_actors", [])
    keywords = row.get("keywords", [])
    mitre = row.get("mitre", [])

    return f"""
### Executive Summary
This incident was ingested from **{source}** and assessed as **{risk} risk** with a severity score of **{score}/100**. The event is categorised as **{category}** and is associated with **{location}**.

### Incident Overview
**Title:** {title}

**Observed indicators/themes:** {", ".join(keywords) if keywords else "No strong indicator keywords extracted."}

**Named threat actors:** {", ".join(actors) if actors else "No named actor detected from article text."}

### Analyst Assessment
This reporting suggests a credible event or emerging signal that may affect operations, personnel safety, digital assets, or travel posture depending on organisational exposure to the affected geography and sector.

### MITRE / Tradecraft Mapping
{chr(10).join([f"- {m}" for m in mitre]) if mitre else "- No clear ATT&CK mapping inferred from the text."}

### Recommended Actions
- Validate whether organisational personnel, offices, vendors, or clients are exposed to the affected location or sector.
- Review relevant detections, watchlists, and access activity for related patterns.
- Increase monitoring for follow-on activity and update the operating picture.
- Escalate to incident management if additional corroboration emerges.

### Confidence
**Moderate** — based on open-source reporting and keyword/entity extraction. Human review recommended.
""".strip()


def generate_openai_incident_report(row: pd.Series, api_key: str, model: str) -> str:
    prompt = f"""
You are a senior security intelligence analyst. Write a polished incident report for a threat monitoring dashboard.

Return markdown with these exact headings:
### Executive Summary
### Incident Overview
### Threat Actor Analysis
### MITRE / TTP Mapping
### Operational Impact
### Recommended Actions
### Confidence

Incident data:
- Title: {clean_text(row.get("title"))}
- Source: {clean_text(row.get("source"))}
- Published: {row.get("published_dt")}
- Risk: {clean_text(row.get("risk"))}
- Risk Score: {row.get("risk_score")}
- Category: {clean_text(row.get("category"))}
- Location: {clean_text(row.get("location"))}
- Region: {clean_text(row.get("region"))}
- Keywords: {", ".join(row.get("keywords", []))}
- Threat Actors: {", ".join(row.get("threat_actors", []))}
- MITRE Mapping: {", ".join(row.get("mitre", []))}
- Description: {clean_text(row.get("description"))}
- Content: {clean_text(row.get("content"))}

Requirements:
- Be concise but high quality.
- Use professional intelligence language.
- If information is uncertain, say so clearly.
- Do not invent facts beyond reasonable inference.
""".strip()

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise senior intelligence analyst."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=45)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def assign_default_analyst(score: int) -> str:
    if score >= 70:
        return "L2 SOC Analyst"
    if score >= 40:
        return "Threat Intelligence Analyst"
    return "Monitoring Queue"


def rank_priority(row: pd.Series) -> int:
    base = int(row.get("risk_score", 0))
    recent_bonus = 0
    published = row.get("published_dt")
    if pd.notna(published):
        age_hours = (datetime.now(timezone.utc) - published.to_pydatetime()).total_seconds() / 3600
        if age_hours <= 6:
            recent_bonus = 12
        elif age_hours <= 24:
            recent_bonus = 6
    actor_bonus = 10 if row.get("threat_actors") else 0
    geo_bonus = 6 if clean_text(row.get("location")) else 0
    return min(100, base + recent_bonus + actor_bonus + geo_bonus)


def format_risk_pill(risk: str) -> str:
    risk = clean_text(risk)
    cls = "pill-low"
    if risk == "High":
        cls = "pill-high"
    elif risk == "Medium":
        cls = "pill-medium"
    return f'<span class="pill {cls}">{risk}</span>'


# =========================================================
# DATA FETCH
# =========================================================
@st.cache_data(ttl=900, show_spinner=False)
def fetch_news(query: str, max_articles: int = 80) -> pd.DataFrame:
    if not NEWSAPI_KEY:
        return pd.DataFrame()

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": min(max_articles, 100),
        "apiKey": NEWSAPI_KEY,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    articles = payload.get("articles", [])

    rows = []
    for article in articles:
        rows.append(
            {
                "source": parse_source_name(article.get("source", {})),
                "author": clean_text(article.get("author")),
                "title": clean_text(article.get("title")),
                "description": clean_text(article.get("description")),
                "url": clean_text(article.get("url")),
                "image_url": clean_text(article.get("urlToImage")),
                "publishedAt": clean_text(article.get("publishedAt")),
                "content": clean_text(article.get("content")),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["published_dt"] = safe_to_datetime(df["publishedAt"])
    df = df.dropna(subset=["title"]).copy()
    df = df.sort_values("published_dt", ascending=False).reset_index(drop=True)

    return df


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    working = df.copy()

    working["text_blob"] = working.apply(article_text_blob, axis=1)
    working[["risk_score", "risk"]] = working["text_blob"].apply(lambda x: pd.Series(get_risk_score_and_label(x)))
    working["category"] = working["text_blob"].apply(detect_primary_category)
    working["threat_actors"] = working["text_blob"].apply(extract_threat_actors)
    working["keywords"] = working["text_blob"].apply(extract_keywords)
    working["mitre"] = working["text_blob"].apply(map_mitre)

    location_info = working["text_blob"].apply(extract_location)
    working["location"] = location_info.apply(lambda x: x[0])
    working["latitude"] = location_info.apply(lambda x: x[1])
    working["longitude"] = location_info.apply(lambda x: x[2])
    working["region"] = location_info.apply(lambda x: x[3])

    working["priority_score"] = working.apply(rank_priority, axis=1)
    working["assigned_to"] = working["risk_score"].apply(assign_default_analyst)
    working["status"] = "Open"
    working["hour_bucket"] = working["published_dt"].dt.floor("h")
    working["article_id"] = range(1, len(working) + 1)

    return working


# =========================================================
# SESSION STATE
# =========================================================
if "assignments" not in st.session_state:
    st.session_state.assignments = {}

if "statuses" not in st.session_state:
    st.session_state.statuses = {}

if "selected_article_id" not in st.session_state:
    st.session_state.selected_article_id = None

if "generated_reports" not in st.session_state:
    st.session_state.generated_reports = {}


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("## Control Centre")
    st.caption("Tune the collection, triage, and analyst workflow.")

    query = st.text_area(
        "Threat query",
        value=NEWS_QUERY_DEFAULT,
        height=130,
        help="NewsAPI search query. Adjust to focus the feed.",
    )

    max_articles = st.slider("Max articles", 20, 100, MAX_ARTICLES_DEFAULT, 10)

    st.markdown("### Filters")

    severity_filter = st.multiselect(
        "Severity",
        options=["High", "Medium", "Low"],
        default=["High", "Medium", "Low"],
    )

    region_filter = st.multiselect(
        "Region",
        options=["North America", "Europe", "Middle East", "Asia-Pacific", "Africa", "Latin America", "Europe/Asia", "Unknown"],
        default=["North America", "Europe", "Middle East", "Asia-Pacific", "Africa", "Latin America", "Europe/Asia", "Unknown"],
    )

    category_filter = st.multiselect(
        "Category",
        options=["Cyber", "Civil Unrest", "Terrorism / Violence", "Espionage", "Supply Chain", "Disinformation / Influence", "General Threat"],
        default=["Cyber", "Civil Unrest", "Terrorism / Violence", "Espionage", "Supply Chain", "Disinformation / Influence", "General Threat"],
    )

    keyword_filter = st.text_input(
        "Keyword contains",
        placeholder="e.g. ransomware, London, LockBit",
    )

    analyst_filter = st.multiselect(
        "Assigned analyst",
        options=["L2 SOC Analyst", "Threat Intelligence Analyst", "Monitoring Queue", "IR Lead", "Regional Security", "Cyber Duty Officer"],
        default=["L2 SOC Analyst", "Threat Intelligence Analyst", "Monitoring Queue", "IR Lead", "Regional Security", "Cyber Duty Officer"],
    )

    only_mapped_geo = st.checkbox("Only show geolocated incidents", value=False)
    only_named_actors = st.checkbox("Only show named threat actors", value=False)

    st.markdown("### AI Reporting")
    use_openai = st.checkbox("Use OpenAI for incident reports", value=False, help="Requires OPENAI_API_KEY in your Streamlit secrets or environment.")
    auto_generate_local = st.checkbox("Auto-generate local analyst report", value=True)

    refresh = st.button("Refresh feed", use_container_width=True)

    st.markdown("---")
    st.caption("Environment variables needed:")
    st.code("NEWSAPI_KEY\nOPENAI_API_KEY (optional)\nOPENAI_MODEL (optional)", language="bash")


# =========================================================
# LOAD DATA
# =========================================================
if refresh:
    st.cache_data.clear()

raw_df = fetch_news(query=query, max_articles=max_articles)
df = enrich_dataframe(raw_df)

# apply dynamic assignment/status overrides
if not df.empty:
    df = df.copy()
    for idx, row in df.iterrows():
        aid = int(row["article_id"])
        if aid in st.session_state.assignments:
            df.at[idx, "assigned_to"] = st.session_state.assignments[aid]
        if aid in st.session_state.statuses:
            df.at[idx, "status"] = st.session_state.statuses[aid]

# filters
filtered_df = df.copy()
if not filtered_df.empty:
    filtered_df = filtered_df[filtered_df["risk"].isin(severity_filter)]
    filtered_df = filtered_df[filtered_df["region"].isin(region_filter)]
    filtered_df = filtered_df[filtered_df["category"].isin(category_filter)]
    filtered_df = filtered_df[filtered_df["assigned_to"].isin(analyst_filter)]

    if keyword_filter.strip():
        needle = keyword_filter.strip().lower()
        filtered_df = filtered_df[
            filtered_df["text_blob"].str.lower().str.contains(re.escape(needle), na=False)
        ]

    if only_mapped_geo:
        filtered_df = filtered_df[filtered_df["latitude"].notna() & filtered_df["longitude"].notna()]

    if only_named_actors:
        filtered_df = filtered_df[filtered_df["threat_actors"].apply(lambda x: len(x) > 0)]

    filtered_df = filtered_df.sort_values(
        ["priority_score", "published_dt"],
        ascending=[False, False]
    ).reset_index(drop=True)


# =========================================================
# HEADER
# =========================================================
st.markdown('<div class="main-title">Global Threat Monitoring Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-title">Real-time OSINT triage, threat visualisation, analyst workflow, and incident reporting. Last refresh: {utc_now_str()}</div>',
    unsafe_allow_html=True,
)

if not NEWSAPI_KEY:
    st.error("No NEWSAPI_KEY found. Add it to your environment or Streamlit secrets before running the live feed.")
    st.stop()

if df.empty:
    st.warning("No articles returned. Try widening the query or checking the NewsAPI configuration.")
    st.stop()


# =========================================================
# TOP METRICS
# =========================================================
total_alerts = len(filtered_df)
high_count = int((filtered_df["risk"] == "High").sum())
mapped_count = int(filtered_df["latitude"].notna().sum())
actor_count = int(filtered_df["threat_actors"].apply(lambda x: len(x) > 0).sum())
top_region = filtered_df["region"].mode().iloc[0] if not filtered_df.empty and not filtered_df["region"].mode().empty else "Unknown"

m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Visible Alerts</div>
            <div class="metric-value">{total_alerts}</div>
            <div class="metric-sub">Filtered operational picture</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">High Severity</div>
            <div class="metric-value">{high_count}</div>
            <div class="metric-sub">Auto-prioritised for review</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Geolocated</div>
            <div class="metric-value">{mapped_count}</div>
            <div class="metric-sub">Map-ready incidents</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Named Actors</div>
            <div class="metric-value">{actor_count}</div>
            <div class="metric-sub">Auto-profile capable</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m5:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Top Region</div>
            <div class="metric-value" style="font-size:1.35rem;">{top_region}</div>
            <div class="metric-sub">Most represented in current view</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="divider-space"></div>', unsafe_allow_html=True)


# =========================================================
# LAYOUT
# =========================================================
left_col, right_col = st.columns([1.55, 1.0], gap="large")


# =========================================================
# LEFT COLUMN
# =========================================================
with left_col:
    st.markdown('<div class="section-title">Live Threat Map</div>', unsafe_allow_html=True)

    map_df = filtered_df.dropna(subset=["latitude", "longitude"]).copy()

    if not map_df.empty:
        map_df["radius"] = map_df["priority_score"].apply(lambda x: max(25000, int(x) * 1800))
        map_df["tooltip_risk"] = map_df["risk"]
        map_df["tooltip_title"] = map_df["title"].apply(lambda x: shorten(x, 100))
        map_df["tooltip_location"] = map_df["location"].fillna("Unknown")

        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position='[longitude, latitude]',
            get_radius="radius",
            get_fill_color="""
                tooltip_risk === 'High' ? [255, 107, 107, 180] :
                tooltip_risk === 'Medium' ? [255, 209, 102, 170] :
                [123, 211, 137, 160]
            """,
            pickable=True,
            opacity=0.75,
            stroked=True,
            get_line_color=[255, 255, 255, 40],
            line_width_min_pixels=1,
        )

        hex_layer = pdk.Layer(
            "HexagonLayer",
            data=map_df,
            get_position='[longitude, latitude]',
            radius=120000,
            elevation_scale=25,
            elevation_range=[0, 3000],
            extruded=True,
            pickable=True,
            auto_highlight=True,
            coverage=0.88,
        )

        view_state = pdk.ViewState(
            latitude=float(map_df["latitude"].mean()),
            longitude=float(map_df["longitude"].mean()),
            zoom=1.2,
            pitch=35,
        )

        deck = pdk.Deck(
            layers=[hex_layer, scatter_layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/dark-v11",
            tooltip={
                "html": """
                    <b>{tooltip_title}</b><br/>
                    Severity: {tooltip_risk}<br/>
                    Location: {tooltip_location}<br/>
                    Source: {source}
                """,
                "style": {"backgroundColor": "#121722", "color": "white"},
            },
        )
        st.pydeck_chart(deck, use_container_width=True)
    else:
        st.info("No incidents in the current filtered view have usable geolocation.")

    st.markdown('<div class="section-title">Activity Timeline</div>', unsafe_allow_html=True)
    if not filtered_df.empty:
        timeline = (
            filtered_df.dropna(subset=["hour_bucket"])
            .groupby(["hour_bucket", "risk"], as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )

        if not timeline.empty:
            fig_timeline = px.area(
                timeline,
                x="hour_bucket",
                y="count",
                color="risk",
                line_group="risk",
                category_orders={"risk": ["Low", "Medium", "High"]},
                labels={"hour_bucket": "Published (UTC)", "count": "Alerts"},
            )
            fig_timeline.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                legend_title_text="Severity",
                font=dict(color="white"),
            )
            fig_timeline.update_xaxes(showgrid=False)
            fig_timeline.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
            st.plotly_chart(fig_timeline, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Not enough timestamped articles to render the timeline.")

    st.markdown('<div class="section-title">Alert Triage Queue</div>', unsafe_allow_html=True)

    if filtered_df.empty:
        st.warning("No alerts match the current filters.")
    else:
        queue_preview = filtered_df.head(12).copy()

        for _, row in queue_preview.iterrows():
            aid = int(row["article_id"])
            title = clean_text(row["title"])
            source = clean_text(row["source"])
            risk = clean_text(row["risk"])
            category = clean_text(row["category"])
            location = clean_text(row["location"]) or "Unknown"
            priority = int(row["priority_score"])
            published = row["published_dt"].strftime("%Y-%m-%d %H:%M UTC") if pd.notna(row["published_dt"]) else "Unknown"
            assigned_to = clean_text(row["assigned_to"])
            status = clean_text(row["status"])

            with st.expander(f"[P{priority}] {title}", expanded=False):
                c1, c2 = st.columns([2.8, 1.2], gap="large")

                with c1:
                    st.markdown(format_risk_pill(risk), unsafe_allow_html=True)
                    st.markdown(f'<span class="pill">{category}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span class="pill">{location}</span>', unsafe_allow_html=True)
                    if row["threat_actors"]:
                        for actor in row["threat_actors"][:3]:
                            st.markdown(f'<span class="pill">{actor}</span>', unsafe_allow_html=True)

                    st.markdown(
                        f"""
                        <div class="small-muted">
                        <strong>Source:</strong> {source}<br/>
                        <strong>Published:</strong> {published}<br/>
                        <strong>Assigned:</strong> {assigned_to}<br/>
                        <strong>Status:</strong> {status}<br/>
                        <strong>Priority Score:</strong> {priority}/100
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if clean_text(row["description"]):
                        st.write(clean_text(row["description"]))

                with c2:
                    selected_analyst = st.selectbox(
                        f"Assign analyst #{aid}",
                        options=["Monitoring Queue", "Threat Intelligence Analyst", "L2 SOC Analyst", "IR Lead", "Regional Security", "Cyber Duty Officer"],
                        index=["Monitoring Queue", "Threat Intelligence Analyst", "L2 SOC Analyst", "IR Lead", "Regional Security", "Cyber Duty Officer"].index(assigned_to)
                        if assigned_to in ["Monitoring Queue", "Threat Intelligence Analyst", "L2 SOC Analyst", "IR Lead", "Regional Security", "Cyber Duty Officer"]
                        else 0,
                        key=f"assign_select_{aid}",
                    )
                    if st.button("Save assignment", key=f"assign_btn_{aid}", use_container_width=True):
                        st.session_state.assignments[aid] = selected_analyst
                        st.success(f"Assigned to {selected_analyst}")

                    selected_status = st.selectbox(
                        f"Update status #{aid}",
                        options=["Open", "Monitoring", "Escalated", "Closed"],
                        index=["Open", "Monitoring", "Escalated", "Closed"].index(status)
                        if status in ["Open", "Monitoring", "Escalated", "Closed"]
                        else 0,
                        key=f"status_select_{aid}",
                    )
                    if st.button("Save status", key=f"status_btn_{aid}", use_container_width=True):
                        st.session_state.statuses[aid] = selected_status
                        st.success(f"Status updated to {selected_status}")

                    if st.button("Open incident view", key=f"open_incident_{aid}", use_container_width=True):
                        st.session_state.selected_article_id = aid

                    st.link_button("View source", row["url"], use_container_width=True)


# =========================================================
# RIGHT COLUMN
# =========================================================
with right_col:
    st.markdown('<div class="section-title">Threat Distribution</div>', unsafe_allow_html=True)

    if not filtered_df.empty:
        c1, c2 = st.columns(2)

        with c1:
            severity_counts = (
                filtered_df["risk"]
                .value_counts()
                .reindex(["High", "Medium", "Low"])
                .fillna(0)
                .reset_index()
            )
            severity_counts.columns = ["risk", "count"]
            fig_sev = px.pie(severity_counts, names="risk", values="count", hole=0.58)
            fig_sev.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                font=dict(color="white"),
                showlegend=True,
            )
            st.plotly_chart(fig_sev, use_container_width=True, config={"displayModeBar": False})

        with c2:
            region_counts = filtered_df["region"].value_counts().reset_index()
            region_counts.columns = ["region", "count"]
            fig_region = px.bar(region_counts, x="region", y="count")
            fig_region.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                font=dict(color="white"),
            )
            fig_region.update_xaxes(showgrid=False)
            fig_region.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
            st.plotly_chart(fig_region, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="section-title">Threat Actor Profiles</div>', unsafe_allow_html=True)

    actor_rows = filtered_df[filtered_df["threat_actors"].apply(lambda x: len(x) > 0)].head(5)
    if actor_rows.empty:
        st.info("No named threat actors detected in the current filtered view.")
    else:
        for _, row in actor_rows.iterrows():
            actors = row["threat_actors"]
            with st.container():
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown(f"**Linked incident:** {shorten(row['title'], 88)}")
                st.markdown(build_actor_profile(actors))
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="divider-space"></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">KQL Detection Simulation</div>', unsafe_allow_html=True)

    kql_source_df = filtered_df.head(8)
    if not kql_source_df.empty:
        options = {
            f"[{r['risk']}] {shorten(r['title'], 78)}": int(r["article_id"])
            for _, r in kql_source_df.iterrows()
        }
        selected_kql_label = st.selectbox("Choose incident for KQL pivots", list(options.keys()))
        selected_kql_id = options[selected_kql_label]
        selected_kql_row = filtered_df[filtered_df["article_id"] == selected_kql_id].iloc[0]
        st.code(build_kql_queries(selected_kql_row), language="kusto")
    else:
        st.info("No incidents available for KQL simulation.")

    st.markdown('<div class="section-title">Operational Log Stream</div>', unsafe_allow_html=True)
    if not filtered_df.empty:
        log_row = filtered_df.iloc[0]
        logs = generate_simulated_logs(log_row)
        st.markdown(
            f'<div class="log-box">{"".join(line + chr(10) for line in logs)}</div>',
            unsafe_allow_html=True,
        )


# =========================================================
# INCIDENT DRILL-DOWN
# =========================================================
st.markdown("---")
st.markdown('<div class="section-title">Incident Drill-Down</div>', unsafe_allow_html=True)

incident_df = filtered_df.copy()
if incident_df.empty:
    st.info("No incidents available in the current view.")
    st.stop()

incident_options = {
    f"[{row['risk']}] {shorten(row['title'], 90)}": int(row["article_id"])
    for _, row in incident_df.head(30).iterrows()
}

default_incident_id = st.session_state.selected_article_id
if default_incident_id not in incident_df["article_id"].tolist():
    default_incident_id = int(incident_df.iloc[0]["article_id"])

incident_labels = list(incident_options.keys())
default_label = next(
    (label for label, aid in incident_options.items() if aid == default_incident_id),
    incident_labels[0]
)

selected_incident_label = st.selectbox("Select incident", incident_labels, index=incident_labels.index(default_label))
selected_incident_id = incident_options[selected_incident_label]
selected = incident_df[incident_df["article_id"] == selected_incident_id].iloc[0]

st.session_state.selected_article_id = int(selected["article_id"])

d1, d2 = st.columns([1.15, 0.85], gap="large")

with d1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f"## {clean_text(selected['title'])}")
    st.markdown(
        f"""
        {format_risk_pill(clean_text(selected['risk']))}
        <span class="pill">{clean_text(selected['category'])}</span>
        <span class="pill">{clean_text(selected['region'])}</span>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="small-muted">
        <strong>Source:</strong> {clean_text(selected['source'])}<br/>
        <strong>Published:</strong> {selected['published_dt'].strftime("%Y-%m-%d %H:%M UTC") if pd.notna(selected['published_dt']) else "Unknown"}<br/>
        <strong>Location:</strong> {clean_text(selected['location']) or "Unknown"}<br/>
        <strong>Assigned:</strong> {clean_text(selected['assigned_to'])}<br/>
        <strong>Status:</strong> {clean_text(selected['status'])}<br/>
        <strong>Priority Score:</strong> {int(selected['priority_score'])}/100
        </div>
        """,
        unsafe_allow_html=True,
    )

    if clean_text(selected["description"]):
        st.markdown("### Summary")
        st.write(clean_text(selected["description"]))

    if clean_text(selected["content"]):
        st.markdown("### Source Extract")
        st.write(clean_text(selected["content"]))

    if selected["keywords"]:
        st.markdown("### Extracted Indicators / Themes")
        for kw in selected["keywords"]:
            st.markdown(f"- {kw}")

    if selected["mitre"]:
        st.markdown("### MITRE / TTP Mapping")
        for m in selected["mitre"]:
            st.markdown(f"- {m}")

    if selected["threat_actors"]:
        st.markdown("### Threat Actor Analysis")
        st.markdown(build_actor_profile(selected["threat_actors"]))
    else:
        st.markdown("### Threat Actor Analysis")
        st.write("No named actor detected. Continue monitoring for campaign overlap, infrastructure reuse, or external attribution.")

    st.link_button("Open original article", selected["url"])
    st.markdown('</div>', unsafe_allow_html=True)

with d2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Analyst Workflow")

    esc1, esc2 = st.columns(2)
    with esc1:
        if st.button("Escalate Incident", key=f"escalate_main_{selected_incident_id}", use_container_width=True):
            st.session_state.statuses[int(selected_incident_id)] = "Escalated"
            st.success("Incident escalated.")
    with esc2:
        if st.button("Close Incident", key=f"close_main_{selected_incident_id}", use_container_width=True):
            st.session_state.statuses[int(selected_incident_id)] = "Closed"
            st.success("Incident closed.")

    st.markdown("### Assignment")
    chosen_owner = st.selectbox(
        "Reassign owner",
        ["Monitoring Queue", "Threat Intelligence Analyst", "L2 SOC Analyst", "IR Lead", "Regional Security", "Cyber Duty Officer"],
        index=["Monitoring Queue", "Threat Intelligence Analyst", "L2 SOC Analyst", "IR Lead", "Regional Security", "Cyber Duty Officer"].index(clean_text(selected["assigned_to"]))
        if clean_text(selected["assigned_to"]) in ["Monitoring Queue", "Threat Intelligence Analyst", "L2 SOC Analyst", "IR Lead", "Regional Security", "Cyber Duty Officer"]
        else 0,
        key=f"incident_reassign_{selected_incident_id}",
    )
    if st.button("Update owner", key=f"incident_reassign_btn_{selected_incident_id}", use_container_width=True):
        st.session_state.assignments[int(selected_incident_id)] = chosen_owner
        st.success(f"Owner updated to {chosen_owner}")

    st.markdown("### Simulated Detection Logs")
    log_lines = generate_simulated_logs(selected)
    st.markdown(
        f'<div class="log-box">{"".join(line + chr(10) for line in log_lines)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# AI INCIDENT REPORT
# =========================================================
st.markdown("---")
st.markdown('<div class="section-title">AI-Generated Incident Report</div>', unsafe_allow_html=True)

report_key = int(selected_incident_id)

if auto_generate_local and report_key not in st.session_state.generated_reports:
    st.session_state.generated_reports[report_key] = generate_local_incident_report(selected)

r1, r2 = st.columns([1.15, 0.85], gap="large")

with r1:
    if use_openai and not OPENAI_API_KEY:
        st.warning("OPENAI_API_KEY is not set, so the app cannot generate a live OpenAI report. Showing the local analyst report instead.")

    generate_btn = st.button("Generate / Refresh Report", key=f"gen_report_{report_key}")

    if generate_btn:
        try:
            if use_openai and OPENAI_API_KEY:
                with st.spinner("Generating report with OpenAI..."):
                    st.session_state.generated_reports[report_key] = generate_openai_incident_report(
                        selected, OPENAI_API_KEY, OPENAI_MODEL
                    )
            else:
                st.session_state.generated_reports[report_key] = generate_local_incident_report(selected)
        except Exception as e:
            st.error(f"Report generation failed: {e}")
            st.session_state.generated_reports[report_key] = generate_local_incident_report(selected)

    current_report = st.session_state.generated_reports.get(report_key, generate_local_incident_report(selected))
    st.markdown(current_report)

with r2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Report Actions")
    st.download_button(
        "Download Incident Report",
        data=current_report,
        file_name=f"incident_report_{report_key}.md",
        mime="text/markdown",
        use_container_width=True,
        key=f"download_report_{report_key}",
    )

    st.download_button(
        "Download Filtered Dataset",
        data=filtered_df.drop(columns=["text_blob"]).to_csv(index=False).encode("utf-8"),
        file_name="filtered_threat_feed.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_filtered_dataset",
    )

    st.markdown("### Report Metadata")
    st.markdown(
        f"""
        <div class="small-muted">
        <strong>Model path:</strong> {"OpenAI API" if use_openai and OPENAI_API_KEY else "Local heuristic report"}<br/>
        <strong>Incident ID:</strong> {report_key}<br/>
        <strong>Severity:</strong> {clean_text(selected["risk"])}<br/>
        <strong>Category:</strong> {clean_text(selected["category"])}<br/>
        <strong>Generated:</strong> {utc_now_str()}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# ANALYST TABLE
# =========================================================
st.markdown("---")
st.markdown('<div class="section-title">Analyst Workbench Table</div>', unsafe_allow_html=True)

table_df = filtered_df[
    [
        "article_id",
        "published_dt",
        "risk",
        "risk_score",
        "priority_score",
        "category",
        "region",
        "location",
        "source",
        "assigned_to",
        "status",
        "title",
    ]
].copy()

table_df["published_dt"] = table_df["published_dt"].dt.strftime("%Y-%m-%d %H:%M UTC")
st.dataframe(table_df, use_container_width=True, hide_index=True)
