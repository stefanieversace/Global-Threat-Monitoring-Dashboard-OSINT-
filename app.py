import html
import re
from datetime import datetime, timezone

import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Global Threat Monitoring Dashboard",
    page_icon="🌍",
    layout="wide",
)

# =========================================================
# GLOBAL STYLING
# =========================================================
st.markdown(
    """
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    :root {
        --bg: #050811;
        --bg2: #09111d;
        --panel: rgba(13, 20, 33, 0.92);
        --panel2: rgba(10, 16, 27, 0.96);
        --stroke: rgba(255,255,255,0.08);
        --text: #eef3ff;
        --muted: #9fb0cf;
        --accent: #95adff;
        --accent2: #69e3c6;
        --red: #ff6b86;
        --amber: #ffc26b;
        --green: #67e6a8;
        --shadow: 0 22px 60px rgba(0,0,0,0.35);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(149,173,255,0.11), transparent 26%),
            radial-gradient(circle at top right, rgba(105,227,198,0.07), transparent 20%),
            linear-gradient(180deg, var(--bg) 0%, var(--bg2) 100%);
        color: var(--text);
    }

    html, body, [class*="css"] {
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .block-container {
        padding-top: 1.1rem;
        padding-bottom: 2rem;
        max-width: 1550px;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10,14,24,0.98), rgba(8,11,20,0.98));
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    .hero-wrap {
        padding-top: 0.35rem;
        padding-bottom: 0.45rem;
        margin-bottom: 0.65rem;
    }

    .hero-title {
        font-size: 2.55rem;
        font-weight: 850;
        line-height: 1.02;
        letter-spacing: -0.03em;
        color: #ffffff;
        text-align: center;
        margin-bottom: 0.3rem;
    }

    .hero-sub {
        text-align: center;
        color: var(--muted);
        font-size: 0.98rem;
        margin-bottom: 0.5rem;
    }

    .mode-pill {
        display: inline-block;
        margin: 0 auto;
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
        color: #dbe5ff;
        font-size: 0.8rem;
        font-weight: 700;
    }

    .panel {
        background: linear-gradient(180deg, rgba(17,24,39,0.94), rgba(10,15,27,0.97));
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 24px;
        padding: 1rem 1rem 1rem 1rem;
        box-shadow: var(--shadow);
        backdrop-filter: blur(10px);
    }

    .metric-card {
        background: linear-gradient(180deg, rgba(17,24,39,0.98), rgba(10,15,27,0.98));
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 22px;
        padding: 1rem 1rem 0.95rem 1rem;
        box-shadow: var(--shadow);
        min-height: 122px;
    }

    .metric-label {
        color: var(--muted);
        font-size: 0.79rem;
        margin-bottom: 0.32rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .metric-value {
        color: white;
        font-size: 2rem;
        font-weight: 850;
        line-height: 1.0;
        margin-bottom: 0.3rem;
    }

    .metric-sub {
        color: var(--muted);
        font-size: 0.88rem;
    }

    .alert-card {
        background: linear-gradient(180deg, rgba(14,20,34,0.99), rgba(9,13,24,0.99));
        border: 1px solid rgba(255,255,255,0.06);
        border-left: 5px solid #8ea6ff;
        border-radius: 18px;
        padding: 0.95rem 1rem;
        margin-bottom: 0.9rem;
    }

    .alert-high { border-left-color: #ff6b86; }
    .alert-medium { border-left-color: #ffc26b; }
    .alert-low { border-left-color: #67e6a8; }

    .badge {
        display: inline-block;
        padding: 0.26rem 0.62rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        margin-right: 0.35rem;
        margin-top: 0.25rem;
        border: 1px solid rgba(255,255,255,0.08);
    }

    .badge-high { background: rgba(255,107,134,0.16); color: #ffd0d9; }
    .badge-medium { background: rgba(255,194,107,0.16); color: #ffe2b4; }
    .badge-low { background: rgba(103,230,168,0.16); color: #d3ffe7; }
    .badge-neutral { background: rgba(142,166,255,0.16); color: #dfe7ff; }

    .small-muted {
        color: var(--muted);
        font-size: 0.9rem;
        line-height: 1.6;
    }

    .brief-panel {
        background: linear-gradient(180deg, rgba(18,24,38,0.98), rgba(9,14,24,0.98));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 18px;
        max-height: 480px;
        overflow-y: auto;
        white-space: pre-wrap;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 13px;
        line-height: 1.65;
        color: #e6ecff;
    }

    .footer-note {
        color: var(--muted);
        font-size: 0.82rem;
        margin-top: 1rem;
        text-align: center;
    }

    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stTextArea textarea,
    .stNumberInput input {
        background-color: rgba(255,255,255,0.03) !important;
        color: white !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }

    .stDownloadButton button,
    .stButton button,
    .stLinkButton a {
        background: linear-gradient(180deg, #95adff, #7594ff) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 20px rgba(117,148,255,0.25);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 0.5rem 0.9rem;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(149,173,255,0.14) !important;
    }

    .log-box {
        background: rgba(0,0,0,0.22);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 0.75rem 0.85rem;
        margin-bottom: 0.6rem;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        color: #dce5ff;
        font-size: 0.83rem;
        line-height: 1.55;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# CONSTANTS
# =========================================================
LOCATION_ALIASES = {
    "London": [
        "london", "uk", "united kingdom", "britain", "england"
    ],
    "Paris": [
        "paris", "france"
    ],
    "Berlin": [
        "berlin", "germany"
    ],
    "Rome": [
        "rome", "italy"
    ],
    "Madrid": [
        "madrid", "spain"
    ],
    "New York": [
        "new york", "nyc", "new york city"
    ],
    "Washington": [
        "washington", "washington dc", "dc"
    ],
    "Los Angeles": [
        "los angeles", "la"
    ],
    "Chicago": [
        "chicago"
    ],
    "San Francisco": [
        "san francisco"
    ],
    "Toronto": [
        "toronto", "canada"
    ],
    "Mexico City": [
        "mexico city", "mexico"
    ],
    "Dubai": [
        "dubai", "uae", "united arab emirates"
    ],
    "Tel Aviv": [
        "tel aviv", "israel"
    ],
    "Jerusalem": [
        "jerusalem"
    ],
    "Gaza": [
        "gaza"
    ],
    "Kyiv": [
        "kyiv", "kiev", "ukraine"
    ],
    "Moscow": [
        "moscow", "russia"
    ],
    "Istanbul": [
        "istanbul", "turkey"
    ],
    "Athens": [
        "athens", "greece"
    ],
    "Warsaw": [
        "warsaw", "poland"
    ],
    "Brussels": [
        "brussels", "belgium"
    ],
    "Amsterdam": [
        "amsterdam", "netherlands"
    ],
    "Vienna": [
        "vienna", "austria"
    ],
    "Dublin": [
        "dublin", "ireland"
    ],
    "Stockholm": [
        "stockholm", "sweden"
    ],
    "Oslo": [
        "oslo", "norway"
    ],
    "Copenhagen": [
        "copenhagen", "denmark"
    ],
    "Prague": [
        "prague", "czech republic", "czechia"
    ],
    "Cairo": [
        "cairo", "egypt"
    ],
    "Nairobi": [
        "nairobi", "kenya"
    ],
    "Lagos": [
        "lagos", "nigeria"
    ],
    "Johannesburg": [
        "johannesburg", "south africa"
    ],
    "Cape Town": [
        "cape town"
    ],
    "Beijing": [
        "beijing", "china"
    ],
    "Shanghai": [
        "shanghai"
    ],
    "Tokyo": [
        "tokyo", "japan"
    ],
    "Seoul": [
        "seoul", "south korea", "korea"
    ],
    "Taipei": [
        "taipei", "taiwan"
    ],
    "Hong Kong": [
        "hong kong"
    ],
    "Singapore": [
        "singapore"
    ],
    "Bangkok": [
        "bangkok", "thailand"
    ],
    "Jakarta": [
        "jakarta", "indonesia"
    ],
    "Bali": [
        "bali"
    ],
    "Manila": [
        "manila", "philippines"
    ],
    "Delhi": [
        "delhi", "new delhi"
    ],
    "Mumbai": [
        "mumbai", "bombay"
    ],
    "Sydney": [
        "sydney", "australia"
    ],
    "Melbourne": [
        "melbourne"
    ],
    "Auckland": [
        "auckland", "new zealand"
    ],
    "Sao Paulo": [
        "sao paulo", "são paulo"
    ],
    "Rio de Janeiro": [
        "rio de janeiro", "rio"
    ],
    "Buenos Aires": [
        "buenos aires", "argentina"
    ],
}

LOCATION_COORDS = {
    "London": (51.5074, -0.1278),
    "Paris": (48.8566, 2.3522),
    "Berlin": (52.5200, 13.4050),
    "Rome": (41.9028, 12.4964),
    "Madrid": (40.4168, -3.7038),
    "New York": (40.7128, -74.0060),
    "Washington": (38.9072, -77.0369),
    "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298),
    "San Francisco": (37.7749, -122.4194),
    "Toronto": (43.6532, -79.3832),
    "Mexico City": (19.4326, -99.1332),
    "Dubai": (25.2048, 55.2708),
    "Tel Aviv": (32.0853, 34.7818),
    "Jerusalem": (31.7683, 35.2137),
    "Gaza": (31.5017, 34.4668),
    "Kyiv": (50.4501, 30.5234),
    "Moscow": (55.7558, 37.6173),
    "Istanbul": (41.0082, 28.9784),
    "Athens": (37.9838, 23.7275),
    "Warsaw": (52.2297, 21.0122),
    "Brussels": (50.8503, 4.3517),
    "Amsterdam": (52.3676, 4.9041),
    "Vienna": (48.2082, 16.3738),
    "Dublin": (53.3498, -6.2603),
    "Stockholm": (59.3293, 18.0686),
    "Oslo": (59.9139, 10.7522),
    "Copenhagen": (55.6761, 12.5683),
    "Prague": (50.0755, 14.4378),
    "Cairo": (30.0444, 31.2357),
    "Nairobi": (-1.2921, 36.8219),
    "Lagos": (6.5244, 3.3792),
    "Johannesburg": (-26.2041, 28.0473),
    "Cape Town": (-33.9249, 18.4241),
    "Beijing": (39.9042, 116.4074),
    "Shanghai": (31.2304, 121.4737),
    "Tokyo": (35.6762, 139.6503),
    "Seoul": (37.5665, 126.9780),
    "Taipei": (25.0330, 121.5654),
    "Hong Kong": (22.3193, 114.1694),
    "Singapore": (1.3521, 103.8198),
    "Bangkok": (13.7563, 100.5018),
    "Jakarta": (-6.2088, 106.8456),
    "Bali": (-8.4095, 115.1889),
    "Manila": (14.5995, 120.9842),
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Sydney": (-33.8688, 151.2093),
    "Melbourne": (-37.8136, 144.9631),
    "Auckland": (-36.8509, 174.7645),
    "Sao Paulo": (-23.5505, -46.6333),
    "Rio de Janeiro": (-22.9068, -43.1729),
    "Buenos Aires": (-34.6037, -58.3816),
    "Global": (20.0, 0.0),
}

REGION_LOOKUP = {
    "Europe": [
        "London", "Paris", "Berlin", "Rome", "Madrid", "Kyiv", "Moscow", "Istanbul",
        "Athens", "Warsaw", "Brussels", "Amsterdam", "Vienna", "Dublin",
        "Stockholm", "Oslo", "Copenhagen", "Prague"
    ],
    "North America": [
        "New York", "Washington", "Los Angeles", "Chicago", "San Francisco", "Toronto", "Mexico City"
    ],
    "Asia-Pacific": [
        "Beijing", "Shanghai", "Tokyo", "Seoul", "Taipei", "Hong Kong", "Singapore",
        "Bangkok", "Jakarta", "Bali", "Manila", "Delhi", "Mumbai", "Sydney",
        "Melbourne", "Auckland"
    ],
    "Middle East": [
        "Dubai", "Tel Aviv", "Jerusalem", "Gaza"
    ],
    "Africa": [
        "Cairo", "Nairobi", "Lagos", "Johannesburg", "Cape Town"
    ],
    "Latin America": [
        "Sao Paulo", "Rio de Janeiro", "Buenos Aires"
    ],
    "Global": [
        "Global"
    ],
}

THREAT_PATTERNS = {
    "Cyberattack": [
        "cyber", "breach", "ransomware", "phishing", "malware", "ddos",
        "exploit", "zero-day", "hacker", "compromised", "credential", "intrusion"
    ],
    "Civil Unrest": [
        "protest", "riot", "unrest", "clashes", "demonstration", "strike", "march", "curfew"
    ],
    "Conflict": [
        "missile", "drone", "shelling", "airstrike", "troops", "conflict", "military",
        "offensive", "strike", "attack", "artillery"
    ],
    "Terror / Violent Incident": [
        "terror", "bomb", "shooting", "explosion", "hostage", "knife attack", "assailant"
    ],
    "Infrastructure / Disruption": [
        "outage", "blackout", "airport", "rail", "transport", "shutdown", "port",
        "service disruption", "grid", "power outage", "network outage"
    ],
    "Fraud / Financial Crime": [
        "fraud", "scam", "money laundering", "sanctions", "illicit finance", "embezzlement"
    ],
}

SECTOR_PATTERNS = {
    "Finance": ["bank", "banking", "financial", "payment", "fintech", "exchange", "insurer"],
    "Government": ["government", "ministry", "parliament", "embassy", "federal", "state department"],
    "Technology": ["tech", "software", "cloud", "platform", "app", "provider", "data centre", "saas"],
    "Transport": ["airport", "rail", "metro", "flight", "airline", "shipping", "port", "train"],
    "Healthcare": ["hospital", "clinic", "health", "pharma", "medical", "nhs"],
    "Energy": ["energy", "power", "grid", "oil", "gas", "utility", "substation"],
    "Media": ["media", "broadcast", "newsroom", "television", "streaming", "studio"],
    "Retail": ["retail", "store", "supermarket", "e-commerce", "consumer"],
}

MITRE_RULES = [
    ("T1566", "Phishing", ["phishing", "malicious email", "credential harvesting", "email lure"]),
    ("T1078", "Valid Accounts", ["stolen credentials", "compromised account", "account takeover", "credential"]),
    ("T1190", "Exploit Public-Facing Application", ["exploit", "zero-day", "public-facing", "vulnerability"]),
    ("T1486", "Data Encrypted for Impact", ["ransomware", "encrypted systems", "encryption malware"]),
    ("T1498", "Network Denial of Service", ["ddos", "traffic flood", "service disruption"]),
    ("T1567", "Exfiltration Over Web Service", ["data leak", "data breach", "exfiltration"]),
]

DEFAULT_QUERY = (
    "cyber OR ransomware OR phishing OR protest OR conflict OR explosion "
    "OR outage OR breach OR attack OR fraud"
)

SIMULATED_INCIDENTS = [
    {
        "title": "Phishing campaign targets European financial institutions",
        "description": "Credential harvesting lures reported against banking users in London and Paris, with suspicious login infrastructure observed.",
        "source": {"name": "Simulation Desk"},
        "url": "https://example.com/sim-1",
        "publishedAt": "2026-04-04T07:20:00Z",
    },
    {
        "title": "Civil unrest disrupts metro services in Paris",
        "description": "Transport disruption reported after demonstrations escalated near major transit hubs in Paris.",
        "source": {"name": "Simulation Desk"},
        "url": "https://example.com/sim-2",
        "publishedAt": "2026-04-04T09:10:00Z",
    },
    {
        "title": "Ransomware incident affects healthcare network in New York",
        "description": "A regional healthcare provider reported encrypted systems and cancelled appointments following a suspected ransomware intrusion.",
        "source": {"name": "Simulation Desk"},
        "url": "https://example.com/sim-3",
        "publishedAt": "2026-04-04T05:55:00Z",
    },
    {
        "title": "DDoS activity causes outage for cloud platform in Singapore",
        "description": "Customers reported service instability after heavy malicious traffic impacted a cloud provider serving enterprise applications.",
        "source": {"name": "Simulation Desk"},
        "url": "https://example.com/sim-4",
        "publishedAt": "2026-04-04T02:40:00Z",
    },
    {
        "title": "Drone strike reported near critical infrastructure in Kyiv",
        "description": "Authorities reported overnight drone activity affecting power distribution and operational continuity in Ukraine.",
        "source": {"name": "Simulation Desk"},
        "url": "https://example.com/sim-5",
        "publishedAt": "2026-04-04T01:05:00Z",
    },
    {
        "title": "Suspicious financial crime probe expands in Dubai",
        "description": "Investigators are reviewing possible money laundering exposure linked to shell entities and regional transaction flows.",
        "source": {"name": "Simulation Desk"},
        "url": "https://example.com/sim-6",
        "publishedAt": "2026-04-03T22:25:00Z",
    },
    {
        "title": "Power disruption reported near Cairo transport corridor",
        "description": "Operational delays followed a grid issue affecting rail-linked transport infrastructure outside Cairo.",
        "source": {"name": "Simulation Desk"},
        "url": "https://example.com/sim-7",
        "publishedAt": "2026-04-03T18:45:00Z",
    },
    {
        "title": "Credential theft infrastructure linked to Tokyo enterprise users",
        "description": "Suspicious fake login pages targeting corporate users in Tokyo suggest a coordinated phishing operation.",
        "source": {"name": "Simulation Desk"},
        "url": "https://example.com/sim-8",
        "publishedAt": "2026-04-03T17:30:00Z",
    },
]

# =========================================================
# HELPERS
# =========================================================
def get_newsapi_key():
    try:
        return st.secrets["NEWSAPI_KEY"]
    except Exception:
        return None


def clean_text(value):
    if pd.isna(value):
        return ""
    return html.unescape(str(value)).strip()


def safe_lower(value):
    return str(value).lower().strip()


def normalize_text_for_location(text):
    text = str(text).lower()

    # Remove punctuation that can break matching
    text = re.sub(r"[^\w\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_location(text):
    text_norm = normalize_text_for_location(text)

    # Longest keyword first to avoid "york" type misfires if added later
    matches = []
    for canonical, aliases in LOCATION_ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            if alias in text_norm:
                matches.append((canonical, len(alias)))

    if matches:
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0][0]

    return "Global"


def location_to_coords(location):
    return LOCATION_COORDS.get(location, LOCATION_COORDS["Global"])


def infer_region(location):
    for region, places in REGION_LOOKUP.items():
        if location in places:
            return region
    return "Global"


def infer_threat_type(text):
    text_lower = safe_lower(text)
    for threat, keywords in THREAT_PATTERNS.items():
        if any(word in text_lower for word in keywords):
            return threat
    return "General Security"


def infer_sector(text):
    text_lower = safe_lower(text)
    for sector, keywords in SECTOR_PATTERNS.items():
        if any(word in text_lower for word in keywords):
            return sector
    return "General"


def severity_score(text):
    text_lower = safe_lower(text)
    score = 20

    high_terms = [
        "ransomware", "explosion", "terror", "missile", "drone strike",
        "breach", "data breach", "hospital", "critical infrastructure",
        "airstrike", "shooting", "hostage", "outage", "blackout",
        "ddos", "zero-day", "power grid", "mass casualty"
    ]
    medium_terms = [
        "phishing", "fraud", "protest", "unrest", "clashes",
        "investigation", "suspicious", "disruption", "shutdown",
        "sanctions", "malware", "intrusion"
    ]

    for term in high_terms:
        if term in text_lower:
            score += 18

    for term in medium_terms:
        if term in text_lower:
            score += 9

    if any(word in text_lower for word in [
        "government", "bank", "airport", "rail", "hospital", "energy", "power", "cloud", "telecom"
    ]):
        score += 12

    if any(word in text_lower for word in [
        "multiple", "regional", "national", "global", "widespread", "coordinated"
    ]):
        score += 8

    return min(score, 100)


def severity_label(score):
    if score >= 70:
        return "High"
    if score >= 45:
        return "Medium"
    return "Low"


def severity_color(severity):
    if severity == "High":
        return "red"
    if severity == "Medium":
        return "orange"
    return "green"


def map_to_mitre(text):
    text_lower = safe_lower(text)
    hits = []

    for technique, name, keywords in MITRE_RULES:
        if any(k in text_lower for k in keywords):
            hits.append(f"{technique} • {name}")

    return hits if hits else ["T1595 • Active Scanning / Unspecified"]


def generate_actor_profile(text):
    text_lower = safe_lower(text)

    if "ransomware" in text_lower:
        return {
            "actor": "Ransomware Operators",
            "motivation": "Financial gain",
            "capability": "High",
            "ttp": "Initial access via phishing, exposed services, or stolen credentials followed by encryption and extortion.",
        }
    if "phishing" in text_lower or "credential" in text_lower:
        return {
            "actor": "Credential Theft Cluster",
            "motivation": "Account compromise and follow-on intrusion",
            "capability": "Medium",
            "ttp": "Deceptive lures, fake login pages, and session theft against enterprise users.",
        }
    if any(word in text_lower for word in ["protest", "riot", "demonstration", "unrest", "clashes"]):
        return {
            "actor": "Unstructured Demonstration Network",
            "motivation": "Political or social mobilisation",
            "capability": "Low to Medium",
            "ttp": "Crowd mobilisation, transport disruption, opportunistic escalation, and rapid online amplification.",
        }
    if any(word in text_lower for word in ["drone", "missile", "airstrike", "troops", "shelling", "conflict"]):
        return {
            "actor": "Hybrid Conflict Actor",
            "motivation": "Territorial, military, or political objectives",
            "capability": "High",
            "ttp": "Kinetic strikes, infrastructure pressure, information operations, and asymmetric escalation.",
        }
    if any(word in text_lower for word in ["fraud", "money laundering", "shell entities", "illicit finance"]):
        return {
            "actor": "Financial Crime Network",
            "motivation": "Profit and concealment of illicit flows",
            "capability": "Medium to High",
            "ttp": "Layered transactions, shell entities, sanctions evasion patterns, and transactional opacity.",
        }

    return {
        "actor": "Emergent / Unspecified Threat Cluster",
        "motivation": "Mixed or unclear",
        "capability": "Medium",
        "ttp": "Limited information available. Monitoring recommended for repeat patterns and escalation indicators.",
    }


def generate_detection_summary(row):
    threat = row["threat_type"]

    if threat == "Cyberattack":
        return "Suspicious intrusion activity consistent with credential theft, ransomware, or exploitation workflow."
    if threat == "Civil Unrest":
        return "Escalation risk to transport, venue operations, and personnel movement due to public disorder indicators."
    if threat == "Conflict":
        return "Kinetic or hybrid threat indicators suggest infrastructure disruption and elevated regional instability."
    if threat == "Infrastructure / Disruption":
        return "Operational continuity affected by service outage or infrastructure pressure requiring contingency tracking."
    if threat == "Fraud / Financial Crime":
        return "Potential regulatory, transactional, or illicit finance exposure requiring enhanced due diligence."
    if threat == "Terror / Violent Incident":
        return "Potential mass-casualty or targeted violence indicators require immediate validation and protective posture review."
    return "Monitor evolving threat indicators and validate operational impact."


def simulated_log_lines(row):
    ts = row["published_dt"]
    if pd.isna(ts):
        ts = datetime.now(timezone.utc)

    ts_str = ts.strftime("%Y-%m-%d %H:%M:%S UTC")
    mitre_first = row["mitre_tags"][0] if row["mitre_tags"] else "Unmapped"

    return [
        f"{ts_str} | OSINT_FEED      | INGEST           | source={row['source']} | title=\"{row['title'][:100]}\"",
        f"{ts_str} | NLP_GEO         | LOCATION_MATCH   | location={row['location']} | region={row['region']}",
        f"{ts_str} | TRIAGE_ENGINE   | SCORE={row['severity_score']} | threat_type={row['threat_type']} | sector={row['sector']}",
        f"{ts_str} | MITRE_ENRICH    | technique={mitre_first}",
        f"{ts_str} | ANALYST_QUEUE   | priority={row['queue_priority']} | action={'ESCALATE' if row['severity'] == 'High' else 'VALIDATE'}",
    ]


def build_brief(df):
    now_str = datetime.now().strftime("%d %b %Y, %H:%M")
    total_count = len(df)
    high_count = int((df["severity"] == "High").sum()) if not df.empty else 0
    dominant_threat = df["threat_type"].mode().iloc[0] if not df.empty else "N/A"
    dominant_region = df["region"].mode().iloc[0] if not df.empty else "N/A"

    lines = [
        "GLOBAL THREAT INTELLIGENCE BRIEF",
        f"Generated: {now_str}",
        "",
        "EXECUTIVE SUMMARY",
        f"- Total incidents tracked: {total_count}",
        f"- High severity incidents: {high_count}",
        f"- Most frequent threat type: {dominant_threat}",
        f"- Most active region: {dominant_region}",
        "",
        "KEY DEVELOPMENTS",
    ]

    top_items = df[df["severity"] == "High"].head(5)
    if top_items.empty:
        top_items = df.head(5)

    for _, row in top_items.iterrows():
        lines.append(
            f"- [{row['severity']}] {row['title']} ({row['location']}, {row['source']})"
        )

    sector_line = ", ".join(df["sector"].value_counts().head(4).index.tolist()) if not df.empty else "N/A"

    lines.extend([
        "",
        "RISK OUTLOOK",
        f"- Current exposure spans: {sector_line}",
        "- Elevated monitoring is recommended where critical infrastructure, healthcare, finance, transport, or government-linked services are affected.",
        "",
        "ANALYST JUDGEMENT",
        "The current operating picture indicates a mixed environment spanning cyber intrusion, infrastructure disruption, public disorder, and selective regional conflict pressure. Priority monitoring should focus on incidents with operational continuity implications, executive visibility, or cross-sector contagion risk.",
        "",
        "RECOMMENDED ACTIONS",
        "- Prioritise high-severity incidents for immediate validation and impact assessment.",
        "- Review credential abuse, phishing, ransomware, and service outage indicators across relevant environments.",
        "- Monitor transport, venue, and staff safety implications where civil unrest or conflict indicators are present.",
        "- Maintain executive situational awareness with recurring brief updates.",
    ])

    return "\n".join(lines)


def render_brief_panel(text):
    safe_text = html.escape(text).replace("\n", "<br>")
    st.markdown(f"<div class='brief-panel'>{safe_text}</div>", unsafe_allow_html=True)


def convert_df_to_csv(df):
    export_df = df.copy()
    if "published_dt" in export_df.columns:
        export_df["published_dt"] = export_df["published_dt"].dt.strftime("%Y-%m-%d %H:%M:%S")
    if "mitre_tags" in export_df.columns:
        export_df["mitre_tags"] = export_df["mitre_tags"].apply(lambda x: " | ".join(x) if isinstance(x, list) else x)
    return export_df.to_csv(index=False).encode("utf-8")


@st.cache_data(ttl=900, show_spinner=False)
def fetch_news_live(api_key, query, page_size=40):
    if not api_key:
        return []

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])
    except Exception:
        return []


def build_dataframe(articles):
    rows = []

    for article in articles:
        title = clean_text(article.get("title", "Untitled"))
        description = clean_text(article.get("description", ""))
        source = clean_text(article.get("source", {}).get("name", "Unknown"))
        url = clean_text(article.get("url", ""))
        published = clean_text(article.get("publishedAt", ""))

        combined_text = f"{title}. {description}".strip()
        location = extract_location(combined_text)
        lat, lon = location_to_coords(location)
        threat_type = infer_threat_type(combined_text)
        sector = infer_sector(combined_text)
        score = severity_score(combined_text)
        severity = severity_label(score)
        mitre_tags = map_to_mitre(combined_text)
        actor = generate_actor_profile(combined_text)

        published_dt = pd.to_datetime(published, errors="coerce", utc=True)
        if pd.isna(published_dt):
            published_dt = pd.Timestamp.now(tz="UTC")

        rows.append({
            "title": title,
            "description": description,
            "source": source,
            "url": url if url else "#",
            "publishedAt": published,
            "published_dt": published_dt,
            "location": location,
            "lat": lat,
            "lon": lon,
            "region": infer_region(location),
            "threat_type": threat_type,
            "sector": sector,
            "severity_score": score,
            "severity": severity,
            "mitre_tags": mitre_tags,
            "actor_name": actor["actor"],
            "actor_motivation": actor["motivation"],
            "actor_capability": actor["capability"],
            "actor_ttp": actor["ttp"],
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df = df.sort_values("published_dt", ascending=False).reset_index(drop=True)
    df["hour_bucket"] = df["published_dt"].dt.floor("h")
    df["queue_priority"] = df["severity_score"].rank(method="dense", ascending=False).astype(int)
    df["detection_summary"] = df.apply(generate_detection_summary, axis=1)
    return df


def build_kpi_card(label, value, subtext, smaller=False):
    font_size = "1.45rem" if smaller else "2rem"
    return f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="font-size:{font_size};">{value}</div>
            <div class="metric-sub">{subtext}</div>
        </div>
    """


def build_map(df, heatmap=False):
    base_map = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    if df.empty:
        return base_map

    cluster = MarkerCluster().add_to(base_map)

    for _, row in df.iterrows():
        popup_html = f"""
        <div style="min-width:260px;">
            <b>{html.escape(row['title'])}</b><br>
            <small>{html.escape(row['source'])}</small><br><br>
            <b>Location:</b> {html.escape(row['location'])}<br>
            <b>Threat:</b> {html.escape(row['threat_type'])}<br>
            <b>Severity:</b> {html.escape(row['severity'])} ({row['severity_score']})<br>
            <b>Sector:</b> {html.escape(row['sector'])}<br>
        </div>
        """

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7 if row["severity"] != "High" else 9,
            popup=folium.Popup(popup_html, max_width=350),
            color=severity_color(row["severity"]),
            fill=True,
            fill_opacity=0.85,
        ).add_to(cluster)

    if heatmap:
        heat_data = df[["lat", "lon", "severity_score"]].values.tolist()
        HeatMap(heat_data, radius=16, blur=14, min_opacity=0.35).add_to(base_map)

    return base_map


