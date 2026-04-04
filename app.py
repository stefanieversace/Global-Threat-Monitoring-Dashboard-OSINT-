import math
import random
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Threat Operations Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# THEME / CSS
# =========================================================
CUSTOM_CSS = """
<style>
:root {
    --bg: #070b10;
    --bg-2: #0b1118;
    --panel: rgba(11, 17, 24, 0.92);
    --panel-2: rgba(15, 22, 31, 0.96);
    --border: rgba(255,255,255,0.075);
    --border-strong: rgba(141,183,255,0.22);
    --text: #e7edf5;
    --muted: #95a4b8;
    --accent: #8db7ff;
    --accent-soft: rgba(141,183,255,0.12);
    --critical: #ff4d6d;
    --high: #ff8c42;
    --medium: #ffd166;
    --low: #06d6a0;
    --shadow: 0 18px 40px rgba(0,0,0,0.34);
    --radius-xl: 22px;
    --radius-lg: 18px;
    --radius-md: 14px;
}

html, body, .stApp {
    background:
        radial-gradient(circle at top left, rgba(95,143,255,0.12), transparent 28%),
        radial-gradient(circle at top right, rgba(141,183,255,0.08), transparent 22%),
        linear-gradient(180deg, #05080c 0%, #0a0e14 100%);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
}

#MainMenu, header, footer {
    visibility: hidden;
}

.block-container {
    max-width: 1680px;
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(9,13,18,0.98) 0%, rgba(10,16,22,0.98) 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}

.hero {
    background:
        linear-gradient(135deg, rgba(95,143,255,0.14), rgba(255,255,255,0.015)),
        rgba(8, 12, 18, 0.94);
    border: 1px solid rgba(141,183,255,0.16);
    border-radius: 26px;
    padding: 24px 26px;
    box-shadow: var(--shadow);
    position: relative;
    overflow: hidden;
}

.hero:before {
    content: "";
    position: absolute;
    left: -60px;
    top: -60px;
    width: 280px;
    height: 280px;
    background: radial-gradient(circle, rgba(141,183,255,0.15), transparent 68%);
    pointer-events: none;
}

.eyebrow {
    color: var(--accent);
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}

.hero-title {
    font-size: 2.15rem;
    font-weight: 800;
    line-height: 1.02;
    letter-spacing: -0.03em;
    margin-bottom: 0.45rem;
}

.hero-sub {
    color: var(--muted);
    font-size: 0.98rem;
    line-height: 1.6;
    max-width: 1000px;
}

.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
}

.chip {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    color: var(--text);
    padding: 7px 11px;
    border-radius: 999px;
    font-size: 0.82rem;
    transition: 180ms ease;
}

.chip:hover {
    transform: translateY(-1px);
    border-color: rgba(141,183,255,0.24);
}

.section-kicker {
    color: var(--muted);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    margin-bottom: 0.45rem;
}

.section-title {
    color: var(--text);
    font-size: 1.04rem;
    font-weight: 700;
    margin-bottom: 0.7rem;
}

.panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 18px;
    box-shadow: var(--shadow);
    transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
}

.panel:hover {
    transform: translateY(-2px);
    border-color: rgba(141,183,255,0.18);
}

.panel-tight {
    padding: 14px 16px;
}

.metric-shell {
    background: linear-gradient(180deg, rgba(255,255,255,0.025), rgba(255,255,255,0.015));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 12px 14px;
    box-shadow: var(--shadow);
}

.queue-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    background: rgba(255,255,255,0.018);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 12px 14px;
    margin-bottom: 10px;
    transition: all 180ms ease;
}

.queue-row:hover {
    transform: translateX(3px);
    border-color: rgba(141,183,255,0.22);
    background: rgba(141,183,255,0.05);
}

.queue-left {
    min-width: 0;
}

.queue-title {
    font-weight: 700;
    color: var(--text);
    margin-bottom: 3px;
}

.queue-sub {
    color: var(--muted);
    font-size: 0.87rem;
    line-height: 1.4;
}

.badge {
    display: inline-flex;
    align-items: center;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 800;
    border: 1px solid transparent;
}

.badge-critical {
    background: rgba(255,77,109,0.12);
    color: #ff97ac;
    border-color: rgba(255,77,109,0.22);
}

.badge-high {
    background: rgba(255,140,66,0.12);
    color: #ffb07f;
    border-color: rgba(255,140,66,0.22);
}

.badge-medium {
    background: rgba(255,209,102,0.12);
    color: #ffd98f;
    border-color: rgba(255,209,102,0.22);
}

.badge-low {
    background: rgba(6,214,160,0.12);
    color: #75efcb;
    border-color: rgba(6,214,160,0.22);
}

.log-shell {
    background: #06090d;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 12px 14px;
    max-height: 400px;
    overflow-y: auto;
}

.log-line {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.82rem;
    line-height: 1.55;
    color: #c7d3e0;
    border-bottom: 1px dashed rgba(255,255,255,0.05);
    padding: 6px 0;
    white-space: pre-wrap;
}

.log-time { color: #8db7ff; }
.log-src { color: #ffd166; }
.log-good { color: #06d6a0; }
.log-bad { color: #ff6b6b; }
.log-mid { color: #c5a3ff; }

.info-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}

.info-tile {
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 10px 12px;
    background: rgba(255,255,255,0.02);
}

.info-label {
    color: var(--muted);
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.info-value {
    color: var(--text);
    font-size: 0.96rem;
    font-weight: 700;
    margin-top: 4px;
}

.timeline-item {
    position: relative;
    padding-left: 18px;
    margin-bottom: 13px;
}

.timeline-item:before {
    content: "";
    position: absolute;
    left: 0;
    top: 7px;
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--accent);
    box-shadow: 0 0 14px rgba(141,183,255,0.65);
}

.timeline-time {
    color: var(--muted);
    font-size: 0.8rem;
    margin-bottom: 2px;
}

.timeline-text {
    color: var(--text);
    font-size: 0.92rem;
    line-height: 1.5;
}

.small-note {
    color: var(--muted);
    font-size: 0.82rem;
    line-height: 1.5;
}

.card-label {
    color: var(--muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 4px;
}

.actor-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.025), rgba(255,255,255,0.012));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 16px;
}

.stButton > button {
    width: 100%;
    border: 1px solid rgba(255,255,255,0.10);
    background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.028));
    color: var(--text);
    border-radius: 14px;
    padding: 0.64rem 0.95rem;
    font-weight: 700;
    transition: all 180ms ease;
}

.stButton > button:hover {
    border-color: rgba(141,183,255,0.28);
    transform: translateY(-1px);
    box-shadow: 0 10px 24px rgba(0,0,0,0.28);
}

div[data-testid="stMetric"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.025), rgba(255,255,255,0.015));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 10px 14px;
    box-shadow: var(--shadow);
}

div[data-testid="stMetricLabel"] {
    color: var(--muted);
}

div[data-testid="stMetricValue"] {
    color: var(--text);
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.03);
    border-radius: 12px 12px 0 0;
    padding: 10px 14px;
    color: var(--muted);
}

.stTabs [aria-selected="true"] {
    color: var(--text) !important;
    background: rgba(141,183,255,0.08) !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =========================================================
# CONSTANTS / DATA MODELS
# =========================================================
SEVERITY_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
SEVERITY_COLORS = {
    "Critical": "#ff4d6d",
    "High": "#ff8c42",
    "Medium": "#ffd166",
    "Low": "#06d6a0",
}
SEVERITY_RGBA = {
    "Critical": "rgba(255,77,109,0.92)",
    "High": "rgba(255,140,66,0.92)",
    "Medium": "rgba(255,209,102,0.90)",
    "Low": "rgba(6,214,160,0.88)",
}

MITRE_TECHNIQUES = {
    "Phishing Campaign": ["T1566", "T1204"],
    "Credential Stuffing": ["T1110", "T1078"],
    "Malware Beacon": ["T1105", "T1071"],
    "Ransomware Staging": ["T1486", "T1027"],
    "Cloud Privilege Escalation": ["T1098", "T1068"],
    "Suspicious OAuth Grant": ["T1528", "T1078"],
    "Impossible Travel Login": ["T1078", "T1110"],
    "Data Exfiltration Spike": ["T1041", "T1020"],
}

ACTOR_LIBRARY = {
    "Phishing Campaign": {
        "actor": "Hollow Meridian",
        "profile": "Financially motivated intrusion cluster favouring credential theft via spoofed productivity portals and post-login session hijack workflows.",
        "ioc": ["login-security-check[.]com", "185.193.88.14", "mail-auth-review[.]net"],
        "tactics": ["Initial Access", "Execution", "Credential Access"],
    },
    "Credential Stuffing": {
        "actor": "Grey Torrent",
        "profile": "Automation-heavy credential abuse set targeting reused passwords against media, retail, and SaaS logins using rotating residential proxies.",
        "ioc": ["45.83.122.6", "198.23.214.18", "proxy-auth-edge[.]xyz"],
        "tactics": ["Credential Access", "Persistence", "Defense Evasion"],
    },
    "Malware Beacon": {
        "actor": "Night Comet",
        "profile": "Modular malware operator leveraging staged payload retrieval and low-and-slow beaconing to blend into normal outbound traffic patterns.",
        "ioc": ["cdn-sync-center[.]com", "91.240.118.77", "update-edge-worker[.]io"],
        "tactics": ["Command and Control", "Execution", "Persistence"],
    },
    "Ransomware Staging": {
        "actor": "Black Lantern",
        "profile": "Ransomware affiliate profile using living-off-the-land tooling before detonation, with rapid privilege expansion and backup targeting.",
        "ioc": ["sharepoint-docs-help[.]com", "77.91.124.55", "svc-backup-sync[.]ru"],
        "tactics": ["Lateral Movement", "Impact", "Exfiltration"],
    },
    "Cloud Privilege Escalation": {
        "actor": "Azure Wisp",
        "profile": "Cloud-native intrusion activity focused on IAM abuse, over-permissioned roles, and inherited trust relationships across tenants.",
        "ioc": ["api-console-check[.]app", "34.91.12.118", "token-metadata-node[.]site"],
        "tactics": ["Privilege Escalation", "Persistence", "Discovery"],
    },
    "Suspicious OAuth Grant": {
        "actor": "Velvet Token",
        "profile": "Consent-phishing activity using malicious application grants to obtain durable mailbox, files, and profile access without malware deployment.",
        "ioc": ["verify-m365-access[.]co", "oauth-drive-view[.]net", "172.104.44.29"],
        "tactics": ["Persistence", "Collection", "Credential Access"],
    },
    "Impossible Travel Login": {
        "actor": "Signal Rift",
        "profile": "Account takeover tradecraft focused on session theft and rapid geo-distributed access to high-value identities.",
        "ioc": ["203.0.113.44", "198.51.100.91", "auth-session-check[.]cc"],
        "tactics": ["Valid Accounts", "Defense Evasion", "Discovery"],
    },
    "Data Exfiltration Spike": {
        "actor": "Quiet Vale",
        "profile": "Data theft profile using sanctioned services and compressed archives to reduce detection signal before outbound transfer.",
        "ioc": ["mega-share-sync[.]org", "104.244.73.8", "archive-uploader[.]cloud"],
        "tactics": ["Collection", "Exfiltration", "Defense Evasion"],
    },
}


# =========================================================
# HELPERS
# =========================================================
def seed_everything(seed: int = 11) -> None:
    random.seed(seed)
    np.random.seed(seed)


seed_everything()


def generate_incidents() -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    rows = [
        {
            "incident_id": "INC-24051",
            "title": "Credential Stuffing",
            "region": "New York, US",
            "lat": 40.7128,
            "lon": -74.0060,
            "severity": "Critical",
            "source": "Identity",
            "status": "Investigating",
            "entities": "SSO / Customer Portal",
            "analyst": "SV-21",
            "confidence": 92,
            "opened_minutes_ago": 18,
            "events": 4821,
            "risk_score": 94,
        },
        {
            "incident_id": "INC-24052",
            "title": "Phishing Campaign",
            "region": "London, UK",
            "lat": 51.5074,
            "lon": -0.1278,
            "severity": "High",
            "source": "Email / OSINT",
            "status": "Triaged",
            "entities": "Executive Mailboxes",
            "analyst": "SV-17",
            "confidence": 88,
            "opened_minutes_ago": 39,
            "events": 915,
            "risk_score": 82,
        },
        {
            "incident_id": "INC-24053",
            "title": "Suspicious OAuth Grant",
            "region": "Dublin, IE",
            "lat": 53.3498,
            "lon": -6.2603,
            "severity": "High",
            "source": "Cloud App Security",
            "status": "Containment",
            "entities": "M365 Tenant",
            "analyst": "SV-09",
            "confidence": 85,
            "opened_minutes_ago": 62,
            "events": 304,
            "risk_score": 79,
        },
        {
            "incident_id": "INC-24054",
            "title": "Malware Beacon",
            "region": "Berlin, DE",
            "lat": 52.5200,
            "lon": 13.4050,
            "severity": "Medium",
            "source": "EDR / Proxy",
            "status": "Investigating",
            "entities": "Finance Endpoint",
            "analyst": "SV-14",
            "confidence": 73,
            "opened_minutes_ago": 96,
            "events": 227,
            "risk_score": 66,
        },
        {
            "incident_id": "INC-24055",
            "title": "Impossible Travel Login",
            "region": "Singapore, SG",
            "lat": 1.3521,
            "lon": 103.8198,
            "severity": "Medium",
            "source": "Identity",
            "status": "Escalated",
            "entities": "Privileged Account",
            "analyst": "SV-04",
            "confidence": 77,
            "opened_minutes_ago": 124,
            "events": 118,
            "risk_score": 69,
        },
        {
            "incident_id": "INC-24056",
            "title": "Data Exfiltration Spike",
            "region": "Sydney, AU",
            "lat": -33.8688,
            "lon": 151.2093,
            "severity": "Critical",
            "source": "DLP / Network",
            "status": "Investigating",
            "entities": "Product Design Share",
            "analyst": "SV-31",
            "confidence": 95,
            "opened_minutes_ago": 11,
            "events": 1312,
            "risk_score": 97,
        },
        {
            "incident_id": "INC-24057",
            "title": "Cloud Privilege Escalation",
            "region": "San Francisco, US",
            "lat": 37.7749,
            "lon": -122.4194,
            "severity": "High",
            "source": "CloudTrail / IAM",
            "status": "Investigating",
            "entities": "AWS Production",
            "analyst": "SV-28",
            "confidence": 89,
            "opened_minutes_ago": 54,
            "events": 687,
            "risk_score": 84,
        },
        {
            "incident_id": "INC-24058",
            "title": "Ransomware Staging",
            "region": "Paris, FR",
            "lat": 48.8566,
            "lon": 2.3522,
            "severity": "Critical",
            "source": "EDR / AD",
            "status": "Containment",
            "entities": "Windows Server Cluster",
            "analyst": "SV-12",
            "confidence": 91,
            "opened_minutes_ago": 27,
            "events": 1441,
            "risk_score": 96,
        },
    ]
    df = pd.DataFrame(rows)
    df["opened_at"] = df["opened_minutes_ago"].apply(lambda x: now - timedelta(minutes=int(x)))
    df["sev_rank"] = df["severity"].map(SEVERITY_ORDER)
    df["mitre"] = df["title"].map(MITRE_TECHNIQUES)
    df = df.sort_values(["sev_rank", "risk_score"], ascending=[False, False]).reset_index(drop=True)
    return df


def generate_live_alert() -> dict:
    return {
        "time": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        "alert": random.choice(list(MITRE_TECHNIQUES.keys())),
        "severity": random.choice(["Low", "Medium", "High", "Critical"]),
        "region": random.choice([
            "New York, US", "London, UK", "Berlin, DE", "Singapore, SG",
            "Sydney, AU", "Paris, FR", "Dublin, IE", "San Francisco, US"
        ]),
    }


def generate_timeline(incident: pd.Series) -> list[dict]:
    base = incident["opened_at"]
    return [
        {"time": base.strftime("%H:%M UTC"), "event": f"Detection triggered for {incident['title']} via {incident['source']} telemetry."},
        {"time": (base + timedelta(minutes=4)).strftime("%H:%M UTC"), "event": f"Correlation linked activity to {incident['events']:,} raw events across {incident['entities']}."},
        {"time": (base + timedelta(minutes=8)).strftime("%H:%M UTC"), "event": f"MITRE mapping applied: {', '.join(incident['mitre'])}."},
        {"time": (base + timedelta(minutes=13)).strftime("%H:%M UTC"), "event": f"Analyst {incident['analyst']} enriched with geo, IOC, and asset context."},
        {"time": (base + timedelta(minutes=17)).strftime("%H:%M UTC"), "event": f"Status updated to {incident['status']}; containment recommendation prepared."},
    ]


def generate_logs(incident: pd.Series, count: int = 18) -> list[str]:
    base = incident["opened_at"]
    sources = ["proxy", "identity", "edr", "cloud", "osint", "mail", "network"]
    hosts = ["prod-auth-01", "fin-lt-22", "exec-mbx-03", "dc-core-01", "edge-app-07"]
    actions = [
        "suspicious sign-in evaluated",
        "ioc match observed",
        "outbound beacon classified",
        "token consent anomaly",
        "privilege expansion detected",
        "archive upload spike flagged",
        "email delivery burst correlated",
    ]
    out = []
    for i in range(count):
        ts = (base + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S")
        src = random.choice(sources).upper()
        host = random.choice(hosts)
        action = random.choice(actions)
        verdict = random.choice(["ALLOW", "REVIEW", "BLOCK", "ENRICH"])
        verdict_class = (
            "log-good" if verdict == "ALLOW"
            else "log-bad" if verdict == "BLOCK"
            else "log-mid" if verdict == "ENRICH"
            else "log-src"
        )
        out.append(
            f'<div class="log-line"><span class="log-time">{ts}</span>  <span class="log-src">[{src}]</span>  host={host}  event="{action}"  incident={incident["incident_id"]}  verdict=<span class="{verdict_class}">{verdict}</span></div>'
        )
    return out


def severity_badge(severity: str) -> str:
    cls = {
        "Critical": "badge badge-critical",
        "High": "badge badge-high",
        "Medium": "badge badge-medium",
        "Low": "badge badge-low",
    }[severity]
    return f'<span class="{cls}">{severity}</span>'


def build_mitre_matrix(df: pd.DataFrame) -> pd.DataFrame:
    tactics = [
        "Initial Access", "Execution", "Persistence", "Privilege Escalation",
        "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement",
        "Collection", "Command and Control", "Exfiltration", "Impact",
    ]
    rows = []
    for sev in ["Critical", "High", "Medium", "Low"]:
        subset = df[df["severity"] == sev]
        actor_tactics = []
        for title in subset["title"]:
            actor_tactics.extend(ACTOR_LIBRARY[title]["tactics"])
        row = {t: actor_tactics.count(t) for t in tactics}
        row["Severity"] = sev
        rows.append(row)
    return pd.DataFrame(rows).set_index("Severity")


def generate_ai_assessment(incident: pd.Series) -> str:
    actor = ACTOR_LIBRARY[incident["title"]]
    return (
        f"{incident['incident_id']} is currently assessed as a {incident['severity'].lower()} priority event. "
        f"The pattern is most consistent with {incident['title'].lower()} activity affecting {incident['entities']} in {incident['region']}. "
        f"Observed telemetry from {incident['source']} aligns with MITRE techniques {', '.join(incident['mitre'])}. "
        f"Linked enrichment suggests overlap with the {actor['actor']} profile. "
        f"Immediate focus should remain on scoping affected identities and assets, validating whether access is ongoing, "
        f"and preserving a clear path to containment if the event expands."
    )


def filtered_incidents(df: pd.DataFrame, severities: list[str], sources: list[str], query: str) -> pd.DataFrame:
    out = df.copy()
    if severities:
        out = out[out["severity"].isin(severities)]
    if sources:
        out = out[out["source"].isin(sources)]
    if query.strip():
        q = query.lower().strip()
        mask = (
            out["title"].str.lower().str.contains(q)
            | out["incident_id"].str.lower().str.contains(q)
            | out["region"].str.lower().str.contains(q)
            | out["entities"].str.lower().str.contains(q)
            | out["status"].str.lower().str.contains(q)
        )
        out = out[mask]
    return out.sort_values(["sev_rank", "risk_score"], ascending=[False, False]).reset_index(drop=True)


def build_map_figure(df: pd.DataFrame, selected_id: str) -> go.Figure:
    map_df = df.copy()
    pulse = (math.sin(time.time() * 2.0) + 1.0) / 2.0
    map_df["marker_size"] = (map_df["risk_score"] * (0.28 + pulse * 0.05)).clip(lower=14, upper=36)

    fig = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        size="marker_size",
        size_max=38,
        color="severity",
        hover_name="incident_id",
        hover_data={
            "title": True,
            "region": True,
            "severity": True,
            "risk_score": True,
            "lat": False,
            "lon": False,
            "marker_size": False,
        },
        color_discrete_map=SEVERITY_COLORS,
        zoom=1.2,
        height=560,
    )

    # subtle flow lines between incidents for “networked theater” feel
    if len(map_df) > 1:
        ordered = map_df.sort_values("risk_score", ascending=False).reset_index(drop=True)
        for i in range(len(ordered) - 1):
            fig.add_trace(
                go.Scattermapbox(
                    lat=[ordered.loc[i, "lat"], ordered.loc[i + 1, "lat"]],
                    lon=[ordered.loc[i, "lon"], ordered.loc[i + 1, "lon"]],
                    mode="lines",
                    line=dict(width=1.4, color="rgba(141,183,255,0.28)"),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

    # highlight selected incident
    selected = map_df[map_df["incident_id"] == selected_id]
    if not selected.empty:
        r = selected.iloc[0]
        fig.add_trace(
            go.Scattermapbox(
                lat=[r["lat"]],
                lon=[r["lon"]],
                mode="markers",
                marker=dict(
                    size=46,
                    color="rgba(255,255,255,0.16)",
                    opacity=1.0,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.update_traces(
        marker=dict(opacity=0.92),
        selector=dict(mode="markers"),
    )

    fig.update_layout(
        mapbox_style="carto-darkmatter",
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0b0f14",
        plot_bgcolor="#0b0f14",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cfd8e3"),
        ),
    )
    return fig


def build_graph_figure(df: pd.DataFrame) -> go.Figure:
    nodes = []
    edges = []

    incident_positions = {}
    actor_positions = {}
    ioc_positions = {}

    incident_count = len(df)
    incident_radius = 1.25
    actor_radius = 0.55
    ioc_radius = 2.0

    incident_angles = np.linspace(0, 2 * np.pi, incident_count, endpoint=False)

    for idx, (_, row) in enumerate(df.iterrows()):
        incident_id = row["incident_id"]
        actor = ACTOR_LIBRARY[row["title"]]["actor"]
        iocs = ACTOR_LIBRARY[row["title"]]["ioc"]

        ix = incident_radius * np.cos(incident_angles[idx])
        iy = incident_radius * np.sin(incident_angles[idx])
        incident_positions[incident_id] = (ix, iy)

        if actor not in actor_positions:
            angle = (idx / max(1, incident_count)) * 2 * np.pi + 0.3
            actor_positions[actor] = (actor_radius * np.cos(angle), actor_radius * np.sin(angle))

        for j, ioc in enumerate(iocs):
            if ioc not in ioc_positions:
                angle = ((idx + j + 1) / max(1, incident_count + 3)) * 2 * np.pi
                ioc_positions[ioc] = (ioc_radius * np.cos(angle), ioc_radius * np.sin(angle))

        edges.append((actor_positions[actor], (ix, iy), "rgba(141,183,255,0.42)"))
        for ioc in iocs:
            edges.append((ioc_positions[ioc], (ix, iy), "rgba(255,209,102,0.34)"))

    fig = go.Figure()

    for source, target, color in edges:
        fig.add_trace(
            go.Scatter(
                x=[source[0], target[0]],
                y=[source[1], target[1]],
                mode="lines",
                line=dict(color=color, width=1.6),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # incidents
    for _, row in df.iterrows():
        x, y = incident_positions[row["incident_id"]]
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                text=[row["incident_id"]],
                textposition="top center",
                marker=dict(
                    size=24,
                    color=SEVERITY_COLORS[row["severity"]],
                    line=dict(color="rgba(255,255,255,0.75)", width=1),
                ),
                hovertemplate=(
                    f"<b>{row['incident_id']}</b><br>"
                    f"{row['title']}<br>"
                    f"{row['region']}<br>"
                    f"Severity: {row['severity']}<extra></extra>"
                ),
                showlegend=False,
            )
        )

    # actors
    for actor, (x, y) in actor_positions.items():
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                text=[actor],
                textposition="bottom center",
                marker=dict(
                    size=18,
                    color="#8db7ff",
                    line=dict(color="rgba(255,255,255,0.55)", width=1),
                ),
                hovertemplate=f"<b>{actor}</b><br>Threat actor profile<extra></extra>",
                showlegend=False,
            )
        )

    # iocs
    for ioc, (x, y) in ioc_positions.items():
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                text=[ioc],
                textposition="bottom center",
                marker=dict(
                    size=13,
                    color="#ffd166",
                    line=dict(color="rgba(255,255,255,0.45)", width=1),
                ),
                hovertemplate=f"<b>{ioc}</b><br>Indicator of compromise<extra></extra>",
                showlegend=False,
            )
        )

    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="#0b0f14",
        plot_bgcolor="#0b0f14",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def build_mitre_heatmap(df: pd.DataFrame) -> go.Figure:
    matrix = build_mitre_matrix(df)
    fig = go.Figure(
        data=go.Heatmap(
            z=matrix.values,
            x=matrix.columns,
            y=matrix.index,
            colorscale=[
                [0.0, "#101822"],
                [0.25, "#1e2b3d"],
                [0.5, "#38537a"],
                [0.75, "#5f8fff"],
                [1.0, "#8db7ff"],
            ],
            showscale=False,
            hovertemplate="Severity: %{y}<br>Tactic: %{x}<br>Count: %{z}<extra></extra>",
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="#0b0f14",
        plot_bgcolor="#0b0f14",
        font=dict(color="#e7edf5"),
        xaxis=dict(tickangle=-30),
    )
    return fig


# =========================================================
# DATA + STATE
# =========================================================
INCIDENTS = generate_incidents()

if "selected_incident_id" not in st.session_state:
    st.session_state.selected_incident_id = INCIDENTS.iloc[0]["incident_id"]

if "live_alerts" not in st.session_state:
    st.session_state.live_alerts = []

if "operator_log" not in st.session_state:
    st.session_state.operator_log = []

# auto ingest subtle feed
if random.random() < 0.22:
    st.session_state.live_alerts.insert(0, generate_live_alert())


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("### Controls")
    severity_filter = st.multiselect(
        "Severity",
        options=["Critical", "High", "Medium", "Low"],
        default=["Critical", "High", "Medium", "Low"],
    )
    source_filter = st.multiselect(
        "Source",
        options=sorted(INCIDENTS["source"].unique().tolist()),
        default=sorted(INCIDENTS["source"].unique().tolist()),
    )
    search_text = st.text_input("Search incidents", placeholder="INC-24051, OAuth, London...")

FILTERED = filtered_incidents(INCIDENTS, severity_filter, source_filter, search_text)
DISPLAY_DF = FILTERED if not FILTERED.empty else INCIDENTS

if st.session_state.selected_incident_id not in DISPLAY_DF["incident_id"].values:
    st.session_state.selected_incident_id = DISPLAY_DF.iloc[0]["incident_id"]

SELECTED = DISPLAY_DF[DISPLAY_DF["incident_id"] == st.session_state.selected_incident_id].iloc[0]


# =========================================================
# HERO
# =========================================================
now_utc = datetime.now(timezone.utc).strftime("%d %b %Y • %H:%M UTC")
critical_count = int((DISPLAY_DF["severity"] == "Critical").sum())
high_count = int((DISPLAY_DF["severity"] == "High").sum())

st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">GOTHAM // THREAT COMMAND</div>
        <div class="hero-title">Global Intelligence Surface</div>
        <div class="hero-sub">
            A live investigation workspace for correlated identity, endpoint, network, cloud, and OSINT detections.
            Built to feel like a real internal threat operations system with prioritised triage, geospatial context,
            actor enrichment, telemetry, relationship analysis, and executive-facing reasoning.
        </div>
        <div class="chip-row">
            <div class="chip">Incidents <b>{len(DISPLAY_DF)}</b></div>
            <div class="chip">Critical <b>{critical_count}</b></div>
            <div class="chip">High <b>{high_count}</b></div>
            <div class="chip">Ops State <b>Nominal</b></div>
            <div class="chip">Last Sync <b>{now_utc}</b></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Open incidents", len(DISPLAY_DF))
with m2:
    crit = DISPLAY_DF[DISPLAY_DF["severity"] == "Critical"]["risk_score"]
    st.metric("Critical risk avg", int(crit.mean()) if not crit.empty else 0)
with m3:
    st.metric("Correlated events", f"{int(DISPLAY_DF['events'].sum()):,}")
with m4:
    st.metric("Mean confidence", f"{int(DISPLAY_DF['confidence'].mean())}%")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# =========================================================
# MAIN LAYOUT
# =========================================================
left, right = st.columns([1.12, 1], gap="large")

with left:
    st.markdown('<div class="section-kicker">Signal ingestion</div><div class="section-title">Live alert rail</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel panel-tight">', unsafe_allow_html=True)

    a1, a2 = st.columns([1, 1])
    with a1:
        if st.button("Inject alert", key="inject_alert"):
            st.session_state.live_alerts.insert(0, generate_live_alert())
            st.rerun()
    with a2:
        if st.button("Clear feed", key="clear_alerts"):
            st.session_state.live_alerts = []
            st.rerun()

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    feed = st.session_state.live_alerts[:8]
    if not feed:
        st.markdown('<div class="small-note">No recent live alerts. Inject one to simulate new signal ingestion.</div>', unsafe_allow_html=True)
    else:
        for alert in feed:
            st.markdown(
                f"""
                <div class="queue-row" style="margin-bottom:8px;">
                    <div class="queue-left">
                        <div class="queue-title">{alert['alert']}</div>
                        <div class="queue-sub">{alert['time']} · {alert['region']}</div>
                    </div>
                    <div>{severity_badge(alert['severity'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">Analyst workflow</div><div class="section-title">Auto-prioritised triage queue</div>', unsafe_allow_html=True)
    for _, row in DISPLAY_DF.iterrows():
        cols = st.columns([7, 2, 2])
        with cols[0]:
            st.markdown(
                f"""
                <div class="queue-row">
                    <div class="queue-left">
                        <div class="queue-title">{row['incident_id']} · {row['title']}</div>
                        <div class="queue-sub">{row['region']} · {row['entities']} · {row['source']} · Confidence {row['confidence']}%</div>
                    </div>
                    <div>{severity_badge(row['severity'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with cols[1]:
            st.metric("Risk", row["risk_score"])
        with cols[2]:
            if st.button("Open", key=f"open_{row['incident_id']}"):
                st.session_state.selected_incident_id = row["incident_id"]
                st.rerun()

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">Spatial context</div><div class="section-title">Live threat map</div>', unsafe_allow_html=True)
    map_focus = st.selectbox(
        "Map focus",
        options=DISPLAY_DF["incident_id"].tolist(),
        index=DISPLAY_DF.index[DISPLAY_DF["incident_id"] == st.session_state.selected_incident_id][0],
        key="map_focus_select",
    )
    if map_focus != st.session_state.selected_incident_id:
        st.session_state.selected_incident_id = map_focus
        st.rerun()

    map_fig = build_map_figure(DISPLAY_DF, st.session_state.selected_incident_id)
    st.plotly_chart(map_fig, use_container_width=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">TTP landscape</div><div class="section-title">MITRE activity heat table</div>', unsafe_allow_html=True)
    mitre_fig = build_mitre_heatmap(DISPLAY_DF)
    st.plotly_chart(mitre_fig, use_container_width=True)


with right:
    tabs = st.tabs(["Overview", "Timeline", "Logs", "Actor", "Graph", "Actions"])

    with tabs[0]:
        actor = ACTOR_LIBRARY[SELECTED["title"]]
        st.markdown('<div class="section-kicker">Case file</div><div class="section-title">Incident overview</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="panel">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;">
                    <div>
                        <div style="font-size:1.25rem;font-weight:800;">{SELECTED['incident_id']} · {SELECTED['title']}</div>
                        <div class="small-note" style="margin-top:4px;">{SELECTED['region']} · {SELECTED['entities']} · {SELECTED['source']}</div>
                    </div>
                    <div>{severity_badge(SELECTED['severity'])}</div>
                </div>
                <div style="height:12px"></div>
                <div class="info-grid">
                    <div class="info-tile"><div class="info-label">Status</div><div class="info-value">{SELECTED['status']}</div></div>
                    <div class="info-tile"><div class="info-label">Risk score</div><div class="info-value">{SELECTED['risk_score']}</div></div>
                    <div class="info-tile"><div class="info-label">Confidence</div><div class="info-value">{SELECTED['confidence']}%</div></div>
                    <div class="info-tile"><div class="info-label">Assigned analyst</div><div class="info-value">{SELECTED['analyst']}</div></div>
                    <div class="info-tile"><div class="info-label">MITRE</div><div class="info-value">{', '.join(SELECTED['mitre'])}</div></div>
                    <div class="info-tile"><div class="info-label">Threat actor</div><div class="info-value">{actor['actor']}</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        summary = (
            f"{SELECTED['incident_id']} is a {SELECTED['severity'].lower()}-severity {SELECTED['title'].lower()} case affecting "
            f"{SELECTED['entities']} in {SELECTED['region']}. Telemetry from {SELECTED['source']} has been correlated with "
            f"{SELECTED['events']:,} events and mapped to {', '.join(SELECTED['mitre'])}. Current assessment links activity to "
            f"the {actor['actor']} profile. Recommended next step: maintain containment pressure, validate identity and endpoint exposure, "
            f"and prepare stakeholder comms if business impact widens."
        )
        st.markdown('<div class="section-kicker">Leadership brief</div><div class="section-title">Executive summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="panel" style="line-height:1.7;">{summary}</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        ai_text = generate_ai_assessment(SELECTED)
        st.markdown('<div class="section-kicker">Analyst reasoning</div><div class="section-title">AI assessment</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="panel" style="line-height:1.75;">{ai_text}</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="section-kicker">Reasoning path</div><div class="section-title">Incident timeline</div>', unsafe_allow_html=True)
        timeline = generate_timeline(SELECTED)
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        for item in timeline:
            st.markdown(
                f"""
                <div class="timeline-item">
                    <div class="timeline-time">{item['time']}</div>
                    <div class="timeline-text">{item['event']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="section-kicker">Telemetry</div><div class="section-title">SOC log stream</div>', unsafe_allow_html=True)
        logs = generate_logs(SELECTED)
        log_html = '<div class="panel"><div class="log-shell">' + "".join(logs) + "</div></div>"
        st.markdown(log_html, unsafe_allow_html=True)

    with tabs[3]:
        actor = ACTOR_LIBRARY[SELECTED["title"]]
        tactics = ", ".join(actor["tactics"])
        iocs = "<br>".join(actor["ioc"])
        st.markdown('<div class="section-kicker">Enrichment</div><div class="section-title">Threat actor profile</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="actor-card">
                <div style="font-size:1.1rem;font-weight:800;">{actor['actor']}</div>
                <div class="small-note" style="margin-top:3px;margin-bottom:12px;">Auto-generated profile based on incident type, related TTPs, and linked infrastructure patterns.</div>
                <div style="font-size:0.95rem;line-height:1.65;color:var(--text);margin-bottom:12px;">{actor['profile']}</div>
                <div class="info-tile" style="margin-bottom:10px;">
                    <div class="info-label">Likely tactics</div>
                    <div class="info-value" style="font-size:0.90rem;line-height:1.45;">{tactics}</div>
                </div>
                <div class="info-tile">
                    <div class="info-label">Associated IOCs</div>
                    <div class="info-value" style="font-size:0.88rem;line-height:1.55;font-weight:600;">{iocs}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tabs[4]:
        st.markdown('<div class="section-kicker">Relational analysis</div><div class="section-title">Threat relationship graph</div>', unsafe_allow_html=True)
        graph_fig = build_graph_figure(DISPLAY_DF)
        st.plotly_chart(graph_fig, use_container_width=True)
        st.markdown(
            '<div class="small-note">Graph logic links incidents to actor profiles and related IOCs to simulate the relationship-analysis feel of serious intelligence tooling.</div>',
            unsafe_allow_html=True,
        )

    with tabs[5]:
        st.markdown('<div class="section-kicker">Response</div><div class="section-title">Operator actions</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Escalate incident", key="escalate_incident"):
                st.session_state.operator_log.insert(
                    0,
                    f"{datetime.now(timezone.utc).strftime('%H:%M UTC')} · Escalated {SELECTED['incident_id']} to L2 / IR"
                )
        with c2:
            if st.button("Recommend containment", key="recommend_containment"):
                st.session_state.operator_log.insert(
                    0,
                    f"{datetime.now(timezone.utc).strftime('%H:%M UTC')} · Recommended containment for {SELECTED['incident_id']}"
                )
        with c3:
            if st.button("Generate exec summary", key="gen_exec_summary"):
                st.session_state.operator_log.insert(
                    0,
                    f"{datetime.now(timezone.utc).strftime('%H:%M UTC')} · Generated leadership summary for {SELECTED['incident_id']}"
                )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        if st.session_state.operator_log:
            for item in st.session_state.operator_log[:8]:
                st.markdown(f"- {item}")
        else:
            st.markdown('<div class="small-note">No operator actions taken yet.</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# FOOTER
# =========================================================
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
st.markdown(
    '<div class="small-note">Gotham-inspired portfolio demo: live alert rail, risk-based prioritisation, cinematic geospatial view, MITRE enrichment, actor profiling, relationship graph, operator actions, and a premium analyst-first interface.</div>',
    unsafe_allow_html=True,
)

if random.random() < 0.18:
    st.toast("⚡ New threat signal correlated", icon="🚨")
