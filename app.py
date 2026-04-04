import math
import random
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Threat Operations Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# STYLING
# =========================================================
CUSTOM_CSS = """
<style>
:root {
    --bg: #0a0d12;
    --panel: rgba(17, 23, 31, 0.82);
    --panel-2: rgba(23, 30, 40, 0.90);
    --border: rgba(255,255,255,0.08);
    --text: #e8edf3;
    --muted: #93a1b3;
    --accent: #8db7ff;
    --accent-2: #5f8fff;
    --danger: #ff6b6b;
    --warn: #ffbf69;
    --ok: #5dd39e;
    --critical: #ff4d6d;
    --shadow: 0 20px 60px rgba(0,0,0,0.35);
    --radius-xl: 22px;
    --radius-lg: 18px;
    --radius-md: 14px;
}

html, body, .stApp {
    background:
        radial-gradient(circle at top left, rgba(95,143,255,0.12), transparent 28%),
        radial-gradient(circle at top right, rgba(141,183,255,0.10), transparent 22%),
        linear-gradient(180deg, #07090d 0%, #0a0d12 100%);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1600px;
}

#MainMenu, header, footer {visibility: hidden;}

div[data-testid="stMetric"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.015));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 12px 16px;
    box-shadow: var(--shadow);
    transition: all 180ms ease;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: rgba(141,183,255,0.25);
}

div[data-testid="stMetricLabel"] {
    color: var(--muted);
}

div[data-testid="stMetricValue"] {
    color: var(--text);
}

.panel {
    background: var(--panel);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 18px 18px 16px 18px;
    box-shadow: var(--shadow);
    transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.panel:hover {
    transform: translateY(-2px);
    border-color: rgba(141,183,255,0.22);
}

.hero {
    background:
        linear-gradient(135deg, rgba(95,143,255,0.18), rgba(255,255,255,0.02)),
        rgba(15, 20, 28, 0.86);
    border: 1px solid rgba(141,183,255,0.18);
    border-radius: 26px;
    padding: 22px 24px;
    box-shadow: var(--shadow);
    overflow: hidden;
    position: relative;
}

.hero:before {
    content: "";
    position: absolute;
    inset: -20% auto auto -10%;
    width: 360px;
    height: 360px;
    background: radial-gradient(circle, rgba(141,183,255,0.16), transparent 68%);
    pointer-events: none;
}

.eyebrow {
    color: var(--accent);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}

.hero-title {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.05;
    margin-bottom: 0.45rem;
}

.hero-sub {
    color: var(--muted);
    font-size: 0.98rem;
    max-width: 980px;
}

.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
}

.chip {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    color: var(--text);
    padding: 7px 10px;
    border-radius: 999px;
    font-size: 0.83rem;
    transition: all 160ms ease;
}

.chip:hover {
    border-color: rgba(141,183,255,0.25);
    transform: translateY(-1px);
}

.section-title {
    font-size: 1.02rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    color: var(--text);
}

.section-kicker {
    color: var(--muted);
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 0.45rem;
}

.queue-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 12px 14px;
    margin-bottom: 10px;
    transition: all 180ms ease;
}

.queue-row:hover {
    transform: translateX(3px);
    border-color: rgba(141,183,255,0.22);
    background: rgba(141,183,255,0.045);
}

.queue-left {
    min-width: 0;
}

.queue-title {
    font-weight: 700;
    margin-bottom: 3px;
}

.queue-sub {
    color: var(--muted);
    font-size: 0.88rem;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 0.79rem;
    font-weight: 700;
    border: 1px solid transparent;
}

.badge-critical {
    background: rgba(255,77,109,0.12);
    color: #ff92a8;
    border-color: rgba(255,77,109,0.22);
}

.badge-high {
    background: rgba(255,150,84,0.12);
    color: #ffb27c;
    border-color: rgba(255,150,84,0.22);
}

.badge-medium {
    background: rgba(255,191,105,0.12);
    color: #ffd08b;
    border-color: rgba(255,191,105,0.22);
}

.badge-low {
    background: rgba(93,211,158,0.12);
    color: #86e1b7;
    border-color: rgba(93,211,158,0.22);
}

.log-shell {
    background: #06080b;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 14px;
    max-height: 380px;
    overflow-y: auto;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
}

.log-line {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.83rem;
    line-height: 1.55;
    color: #c8d3df;
    white-space: pre-wrap;
    border-bottom: 1px dashed rgba(255,255,255,0.04);
    padding: 5px 0;
}

.log-time { color: #8db7ff; }
.log-tag { color: #ffbf69; }
.log-ok { color: #5dd39e; }
.log-bad { color: #ff6b6b; }
.log-mid { color: #c5a3ff; }

.actor-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.015));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 16px;
    min-height: 220px;
}

.info-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}

.info-tile {
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 10px 12px;
    background: rgba(255,255,255,0.025);
}

.info-label {
    color: var(--muted);
    font-size: 0.78rem;
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
    margin-bottom: 12px;
}

.timeline-item:before {
    content: "";
    position: absolute;
    left: 0;
    top: 8px;
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--accent);
    box-shadow: 0 0 16px rgba(141,183,255,0.6);
}

.timeline-time {
    color: var(--muted);
    font-size: 0.8rem;
    margin-bottom: 2px;
}

.timeline-text {
    color: var(--text);
    font-size: 0.92rem;
}

.stButton > button {
    width: 100%;
    border: 1px solid rgba(255,255,255,0.10);
    background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
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

.stButton > button:focus {
    box-shadow: 0 0 0 0.16rem rgba(141,183,255,0.20) !important;
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

.small-note {
    color: var(--muted);
    font-size: 0.82rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =========================================================
# DATA MODEL
# =========================================================
SEVERITY_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
SEVERITY_COLOR = {
    "Critical": [255, 77, 109, 215],
    "High": [255, 150, 84, 210],
    "Medium": [255, 191, 105, 200],
    "Low": [93, 211, 158, 190],
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


def seed_everything(seed: int = 11) -> None:
    random.seed(seed)
    np.random.seed(seed)


seed_everything()


def generate_incidents() -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    records = [
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

    df = pd.DataFrame(records)
    df["opened_at"] = df["opened_minutes_ago"].apply(lambda x: now - timedelta(minutes=int(x)))
    df["sev_rank"] = df["severity"].map(SEVERITY_ORDER)
    df["mitre"] = df["title"].map(MITRE_TECHNIQUES)
    df["map_radius"] = df["risk_score"].apply(lambda x: 22000 + x * 600)
    df["color"] = df["severity"].map(SEVERITY_COLOR)
    df = df.sort_values(["sev_rank", "risk_score", "opened_at"], ascending=[False, False, False]).reset_index(drop=True)
    return df


INCIDENTS = generate_incidents()


def generate_timeline(incident: pd.Series) -> list[dict]:
    base = incident["opened_at"]
    title = incident["title"]
    return [
        {"time": base.strftime("%H:%M UTC"), "event": f"Detection triggered for {title} via {incident['source']} telemetry."},
        {"time": (base + timedelta(minutes=4)).strftime("%H:%M UTC"), "event": f"Correlation engine linked activity to {incident['events']:,} raw events across {incident['entities']}."},
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
    lines = []
    for i in range(count):
        ts = (base + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S")
        src = random.choice(sources).upper()
        host = random.choice(hosts)
        action = random.choice(actions)
        mark = random.choice(["ALLOW", "REVIEW", "BLOCK", "ENRICH"])
        cls = "log-ok" if mark == "ALLOW" else "log-bad" if mark == "BLOCK" else "log-mid" if mark == "ENRICH" else "log-tag"
        lines.append(
            f'<div class="log-line"><span class="log-time">{ts}</span>  <span class="log-tag">[{src}]</span>  host={host}  event="{action}"  incident={incident["incident_id"]}  verdict=<span class="{cls}">{mark}</span></div>'
        )
    return lines



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
    mitre_df = pd.DataFrame(rows).set_index("Severity")
    return mitre_df


MITRE_MATRIX = build_mitre_matrix(INCIDENTS)

# =========================================================
# STATE
# =========================================================
if "selected_incident_id" not in st.session_state:
    st.session_state.selected_incident_id = INCIDENTS.iloc[0]["incident_id"]

if "escalation_log" not in st.session_state:
    st.session_state.escalation_log = []

# =========================================================
# HELPERS
# =========================================================
def severity_badge(severity: str) -> str:
    cls = {
        "Critical": "badge badge-critical",
        "High": "badge badge-high",
        "Medium": "badge badge-medium",
        "Low": "badge badge-low",
    }[severity]
    return f'<span class="{cls}">{severity}</span>'



def select_incident(incident_id: str) -> None:
    st.session_state.selected_incident_id = incident_id



def get_selected_incident(df: pd.DataFrame) -> pd.Series:
    row = df[df["incident_id"] == st.session_state.selected_incident_id]
    if row.empty:
        return df.iloc[0]
    return row.iloc[0]



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



def render_hero(df: pd.DataFrame) -> None:
    now_utc = datetime.now(timezone.utc).strftime("%d %b %Y • %H:%M UTC")
    critical_count = int((df["severity"] == "Critical").sum())
    high_count = int((df["severity"] == "High").sum())
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">Threat Operations Platform</div>
            <div class="hero-title">Global incident awareness with analyst-grade drill-down</div>
            <div class="hero-sub">
                Correlated signals from identity, endpoint, cloud, network, and OSINT sources. Built to feel like a real
                internal investigation product: triage queue, map-driven context, MITRE enrichment, timeline reasoning,
                and escalation actions.
            </div>
            <div class="chip-row">
                <div class="chip">Active incidents: <b>{len(df)}</b></div>
                <div class="chip">Critical: <b>{critical_count}</b></div>
                <div class="chip">High: <b>{high_count}</b></div>
                <div class="chip">SLA state: <b>Operational</b></div>
                <div class="chip">Last sync: <b>{now_utc}</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_queue(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-kicker">Analyst workflow</div><div class="section-title">Auto-prioritised triage queue</div>', unsafe_allow_html=True)
    for _, row in df.iterrows():
        left = st.container()
        cols = left.columns([7, 2, 2])
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
            if st.button("Open incident", key=f"open_{row['incident_id']}"):
                select_incident(row["incident_id"])
                st.rerun()



def render_map(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-kicker">Spatial context</div><div class="section-title">Global incident map</div>', unsafe_allow_html=True)
    st.caption("Use the queue or map-linked selector below to open a case. Streamlit maps are not deeply click-native, so the app uses a synced incident selector for reliable drill-down.")

    map_df = df.copy()
    map_df["tooltip"] = map_df.apply(
        lambda r: f"{r['incident_id']}\n{r['title']}\n{r['region']}\nSeverity: {r['severity']}\nRisk: {r['risk_score']}", axis=1
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[lon, lat]",
        get_radius="map_radius",
        get_fill_color="color",
        pickable=True,
        stroked=True,
        get_line_color=[255, 255, 255, 120],
        line_width_min_pixels=1,
    )

    text_layer = pdk.Layer(
        "TextLayer",
        data=map_df,
        get_position="[lon, lat]",
        get_text="incident_id",
        get_size=14,
        get_color=[232, 237, 243, 180],
        get_alignment_baseline="bottom",
        get_pixel_offset=[0, -18],
    )

    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v11",
        initial_view_state=pdk.ViewState(latitude=22, longitude=8, zoom=1.2, pitch=18),
        layers=[layer, text_layer],
        tooltip={"text": "{tooltip}"},
    )
    st.pydeck_chart(deck, use_container_width=True)

    selected_from_map = st.selectbox(
        "Open incident from map context",
        options=df["incident_id"].tolist(),
        index=max(0, df.index[df["incident_id"] == st.session_state.selected_incident_id][0]) if st.session_state.selected_incident_id in df["incident_id"].values else 0,
        key="map_selector",
    )
    if selected_from_map != st.session_state.selected_incident_id:
        select_incident(selected_from_map)
        st.rerun()



def render_incident_overview(incident: pd.Series) -> None:
    actor = ACTOR_LIBRARY[incident["title"]]
    st.markdown('<div class="section-kicker">Case file</div><div class="section-title">Incident overview</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="panel">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;">
                <div>
                    <div style="font-size:1.25rem;font-weight:800;">{incident['incident_id']} · {incident['title']}</div>
                    <div class="small-note" style="margin-top:4px;">{incident['region']} · {incident['entities']} · {incident['source']}</div>
                </div>
                <div>{severity_badge(incident['severity'])}</div>
            </div>
            <div style="height:12px"></div>
            <div class="info-grid">
                <div class="info-tile"><div class="info-label">Status</div><div class="info-value">{incident['status']}</div></div>
                <div class="info-tile"><div class="info-label">Risk score</div><div class="info-value">{incident['risk_score']}</div></div>
                <div class="info-tile"><div class="info-label">Confidence</div><div class="info-value">{incident['confidence']}%</div></div>
                <div class="info-tile"><div class="info-label">Assigned analyst</div><div class="info-value">{incident['analyst']}</div></div>
                <div class="info-tile"><div class="info-label">MITRE</div><div class="info-value">{', '.join(incident['mitre'])}</div></div>
                <div class="info-tile"><div class="info-label">Threat actor</div><div class="info-value">{actor['actor']}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_timeline(incident: pd.Series) -> None:
    st.markdown('<div class="section-kicker">Reasoning path</div><div class="section-title">Incident timeline</div>', unsafe_allow_html=True)
    timeline = generate_timeline(incident)
    with st.container():
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
        st.markdown('</div>', unsafe_allow_html=True)



def render_logs(incident: pd.Series) -> None:
    st.markdown('<div class="section-kicker">Telemetry</div><div class="section-title">SOC log stream</div>', unsafe_allow_html=True)
    logs = generate_logs(incident)
    log_html = '<div class="panel"><div class="log-shell">' + ''.join(logs) + '</div></div>'
    st.markdown(log_html, unsafe_allow_html=True)



def render_actor_card(incident: pd.Series) -> None:
    actor = ACTOR_LIBRARY[incident["title"]]
    st.markdown('<div class="section-kicker">Enrichment</div><div class="section-title">Threat actor profile</div>', unsafe_allow_html=True)
    iocs = "<br>".join(actor["ioc"])
    tactics = ", ".join(actor["tactics"])
    st.markdown(
        f"""
        <div class="actor-card">
            <div style="font-size:1.1rem;font-weight:800;">{actor['actor']}</div>
            <div class="small-note" style="margin-top:3px;margin-bottom:12px;">Auto-generated profile based on incident type, related TTPs, and linked infrastructure patterns.</div>
            <div style="font-size:0.95rem;line-height:1.6;color:var(--text);margin-bottom:12px;">{actor['profile']}</div>
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