def get_incident_labels(df, limit=50):
    labels = []
    slice_df = df.head(limit).reset_index(drop=True)
    for i, row in slice_df.iterrows():
        labels.append(f"{i + 1}. {row['title']}")
    return labels

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## Control Centre")

query = st.sidebar.text_input("Threat query", value=DEFAULT_QUERY)
max_articles = st.sidebar.slider("Max articles", 10, 100, 35, 5)
use_live_feed = st.sidebar.toggle("Use live NewsAPI feed", value=True)
use_simulated_fallback = st.sidebar.toggle("Fallback to simulation if feed is empty", value=True)
show_heatmap = st.sidebar.toggle("Enable heatmap overlay", value=False)

NEWSAPI_KEY = get_newsapi_key()

articles = []
data_mode = "Simulation"

if use_live_feed:
    articles = fetch_news_live(NEWSAPI_KEY, query, page_size=max_articles)
    if articles:
        data_mode = "Live NewsAPI"
    elif use_simulated_fallback:
        articles = SIMULATED_INCIDENTS
        data_mode = "Simulation Fallback"
    else:
        articles = []
        data_mode = "No Data"
else:
    articles = SIMULATED_INCIDENTS
    data_mode = "Simulation"

df = build_dataframe(articles)

if df.empty:
    st.markdown(
        """
        <div class="hero-wrap">
            <div class="hero-title">🌍 Global Threat Monitoring Dashboard</div>
            <div class="hero-sub">No data available. Add <code>NEWSAPI_KEY</code> to your Streamlit secrets or enable simulation fallback.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

severity_options = ["High", "Medium", "Low"]
region_options = sorted(df["region"].dropna().unique().tolist())
threat_options = sorted(df["threat_type"].dropna().unique().tolist())
sector_options = sorted(df["sector"].dropna().unique().tolist())

st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")

selected_severity = st.sidebar.multiselect("Severity", severity_options, default=severity_options)
selected_region = st.sidebar.multiselect("Region", region_options, default=region_options)
selected_threat = st.sidebar.multiselect("Threat Type", threat_options, default=threat_options)
selected_sector = st.sidebar.multiselect("Sector", sector_options, default=sector_options)
keyword_filter = st.sidebar.text_input("Keyword filter", value="")

filtered_df = df[
    df["severity"].isin(selected_severity)
    & df["region"].isin(selected_region)
    & df["threat_type"].isin(selected_threat)
    & df["sector"].isin(selected_sector)
].copy()

if keyword_filter.strip():
    term = keyword_filter.strip().lower()
    filtered_df = filtered_df[
        filtered_df["title"].str.lower().str.contains(term, na=False)
        | filtered_df["description"].str.lower().str.contains(term, na=False)
        | filtered_df["location"].str.lower().str.contains(term, na=False)
        | filtered_df["source"].str.lower().str.contains(term, na=False)
    ].copy()

filtered_df = filtered_df.sort_values(
    ["severity_score", "published_dt"],
    ascending=[False, False]
).reset_index(drop=True)

# =========================================================
# HERO
# =========================================================
st.markdown(
    f"""
    <div class="hero-wrap">
        <div class="hero-title">🌍 Global Threat Monitoring Dashboard</div>
        <div class="hero-sub">
            Executive-grade OSINT monitoring with live triage, incident drill-down,
            MITRE enrichment, simulated SOC workflow, and exportable intelligence briefing.
        </div>
        <div style="text-align:center;">
            <span class="mode-pill">Mode: {html.escape(data_mode)}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# KPI CARDS
# =========================================================
total_incidents = len(filtered_df)
high_count = int((filtered_df["severity"] == "High").sum()) if not filtered_df.empty else 0
avg_score = round(filtered_df["severity_score"].mean(), 1) if not filtered_df.empty else 0
top_region = filtered_df["region"].mode().iloc[0] if not filtered_df.empty else "N/A"
dominant_threat = filtered_df["threat_type"].mode().iloc[0] if not filtered_df.empty else "N/A"

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(
        build_kpi_card("Tracked Incidents", total_incidents, "Post-filter incident count"),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        build_kpi_card("High Severity", high_count, "Immediate analyst attention"),
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        build_kpi_card("Average Risk Score", avg_score, "Composite severity estimate"),
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        build_kpi_card("Top Region", top_region, "Most active operating area", smaller=True),
        unsafe_allow_html=True,
    )
with c5:
    st.markdown(
        build_kpi_card("Dominant Threat", dominant_threat, "Most common incident class", smaller=True),
        unsafe_allow_html=True,
    )

st.markdown("")

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Alert Triage", "Incident Drill-Down", "Detections + MITRE", "Exports"]
)

