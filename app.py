import os
import re
import math
from datetime import datetime, timedelta, timezone
from collections import Counter
from typing import Dict, List, Tuple

import pandas as pd
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Global OSINT Threat Monitoring Dashboard",
    page_icon="🌐",
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
            --bg: #0b0d12;
            --panel: rgba(255,255,255,0.05);
            --panel-2: rgba(255,255,255,0.03);
            --border: rgba(255,255,255,0.08);
            --text: #f5f7fb;
            --muted: #a8b0c0;
            --accent: #d7e3ff;
            --danger: #ff6b6b;
            --warn: #ffcc66;
            --ok: #74d99f;
            --info: #88b4ff;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(95, 122, 255, 0.12), transparent 28%),
                radial-gradient(circle at top right, rgba(0, 221, 168, 0.08), transparent 24%),
                linear-gradient(180deg, #07090d 0%, #0b0d12 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }

        h1, h2, h3, h4, h5, h6, p, div, span, label {
            color: var(--text) !important;
        }

        .hero {
            padding: 1.4rem 1.6rem;
            border: 1px solid var(--border);
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
            box-shadow: 0 14px 40px rgba(0,0,0,0.35);
            backdrop-filter: blur(12px);
            margin-bottom: 1rem;
        }

        .hero-title {
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin-bottom: 0.35rem;
        }

        .hero-subtitle {
            color: var(--muted) !important;
            font-size: 0.98rem;
            line-height: 1.5;
        }

        .glass-card {
            border: 1px solid var(--border);
            background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.025));
            border-radius: 22px;
            padding: 1rem 1rem 0.9rem 1rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
            backdrop-filter: blur(12px);
            height: 100%;
        }

        .kpi-card {
            border: 1px solid var(--border);
            background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
            border-radius: 22px;
            padding: 1rem 1rem 0.9rem 1rem;
            min-height: 120px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        }

        .kpi-label {
            font-size: 0.82rem;
            color: var(--muted) !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.4rem;
        }

        .kpi-value {
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.03em;
        }

        .kpi-footnote {
            color: var(--muted) !important;
            font-size: 0.88rem;
            margin-top: 0.35rem;
        }

        .pill {
            display: inline-block;
            padding: 0.3rem 0.55rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.06);
        }

        .sev-high { background: rgba(255, 107, 107, 0.14); color: #ffb3b3 !important; }
        .sev-medium { background: rgba(255, 204, 102, 0.14); color: #ffd98a !important; }
        .sev-low { background: rgba(116, 217, 159, 0.14); color: #9ff0bb !important; }

        .brief-box {
            border: 1px solid var(--border);
            background: rgba(255,255,255,0.035);
            border-radius: 20px;
            padding: 1.1rem;
            margin-top: 0.75rem;
            line-height: 1.6;
        }

        .article-card {
            border: 1px solid var(--border);
            background: rgba(255,255,255,0.03);
            border-radius: 18px;
            padding: 1rem;
            margin-bottom: 0.8rem;
        }

        .muted {
            color: var(--muted) !important;
        }

        .stTextInput > div > div,
        .stMultiSelect > div > div,
        .stSelectbox > div > div,
        .stTextArea textarea,
        .stDateInput > div > div,
        .stNumberInput > div > div {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: 14px !important;
            color: var(--text) !important;
        }

        .stButton > button {
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.08);
            background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04));
            color: white;
            padding: 0.65rem 1rem;
            font-weight: 600;
        }

        .stDownloadButton > button {
            border-radius: 14px;
        }

        .sidebar-panel {
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 1rem;
            background: rgba(255,255,255,0.03);
        }

        hr {
            border-color: rgba(255,255,255,0.08);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CONSTANTS
# =========================================================
NEWSAPI_URL = "https://newsapi.org/v2/everything"
DEFAULT_QUERY = (
    '("cyber attack" OR ransomware OR phishing OR malware OR protest OR unrest '
    'OR conflict OR "critical infrastructure" OR sanctions OR terrorism OR espionage '
    'OR "data breach" OR "state of emergency")'
)

SEVERITY_WEIGHTS = {
    "ransomware": 5,
    "terror": 5,
    "terrorism": 5,
    "explosion": 5,
    "attack": 4,
    "breach": 4,
    "data breach": 4,
    "sabotage": 4,
    "espionage": 4,
    "drone": 4,
    "missile": 5,
    "war": 5,
    "conflict": 4,
    "protest": 3,
    "unrest": 3,
    "riot": 4,
    "disruption": 3,
    "outage": 3,
    "critical infrastructure": 4,
    "phishing": 3,
    "malware": 3,
    "fraud": 2,
    "sanctions": 3,
    "kidnap": 5,
    "evacuation": 4,
    "emergency": 3,
    "shooting": 5,
    "bomb": 5,
}

CATEGORY_KEYWORDS = {
    "Cyber": ["cyber", "ransomware", "malware", "phishing", "breach", "hacker", "ddos", "infostealer"],
    "Civil Unrest": ["protest", "unrest", "riot", "demonstration", "strike", "clashes"],
    "Geopolitical": ["war", "conflict", "sanctions", "missile", "military", "border", "espionage"],
    "Infrastructure": ["power", "grid", "airport", "rail", "port", "telecom", "outage", "critical infrastructure"],
    "Public Safety": ["shooting", "explosion", "terror", "terrorism", "evacuation", "bomb", "kidnap"],
}

SECTOR_KEYWORDS = {
    "Finance": ["bank", "financial", "payments", "stock exchange", "insurance"],
    "Transport": ["airport", "rail", "metro", "transport", "airline", "shipping", "port"],
    "Government": ["government", "ministry", "parliament", "police", "embassy"],
    "Media": ["media", "broadcaster", "journalist", "newsroom", "studio"],
    "Technology": ["tech", "cloud", "software", "platform", "data center"],
    "Energy": ["power", "oil", "gas", "grid", "utility", "pipeline"],
    "Healthcare": ["hospital", "clinic", "healthcare", "pharma"],
}

LOCATION_COORDS = {
    "Paris": (48.8566, 2.3522),
    "London": (51.5072, -0.1276),
    "New York": (40.7128, -74.0060),
    "Washington": (38.9072, -77.0369),
    "Los Angeles": (34.0522, -118.2437),
    "Rome": (41.9028, 12.4964),
    "Milan": (45.4642, 9.19),
    "Berlin": (52.52, 13.405),
    "Brussels": (50.8503, 4.3517),
    "Moscow": (55.7558, 37.6173),
    "Kyiv": (50.4501, 30.5234),
    "Tel Aviv": (32.0853, 34.7818),
    "Jerusalem": (31.7683, 35.2137),
    "Tehran": (35.6892, 51.3890),
    "Dubai": (25.2048, 55.2708),
    "Beijing": (39.9042, 116.4074),
    "Shanghai": (31.2304, 121.4737),
    "Tokyo": (35.6762, 139.6503),
    "Seoul": (37.5665, 126.9780),
    "Taipei": (25.0330, 121.5654),
    "Sydney": (-33.8688, 151.2093),
    "Melbourne": (-37.8136, 144.9631),
    "Canberra": (-35.2809, 149.13),
    "Singapore": (1.3521, 103.8198),
    "Hong Kong": (22.3193, 114.1694),
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Istanbul": (41.0082, 28.9784),
    "Athens": (37.9838, 23.7275),
    "Cairo": (30.0444, 31.2357),
    "Johannesburg": (-26.2041, 28.0473),
    "Nairobi": (-1.2921, 36.8219),
    "Lagos": (6.5244, 3.3792),
    "Mexico City": (19.4326, -99.1332),
    "Sao Paulo": (-23.5558, -46.6396),
    "Buenos Aires": (-34.6037, -58.3816),
}

STOPWORDS = {
    "The", "A", "An", "This", "That", "These", "Those", "It", "Its", "His", "Her", "Their", "They",
    "He", "She", "We", "I", "In", "On", "At", "By", "For", "From", "With", "About", "After", "Before",
    "Over", "Under", "Into", "Across", "Against", "As", "To", "Of", "And", "Or", "But", "News", "Update",
}


# =========================================================
# HELPERS
# =========================================================
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(dt_str: str) -> datetime:
    if not dt_str:
        return utc_now()
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return utc_now()


def safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def clean_text(text: str) -> str:
    text = safe_text(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_url(url: str) -> str:
    url = safe_text(url)
    return re.sub(r"\?.*$", "", url).strip().lower()


def dedupe_articles(articles: List[Dict]) -> List[Dict]:
    seen = set()
    deduped = []
    for article in articles:
        key = (
            clean_text(article.get("title", "")).lower(),
            normalize_url(article.get("url", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(article)
    return deduped


def count_keyword_hits(text: str, keywords: List[str]) -> int:
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw.lower() in text_lower)


def classify_category(text: str) -> str:
    scores = {cat: count_keyword_hits(text, kws) for cat, kws in CATEGORY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General Risk"


def detect_sectors(text: str) -> List[str]:
    hits = []
    lower = text.lower()
    for sector, kws in SECTOR_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            hits.append(sector)
    return hits or ["General Business"]


def extract_locations(text: str) -> List[str]:
    found = []
    for location in LOCATION_COORDS.keys():
        if re.search(rf"\b{re.escape(location)}\b", text, flags=re.IGNORECASE):
            found.append(location)
    return found[:4]


def extract_named_entities_headline(text: str) -> List[str]:
    matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b", text)
    entities = []
    for m in matches:
        if m in STOPWORDS:
            continue
        if len(m) < 3:
            continue
        entities.append(m)
    deduped = []
    seen = set()
    for entity in entities:
        if entity not in seen:
            seen.add(entity)
            deduped.append(entity)
    return deduped[:6]


def calculate_severity_score(text: str, source_name: str, published_at: str) -> int:
    lower = text.lower()
    score = 0

    for term, weight in SEVERITY_WEIGHTS.items():
        if term in lower:
            score += weight

    # Recency boost
    age_hours = max((utc_now() - parse_dt(published_at)).total_seconds() / 3600, 0)
    if age_hours <= 12:
        score += 3
    elif age_hours <= 24:
        score += 2
    elif age_hours <= 72:
        score += 1

    # Source credibility boost
    reputable_sources = {"Reuters", "Associated Press", "AP News", "BBC News", "The Guardian", "Financial Times", "Bloomberg"}
    if source_name in reputable_sources:
        score += 1

    return score


def severity_bucket(score: int) -> str:
    if score >= 9:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def severity_css(severity: str) -> str:
    return {
        "High": "sev-high",
        "Medium": "sev-medium",
        "Low": "sev-low",
    }.get(severity, "sev-low")


def summarise_snippet(description: str, content: str) -> str:
    text = clean_text(description or content)
    if not text:
        return "Limited source detail available from the article excerpt."
    text = re.sub(r"\[\+\d+ chars\]$", "", text).strip()
    if len(text) > 240:
        text = text[:237].rsplit(" ", 1)[0] + "..."
    return text


def build_article_record(article: Dict) -> Dict:
    title = clean_text(article.get("title"))
    description = clean_text(article.get("description"))
    content = clean_text(article.get("content"))
    source_name = safe_text(article.get("source", {}).get("name")) or "Unknown"
    published_at = safe_text(article.get("publishedAt"))
    combined = f"{title}. {description}. {content}"

    category = classify_category(combined)
    sectors = detect_sectors(combined)
    locations = extract_locations(combined)
    entities = extract_named_entities_headline(title)
    sev_score = calculate_severity_score(combined, source_name, published_at)
    severity = severity_bucket(sev_score)

    return {
        "title": title or "Untitled article",
        "source": source_name,
        "author": safe_text(article.get("author")),
        "published_at": published_at,
        "published_dt": parse_dt(published_at),
        "description": description,
        "content": content,
        "snippet": summarise_snippet(description, content),
        "url": safe_text(article.get("url")),
        "image_url": safe_text(article.get("urlToImage")),
        "category": category,
        "sectors": sectors,
        "locations": locations,
        "entities": entities,
        "severity_score": sev_score,
        "severity": severity,
    }


def fetch_news(query: str, api_key: str, page_size: int = 50, language: str = "en", days_back: int = 7) -> List[Dict]:
    from_date = (utc_now() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {
        "q": query,
        "language": language,
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "from": from_date,
        "apiKey": api_key,
    }
    response = requests.get(NEWSAPI_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    articles = data.get("articles", [])
    return dedupe_articles(articles)


def fallback_demo_articles() -> List[Dict]:
    now = utc_now().isoformat()
    return [
        {
            "source": {"name": "Reuters"},
            "author": "Reuters Staff",
            "title": "Ransomware incident disrupts regional hospital systems in London",
            "description": "A cyber incident affected scheduling systems and forced temporary service disruptions while recovery work continued.",
            "content": "A ransomware-related cyber incident has disrupted some digital services at a regional healthcare provider in London. Investigations remain ongoing and contingency procedures were activated.",
            "url": "https://example.com/demo-1",
            "urlToImage": "",
            "publishedAt": now,
        },
        {
            "source": {"name": "BBC News"},
            "author": "BBC",
            "title": "Transport disruption spreads after protests intensify in Paris",
            "description": "Civil unrest affected metro access and increased operational pressure on commuter networks and event logistics.",
            "content": "Protests intensified across parts of Paris, with transport disruption, road closures and crowd management challenges reported near central districts.",
            "url": "https://example.com/demo-2",
            "urlToImage": "",
            "publishedAt": now,
        },
        {
            "source": {"name": "AP News"},
            "author": "AP",
            "title": "Government agencies investigate phishing campaign targeting financial institutions",
            "description": "Security teams are tracking a coordinated campaign using spoofed portals and credential harvesting.",
            "content": "Authorities and financial institutions are responding to a phishing campaign targeting customer and employee credentials through spoofed login infrastructure.",
            "url": "https://example.com/demo-3",
            "urlToImage": "",
            "publishedAt": now,
        },
    ]


def to_dataframe(records: List[Dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(
            columns=[
                "title", "source", "published_at", "published_dt", "category", "severity",
                "severity_score", "locations", "sectors", "entities", "snippet", "url"
            ]
        )
    return pd.DataFrame(records)


def top_items(series, n=5) -> List[Tuple[str, int]]:
    counter = Counter(series)
    return counter.most_common(n)


def flatten_column(df: pd.DataFrame, col: str) -> List[str]:
    items = []
    if col not in df.columns:
        return items
    for value in df[col].dropna().tolist():
        if isinstance(value, list):
            items.extend(value)
        else:
            items.append(str(value))
    return items


def make_brief(df: pd.DataFrame) -> Dict[str, str]:
    if df.empty:
        return {
            "headline": "No significant developments identified.",
            "key_developments": "No qualifying articles matched the current filters.",
            "risk_assessment": "Insufficient reporting to support a reliable threat assessment.",
            "analyst_insight": "Broaden the query, increase the date window, or validate API coverage.",
            "recommended_actions": "Refresh collection parameters and verify upstream data ingestion.",
        }

    working = df.sort_values(["severity_score", "published_dt"], ascending=[False, False]).head(8)
    high_count = int((df["severity"] == "High").sum())
    medium_count = int((df["severity"] == "Medium").sum())
    dominant_category = df["category"].mode().iloc[0] if not df["category"].mode().empty else "General Risk"
    dominant_locations = [x for x, _ in top_items(flatten_column(df, "locations"), 3)]
    dominant_sectors = [x for x, _ in top_items(flatten_column(df, "sectors"), 3)]

    key_lines = []
    for _, row in working.head(3).iterrows():
        loc_text = ", ".join(row["locations"][:2]) if row["locations"] else "multiple locations"
        sector_text = ", ".join(row["sectors"][:2]) if row["sectors"] else "cross-sector targets"
        line = (
            f"• {row['title']} ({row['source']}) indicates {row['category'].lower()} activity affecting "
            f"{loc_text}, with likely implications for {sector_text.lower()}."
        )
        key_lines.append(line)

    geographic_text = ", ".join(dominant_locations) if dominant_locations else "multiple geographies"
    sector_text = ", ".join(dominant_sectors) if dominant_sectors else "general business operations"

    if high_count >= 3:
        risk_level = "High"
        risk_text = (
            f"The reporting environment indicates a high operational risk posture. {high_count} high-severity developments "
            f"suggest near-term disruption potential, particularly across {sector_text.lower()} in {geographic_text}."
        )
    elif high_count >= 1 or medium_count >= 4:
        risk_level = "Medium"
        risk_text = (
            f"The environment reflects a moderate but active risk posture. Current reporting suggests escalation potential in "
            f"{dominant_category.lower()} developments, with business continuity and security monitoring implications across {sector_text.lower()}."
        )
    else:
        risk_level = "Low"
        risk_text = (
            f"Current reporting supports a lower immediate threat posture, though continued monitoring is warranted for {dominant_category.lower()} developments "
            f"in {geographic_text}."
        )

    insight = (
        f"The collection set is dominated by {dominant_category.lower()} reporting rather than isolated incidents, which suggests the need for sustained monitoring rather than one-off reaction. "
        f"For corporate security teams, the most relevant question is whether these developments begin to affect personnel mobility, digital access, or partner operations in {geographic_text}."
    )

    actions = []
    if dominant_category == "Cyber":
        actions.extend([
            "Increase monitoring for credential abuse, phishing infrastructure, and unusual authentication activity.",
            "Validate communications to staff on phishing awareness and escalation procedures.",
        ])
    if dominant_category == "Civil Unrest":
        actions.extend([
            "Review personnel movement and event logistics in affected areas.",
            "Monitor protest locations, transit closures, and local police advisories for escalation indicators.",
        ])
    if dominant_category == "Geopolitical":
        actions.extend([
            "Track second-order impacts on travel, sanctions exposure, and regional partner operations.",
            "Review contingency planning for staff and vendors in or near affected jurisdictions.",
        ])
    if dominant_category == "Infrastructure":
        actions.extend([
            "Assess dependencies on affected transport, telecom, or utility networks.",
            "Verify backup communications and business continuity procedures.",
        ])
    if dominant_category == "Public Safety":
        actions.extend([
            "Review physical security posture and situational awareness for staff in affected areas.",
            "Escalate monitoring where incidents could affect public venues, offices, or live operations.",
        ])
    if not actions:
        actions.extend([
            "Continue monitoring for escalation, concentration by geography, and cross-sector spillover.",
            "Share a concise situational update with relevant stakeholders and document trigger thresholds for escalation.",
        ])

    headline = f"{risk_level} risk environment driven by {dominant_category.lower()} reporting"

    return {
        "headline": headline,
        "key_developments": "\n".join(key_lines) if key_lines else "No major developments identified.",
        "risk_assessment": risk_text,
        "analyst_insight": insight,
        "recommended_actions": "\n".join([f"• {a}" for a in actions[:4]]),
    }


def make_timeline_chart(df: pd.DataFrame):
    if df.empty:
        return None
    timeline = df.copy()
    timeline["hour"] = timeline["published_dt"].dt.floor("H")
    agg = timeline.groupby(["hour", "severity"]).size().reset_index(name="count")
    if agg.empty:
        return None
    fig = px.line(
        agg,
        x="hour",
        y="count",
        color="severity",
        markers=True,
        title="Threat Reporting Timeline",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        margin=dict(l=10, r=10, t=40, b=10),
        legend_title_text="Severity",
    )
    return fig


def make_category_chart(df: pd.DataFrame):
    if df.empty:
        return None
    agg = df["category"].value_counts().reset_index()
    agg.columns = ["category", "count"]
    fig = px.bar(
        agg,
        x="category",
        y="count",
        title="Incidents by Category",
        text="count",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title=None,
        yaxis_title=None,
    )
    return fig


def make_geo_chart(df: pd.DataFrame):
    if df.empty:
        return None

    rows = []
    for _, row in df.iterrows():
        locs = row["locations"] if isinstance(row["locations"], list) else []
        for loc in locs:
            if loc in LOCATION_COORDS:
                lat, lon = LOCATION_COORDS[loc]
                rows.append(
                    {
                        "location": loc,
                        "lat": lat,
                        "lon": lon,
                        "severity": row["severity"],
                        "title": row["title"],
                        "category": row["category"],
                    }
                )

    if not rows:
        return None

    geo_df = pd.DataFrame(rows)
    fig = px.scatter_geo(
        geo_df,
        lat="lat",
        lon="lon",
        hover_name="location",
        hover_data={"title": True, "category": True, "lat": False, "lon": False},
        size_max=18,
        title="Geographic Threat Footprint",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        margin=dict(l=10, r=10, t=40, b=10),
        geo=dict(
            bgcolor="rgba(0,0,0,0)",
            showland=True,
            landcolor="rgba(255,255,255,0.05)",
            showocean=True,
            oceancolor="rgba(255,255,255,0.02)",
            countrycolor="rgba(255,255,255,0.08)",
            coastlinecolor="rgba(255,255,255,0.08)",
            projection_type="natural earth",
        ),
    )
    return fig


def export_brief_text(brief: Dict[str, str], df: pd.DataFrame) -> str:
    timestamp = utc_now().strftime("%d %b %Y %H:%M UTC")
    titles = df.sort_values(["severity_score", "published_dt"], ascending=[False, False])["title"].head(5).tolist()
    source_lines = [f"- {t}" for t in titles]
    return f"""GLOBAL OSINT INTELLIGENCE BRIEF
Generated: {timestamp}

Headline
{brief['headline']}

Key Developments
{brief['key_developments']}

Risk Assessment
{brief['risk_assessment']}

Analyst Insight
{brief['analyst_insight']}

Recommended Actions
{brief['recommended_actions']}

Priority Source Headlines
{chr(10).join(source_lines)}
"""


def render_kpi(label: str, value: str, footnote: str):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-footnote">{footnote}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_article_card(row: pd.Series):
    locations = row["locations"] if isinstance(row["locations"], list) else []
    sectors = row["sectors"] if isinstance(row["sectors"], list) else []
    entities = row["entities"] if isinstance(row["entities"], list) else []

    st.markdown('<div class="article-card">', unsafe_allow_html=True)
    cols = st.columns([7, 2])
    with cols[0]:
        st.markdown(f"### {row['title']}")
        st.markdown(
            f"<div class='muted'>{row['source']} · {row['published_dt'].strftime('%d %b %Y %H:%M UTC')} · {row['category']}</div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            f"<div class='pill {severity_css(row['severity'])}'>{row['severity']} · {row['severity_score']}</div>",
            unsafe_allow_html=True,
        )

    st.write(row["snippet"])

    if locations:
        st.markdown("**Locations**")
        st.markdown(" ".join([f"<span class='pill'>{x}</span>" for x in locations]), unsafe_allow_html=True)
    if sectors:
        st.markdown("**Affected Sectors**")
        st.markdown(" ".join([f"<span class='pill'>{x}</span>" for x in sectors]), unsafe_allow_html=True)
    if entities:
        st.markdown("**Named Entities**")
        st.markdown(" ".join([f"<span class='pill'>{x}</span>" for x in entities]), unsafe_allow_html=True)

    if row["url"]:
        st.markdown(f"[Open source article]({row['url']})")
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
    st.markdown("## Collection Controls")

    newsapi_key = st.text_input(
        "NewsAPI key",
        value=os.getenv("NEWSAPI_KEY", ""),
        type="password",
        help="Leave blank to load demo data.",
    )

    query = st.text_area(
        "Collection query",
        value=DEFAULT_QUERY,
        height=120,
        help="Use a focused Boolean-style query for more intelligence-grade reporting.",
    )

    lookback_days = st.slider("Lookback window (days)", 1, 30, 7)
    article_limit = st.slider("Article limit", 10, 100, 40, step=5)
    language = st.selectbox("Language", ["en", "fr", "de", "it", "es"], index=0)

    run = st.button("Run collection", use_container_width=True)
    use_demo = st.button("Load demo data", use_container_width=True)

    st.markdown("---")
    st.markdown(
        "<div class='muted'>Tip: if your briefs feel generic, the problem is usually broad collection queries or weak filtering. Tightening your collection improves the brief immediately.</div>",
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# DATA LOAD
# =========================================================
if "records" not in st.session_state:
    st.session_state.records = []
    st.session_state.last_run = None
    st.session_state.used_demo = True

if run:
    try:
        if not newsapi_key:
            st.warning("No NewsAPI key detected. Loaded demo data instead.")
            raw_articles = fallback_demo_articles()
            st.session_state.used_demo = True
        else:
            with st.spinner("Collecting and scoring reporting..."):
                raw_articles = fetch_news(
                    query=query,
                    api_key=newsapi_key,
                    page_size=article_limit,
                    language=language,
                    days_back=lookback_days,
                )
            st.session_state.used_demo = False

        st.session_state.records = [build_article_record(a) for a in raw_articles]
        st.session_state.last_run = utc_now()
    except Exception as exc:
        st.error(f"Collection failed: {exc}")

if use_demo:
    st.session_state.records = [build_article_record(a) for a in fallback_demo_articles()]
    st.session_state.last_run = utc_now()
    st.session_state.used_demo = True

if not st.session_state.records:
    st.session_state.records = [build_article_record(a) for a in fallback_demo_articles()]
    st.session_state.last_run = utc_now()
    st.session_state.used_demo = True


df = to_dataframe(st.session_state.records)


# =========================================================
# TOP FILTERS
# =========================================================
st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">🌍 Global OSINT Threat Monitoring Dashboard</div>
        <div class="hero-subtitle">
            Analyst-focused monitoring for cyber, geopolitical, infrastructure, and public safety developments.
            Structured to produce intelligence-style briefs rather than generic news summaries.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([3, 1])
with left:
    available_categories = sorted(df["category"].dropna().unique().tolist()) if not df.empty else []
    selected_categories = st.multiselect("Filter by category", available_categories, default=available_categories)
with right:
    selected_severity = st.multiselect("Filter by severity", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])

filtered_df = df.copy()
if selected_categories:
    filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]
if selected_severity:
    filtered_df = filtered_df[filtered_df["severity"].isin(selected_severity)]

search_term = st.text_input("Search headlines, sectors, locations, or entities")
if search_term:
    pattern = search_term.lower()
    filtered_df = filtered_df[
        filtered_df.apply(
            lambda row: pattern in str(row["title"]).lower()
            or pattern in str(row["snippet"]).lower()
            or pattern in " ".join(row["sectors"] if isinstance(row["sectors"], list) else []).lower()
            or pattern in " ".join(row["locations"] if isinstance(row["locations"], list) else []).lower()
            or pattern in " ".join(row["entities"] if isinstance(row["entities"], list) else []).lower(),
            axis=1,
        )
    ]

filtered_df = filtered_df.sort_values(["severity_score", "published_dt"], ascending=[False, False])
brief = make_brief(filtered_df)


# =========================================================
# KPI ROW
# =========================================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi("Articles", str(len(filtered_df)), "Items in current view")
with col2:
    render_kpi("High Severity", str(int((filtered_df["severity"] == "High").sum()) if not filtered_df.empty else 0), "Immediate attention items")
with col3:
    dominant_cat = filtered_df["category"].mode().iloc[0] if not filtered_df.empty and not filtered_df["category"].mode().empty else "N/A"
    render_kpi("Dominant Risk", dominant_cat, "Most frequent incident type")
with col4:
    last_run_label = st.session_state.last_run.strftime("%d %b %H:%M UTC") if st.session_state.last_run else "Not run"
    render_kpi("Collection Status", "Demo" if st.session_state.used_demo else "Live", f"Last run: {last_run_label}")


# =========================================================
# MAIN GRID
# =========================================================
main_left, main_right = st.columns([1.35, 1])

with main_left:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("## Intelligence Brief")
    st.markdown(f"<div class='pill {severity_css('High' if 'High risk' in brief['headline'] or brief['headline'].startswith('High') else 'Medium' if brief['headline'].startswith('Medium') else 'Low')}'>{brief['headline']}</div>", unsafe_allow_html=True)

    st.markdown('<div class="brief-box">', unsafe_allow_html=True)
    st.markdown("**Key Developments**")
    st.write(brief["key_developments"])
    st.markdown("**Risk Assessment**")
    st.write(brief["risk_assessment"])
    st.markdown("**Analyst Insight**")
    st.write(brief["analyst_insight"])
    st.markdown("**Recommended Actions**")
    st.write(brief["recommended_actions"])
    st.markdown('</div>', unsafe_allow_html=True)

    export_text = export_brief_text(brief, filtered_df)
    st.download_button(
        "Download brief (.txt)",
        data=export_text,
        file_name="osint_intelligence_brief.txt",
        mime="text/plain",
    )
    st.markdown('</div>', unsafe_allow_html=True)

with main_right:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("## Threat Snapshot")

    top_locations = top_items(flatten_column(filtered_df, "locations"), 5)
    top_sectors = top_items(flatten_column(filtered_df, "sectors"), 5)

    st.markdown("**Top Locations**")
    if top_locations:
        st.markdown(" ".join([f"<span class='pill'>{name} · {count}</span>" for name, count in top_locations]), unsafe_allow_html=True)
    else:
        st.markdown("<div class='muted'>No mapped locations detected.</div>", unsafe_allow_html=True)

    st.markdown("**Affected Sectors**")
    if top_sectors:
        st.markdown(" ".join([f"<span class='pill'>{name} · {count}</span>" for name, count in top_sectors]), unsafe_allow_html=True)
    else:
        st.markdown("<div class='muted'>No sector concentration detected.</div>", unsafe_allow_html=True)

    st.markdown("**Priority Headlines**")
    for _, row in filtered_df.head(5).iterrows():
        st.markdown(
            f"<div class='pill {severity_css(row['severity'])}'>{row['severity']}</div> {row['title']}",
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# CHARTS
# =========================================================
chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    timeline_fig = make_timeline_chart(filtered_df)
    if timeline_fig is not None:
        st.plotly_chart(timeline_fig, use_container_width=True)
    else:
        st.info("No timeline data available.")
    st.markdown('</div>', unsafe_allow_html=True)

with chart_col2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    category_fig = make_category_chart(filtered_df)
    if category_fig is not None:
        st.plotly_chart(category_fig, use_container_width=True)
    else:
        st.info("No category data available.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
geo_fig = make_geo_chart(filtered_df)
if geo_fig is not None:
    st.plotly_chart(geo_fig, use_container_width=True)
else:
    st.info("No mapped locations detected in the current result set.")
st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# ARTICLE FEED
# =========================================================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("## Incident Feed")

if filtered_df.empty:
    st.warning("No articles matched the current filters.")
else:
    for _, row in filtered_df.head(25).iterrows():
        render_article_card(row)

st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# ANALYST DEBUG VIEW
# =========================================================
with st.expander("Analyst debug view"):
    st.write(
        "Use this section to inspect why the brief is changing. If output quality drops, this table usually reveals whether the issue is poor source coverage, weak scoring, or broad collection terms."
    )

    debug_df = filtered_df.copy()
    if not debug_df.empty:
        debug_df["locations"] = debug_df["locations"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
        debug_df["sectors"] = debug_df["sectors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
        debug_df["entities"] = debug_df["entities"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
    st.dataframe(
        debug_df[
            [
                "published_dt",
                "severity",
                "severity_score",
                "category",
                "source",
                "title",
                "locations",
                "sectors",
                "entities",
                "url",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption(
    "Built for analyst-style monitoring. This version prioritises structured brief generation, stronger scoring, and clearer operational relevance over generic summarisation."
)