def render_actions(incident: pd.Series) -> None:
    st.markdown('<div class="section-kicker">Response</div><div class="section-title">Operator actions</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Escalate incident", key=f"esc_{incident['incident_id']}"):
                entry = f"{datetime.now(timezone.utc).strftime('%H:%M UTC')} · Escalated {incident['incident_id']} to L2 / IR"
                st.session_state.escalation_log.insert(0, entry)
        with c2:
            if st.button("Recommend containment", key=f"cont_{incident['incident_id']}"):
                entry = f"{datetime.now(timezone.utc).strftime('%H:%M UTC')} · Recommended containment for {incident['incident_id']}"
                st.session_state.escalation_log.insert(0, entry)
        with c3:
            if st.button("Generate exec summary", key=f"sum_{incident['incident_id']}"):
                entry = f"{datetime.now(timezone.utc).strftime('%H:%M UTC')} · Generated leadership summary for {incident['incident_id']}"
                st.session_state.escalation_log.insert(0, entry)

        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        if st.session_state.escalation_log:
            for item in st.session_state.escalation_log[:6]:
                st.markdown(f"- {item}")
        else:
            st.markdown('<div class="small-note">No operator actions taken yet.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)



def render_exec_summary(incident: pd.Series) -> None:
    st.markdown('<div class="section-kicker">Leadership brief</div><div class="section-title">Executive summary</div>', unsafe_allow_html=True)
    actor = ACTOR_LIBRARY[incident["title"]]
    summary = (
        f"{incident['incident_id']} is a {incident['severity'].lower()}-severity {incident['title'].lower()} case affecting "
        f"{incident['entities']} in {incident['region']}. Telemetry from {incident['source']} has been correlated with "
        f"{incident['events']:,} events and mapped to {', '.join(incident['mitre'])}. Current assessment links activity to "
        f"the {actor['actor']} profile. Recommended next step: maintain containment pressure, validate identity and endpoint exposure, "
        f"and prepare stakeholder comms if business impact widens."
    )
    st.markdown(f'<div class="panel" style="line-height:1.7;">{summary}</div>', unsafe_allow_html=True)


# =========================================================
# SIDEBAR FILTERS
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
    search_text = st.text_input("Search incidents", placeholder="INC-24051, London, OAuth...")

DF = filtered_incidents(INCIDENTS, severity_filter, source_filter, search_text)
selected = get_selected_incident(DF if not DF.empty else INCIDENTS)

# =========================================================
# HEADER + METRICS
# =========================================================
render_hero(DF if not DF.empty else INCIDENTS)
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Open incidents", len(DF))
with m2:
    st.metric("Critical risk avg", int(DF[DF["severity"] == "Critical"]["risk_score"].mean()) if not DF[DF["severity"] == "Critical"].empty else 0)
with m3:
    st.metric("Correlated events", f"{int(DF['events'].sum()):,}")
with m4:
    st.metric("Mean confidence", f"{int(DF['confidence'].mean())}%" if not DF.empty else "0%")

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# =========================================================
# MAIN LAYOUT
# =========================================================
left, right = st.columns([1.08, 1], gap="large")

with left:
    render_queue(DF if not DF.empty else INCIDENTS)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    render_map(DF if not DF.empty else INCIDENTS)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">TTP landscape</div><div class="section-title">MITRE activity heat table</div>', unsafe_allow_html=True)
    st.dataframe(MITRE_MATRIX, use_container_width=True)

with right:
    tabs = st.tabs(["Overview", "Timeline", "Logs", "Actor", "Actions"])
    with tabs[0]:
        render_incident_overview(selected)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        render_exec_summary(selected)
    with tabs[1]:
        render_timeline(selected)
    with tabs[2]:
        render_logs(selected)
    with tabs[3]:
        render_actor_card(selected)
    with tabs[4]:
        render_actions(selected)

# =========================================================
# FOOTER NOTE
# =========================================================
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
st.markdown(
    '<div class="small-note">Production-grade portfolio demo notes: stateful incident drill-down, risk-based prioritisation, spatial context, MITRE enrichment, operator actions, and consistent premium UI styling suitable for a serious security product demo.</div>',
    unsafe_allow_html=True,
)