# =========================================================
# TAB 1 - OVERVIEW
# =========================================================
with tab1:
    left, right = st.columns([1.45, 1])

    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Threat Activity Timeline")

        timeline_counts = (
            filtered_df.groupby("hour_bucket").size().reset_index(name="incident_count")
            if not filtered_df.empty else pd.DataFrame(columns=["hour_bucket", "incident_count"])
        )

        if not timeline_counts.empty:
            fig_timeline = px.line(
                timeline_counts,
                x="hour_bucket",
                y="incident_count",
                markers=True,
            )
            fig_timeline.update_traces(line=dict(width=3))
            fig_timeline.update_layout(
                template="plotly_dark",
                height=360,
                margin=dict(l=20, r=20, t=10, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Time",
                yaxis_title="Incident Count",
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info("No timeline data available for the current filters.")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Global Incident Map")
        global_map = build_map(filtered_df, heatmap=show_heatmap)
        st_folium(global_map, width=None, height=530, returned_objects=[])
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Threat Type Breakdown")

        threat_counts = filtered_df["threat_type"].value_counts().reset_index()
        threat_counts.columns = ["threat_type", "count"]

        if not threat_counts.empty:
            fig_threat = px.bar(
                threat_counts,
                x="count",
                y="threat_type",
                orientation="h",
            )
            fig_threat.update_layout(
                template="plotly_dark",
                height=320,
                margin=dict(l=20, r=20, t=10, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Count",
                yaxis_title="",
            )
            st.plotly_chart(fig_threat, use_container_width=True)
        else:
            st.info("No threat data available.")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Sector Exposure")

        sector_counts = filtered_df["sector"].value_counts().reset_index()
        sector_counts.columns = ["sector", "count"]

        if not sector_counts.empty:
            fig_sector = px.pie(
                sector_counts,
                names="sector",
                values="count",
                hole=0.55,
            )
            fig_sector.update_layout(
                template="plotly_dark",
                height=320,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_sector, use_container_width=True)
        else:
            st.info("No sector data available.")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Executive Snapshot")
        st.markdown(
            f"""
            <div class="small-muted">
                <b>Dominant threat pattern:</b> {html.escape(dominant_threat)}<br><br>
                <b>Priority region:</b> {html.escape(top_region)}<br><br>
                <b>Analyst note:</b> Validate high-severity items first where transport, healthcare,
                finance, cloud infrastructure, or government-linked services are involved.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TAB 2 - ALERT TRIAGE
# =========================================================
with tab2:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Auto-Prioritised Alert Queue")
    st.caption("Sorted by severity score and recency.")

    queue_view = filtered_df.head(12)

    for idx, row in queue_view.iterrows():
        alert_class = (
            "alert-high" if row["severity"] == "High"
            else "alert-medium" if row["severity"] == "Medium"
            else "alert-low"
        )
        badge_class = (
            "badge-high" if row["severity"] == "High"
            else "badge-medium" if row["severity"] == "Medium"
            else "badge-low"
        )
        mitre_first = row["mitre_tags"][0] if row["mitre_tags"] else "Unmapped"

        st.markdown(
            f"""
            <div class="alert-card {alert_class}">
                <div style="display:flex; justify-content:space-between; gap:1rem; align-items:flex-start;">
                    <div style="flex:1;">
                        <div style="font-size:1.05rem; font-weight:800; color:white;">{html.escape(row["title"])}</div>
                        <div class="small-muted" style="margin-top:0.35rem;">
                            {html.escape(row["source"])} • {html.escape(row["location"])} • {row["published_dt"].strftime("%d %b %Y %H:%M UTC")}
                        </div>
                        <div style="margin-top:0.45rem;">
                            <span class="badge {badge_class}">{row["severity"]}</span>
                            <span class="badge badge-neutral">{html.escape(row["threat_type"])}</span>
                            <span class="badge badge-neutral">{html.escape(row["sector"])}</span>
                            <span class="badge badge-neutral">{html.escape(mitre_first)}</span>
                        </div>
                        <div class="small-muted" style="margin-top:0.65rem;">
                            {html.escape(row["detection_summary"])}
                        </div>
                    </div>
                    <div style="text-align:right; min-width:120px;">
                        <div class="small-muted">Score</div>
                        <div style="font-size:1.7rem; font-weight:800; color:white;">{row["severity_score"]}</div>
                        <div class="small-muted">Priority #{row["queue_priority"]}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        b1, b2, b3 = st.columns([1, 1, 1.2])
        with b1:
            st.button(f"Escalate incident #{idx}", key=f"escalate_{idx}")
        with b2:
            st.button(f"Assign to L2 #{idx}", key=f"assign_{idx}")
        with b3:
            st.link_button(f"Open source #{idx}", row["url"])

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("")

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Structured Queue Table")

    queue_table = filtered_df[[
        "published_dt", "title", "location", "region",
        "threat_type", "sector", "severity", "severity_score", "queue_priority"
    ]].copy()

    if not queue_table.empty:
        queue_table["published_dt"] = queue_table["published_dt"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(queue_table, use_container_width=True, hide_index=True)
    else:
        st.info("No queue data available.")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TAB 3 - DRILL DOWN
# =========================================================
with tab3:
    if filtered_df.empty:
        st.info("No incidents available for drill-down.")
    else:
        incident_labels = get_incident_labels(filtered_df, limit=50)
        selected_label = st.selectbox("Select an incident", incident_labels)
        selected_index = int(selected_label.split(".")[0]) - 1
        row = filtered_df.iloc[selected_index]

        left, right = st.columns([1.25, 1])

        with left:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Incident Overview")
            st.markdown(f"### {row['title']}")
            st.markdown(
                f"""
                <div class="small-muted">
                    <b>Source:</b> {html.escape(row['source'])}<br>
                    <b>Published:</b> {row['published_dt'].strftime("%d %b %Y %H:%M UTC")}<br>
                    <b>Location:</b> {html.escape(row['location'])}<br>
                    <b>Region:</b> {html.escape(row['region'])}<br>
                    <b>Threat Type:</b> {html.escape(row['threat_type'])}<br>
                    <b>Sector:</b> {html.escape(row['sector'])}<br>
                    <b>Severity:</b> {html.escape(row['severity'])} ({row['severity_score']}/100)
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("#### Description")
            st.write(row["description"] if row["description"] else "No additional description provided.")

            st.markdown("#### Analyst Assessment")
            st.write(row["detection_summary"])

            st.markdown("#### MITRE Mapping")
            for tag in row["mitre_tags"]:
                st.markdown(f"- {tag}")

            st.link_button("Open source article", row["url"])
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("")

            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("SIEM / SOC Log View")
            for line in simulated_log_lines(row):
                st.markdown(f"<div class='log-box'>{html.escape(line)}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Threat Actor Profile")
            st.markdown(
                f"""
                <div class="small-muted">
                    <b>Actor cluster:</b> {html.escape(row['actor_name'])}<br><br>
                    <b>Motivation:</b> {html.escape(row['actor_motivation'])}<br><br>
                    <b>Capability:</b> {html.escape(row['actor_capability'])}<br><br>
                    <b>Typical behaviour:</b> {html.escape(row['actor_ttp'])}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("")

            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Single Incident Map")
            incident_map = folium.Map(
                location=[row["lat"], row["lon"]],
                zoom_start=4 if row["location"] != "Global" else 2,
                tiles="CartoDB dark_matter"
            )
            folium.Marker(
                [row["lat"], row["lon"]],
                popup=row["title"],
                tooltip=row["location"],
            ).add_to(incident_map)
            st_folium(incident_map, width=None, height=360, returned_objects=[])
            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TAB 4 - DETECTIONS + MITRE
# =========================================================
with tab4:
    left, right = st.columns([1, 1])

    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("MITRE Technique Coverage")

        mitre_exploded = filtered_df[["mitre_tags"]].explode("mitre_tags") if not filtered_df.empty else pd.DataFrame(columns=["mitre_tags"])
        mitre_counts = mitre_exploded["mitre_tags"].value_counts().reset_index()
        if not mitre_counts.empty:
            mitre_counts.columns = ["technique", "count"]

            fig_mitre = px.bar(
                mitre_counts,
                x="technique",
                y="count",
            )
            fig_mitre.update_layout(
                template="plotly_dark",
                height=380,
                margin=dict(l=20, r=20, t=10, b=90),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Technique",
                yaxis_title="Matched Incidents",
            )
            st.plotly_chart(fig_mitre, use_container_width=True)
        else:
            st.info("No MITRE mappings available.")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Detection Rules Simulation")

        detection_rows = []
        for _, row in filtered_df.head(20).iterrows():
            detection_rows.append({
                "rule_name": f"{row['threat_type']} Detection",
                "trigger_summary": row["title"][:95],
                "severity": row["severity"],
                "mapped_technique": row["mitre_tags"][0] if row["mitre_tags"] else "Unmapped",
                "recommended_action": "Escalate to L2" if row["severity"] == "High" else "Monitor / validate context",
            })

        detection_df = pd.DataFrame(detection_rows)
        if not detection_df.empty:
            st.dataframe(detection_df, use_container_width=True, hide_index=True)
        else:
            st.info("No detection rules generated.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Severity Distribution")

        sev_counts = (
            filtered_df["severity"]
            .value_counts()
            .reindex(["High", "Medium", "Low"])
            .fillna(0)
            .reset_index()
        )
        sev_counts.columns = ["severity", "count"]

        fig_sev = px.funnel_area(
            sev_counts,
            names="severity",
            values="count",
        )
        fig_sev.update_layout(
            template="plotly_dark",
            height=380,
            margin=dict(l=20, r=20, t=10, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_sev, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Regional Threat Load")

        region_counts = filtered_df["region"].value_counts().reset_index()
        if not region_counts.empty:
            region_counts.columns = ["region", "count"]
            fig_region = go.Figure(
                data=[
                    go.Bar(
                        x=region_counts["region"],
                        y=region_counts["count"],
                    )
                ]
            )
            fig_region.update_layout(
                template="plotly_dark",
                height=250,
                margin=dict(l=20, r=20, t=10, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Region",
                yaxis_title="Incidents",
            )
            st.plotly_chart(fig_region, use_container_width=True)
        else:
            st.info("No regional data available.")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Analyst Recommendations")
        st.markdown(
            """
            <div class="small-muted">
                <b>For High severity:</b> validate impact immediately, identify affected entities,
                determine whether executive escalation is required, and assess continuity implications.<br><br>
                <b>For Medium severity:</b> confirm credibility, map likely operational impact,
                enrich with contextual reporting, and track for amplification.<br><br>
                <b>For Low severity:</b> retain for situational awareness and future correlation.<br><br>
                <b>Interview line:</b> this dashboard simulates a modern SOC / intelligence workflow
                by combining ingestion, enrichment, classification, prioritisation, drill-down analysis,
                and executive reporting in one interface.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TAB 5 - EXPORTS
# =========================================================
with tab5:
    left, right = st.columns([1, 1])

    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Generated Intelligence Brief")
        brief_text = build_brief(filtered_df)
        render_brief_panel(brief_text)

        st.download_button(
            label="Download intelligence brief (.txt)",
            data=brief_text,
            file_name="global_threat_intelligence_brief.txt",
            mime="text/plain",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Export Incident Dataset")

        preview_cols = [
            "published_dt", "title", "source", "location", "region",
            "threat_type", "sector", "severity", "severity_score", "queue_priority"
        ]
        preview_df = filtered_df[preview_cols].copy() if not filtered_df.empty else pd.DataFrame(columns=preview_cols)

        if not preview_df.empty:
            preview_df["published_dt"] = preview_df["published_dt"].dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(preview_df.head(20), use_container_width=True, hide_index=True)
        else:
            st.info("No incident data available for export preview.")

        csv_data = convert_df_to_csv(filtered_df)
        st.download_button(
            label="Download filtered incidents (.csv)",
            data=csv_data,
            file_name="filtered_threat_incidents.csv",
            mime="text/csv",
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Setup")
        st.code(
            '''# .streamlit/secrets.toml
NEWSAPI_KEY = "your_key_here"
''',
            language="toml",
        )
        st.markdown(
            """
            <div class="small-muted">
                This app is designed to keep running even if the live feed returns no articles.
                When enabled, it automatically falls back to simulation mode so the UI still works
                during demos, portfolio reviews, and recruiter walkthroughs.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown(
    "<div class='footer-note'>Built to simulate intelligence monitoring, alert triage, drill-down analysis, MITRE enrichment, and executive briefing workflows in one polished interface.</div>",
    unsafe_allow_html=True,
)
