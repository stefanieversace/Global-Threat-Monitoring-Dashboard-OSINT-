import requests
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import spacy

API_KEY = st.secrets["NEWS_API_KEY"]

KEYWORDS = "terrorism OR protest OR conflict OR attack OR unrest OR violence OR explosion OR riot"

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
HISTORY_FILE = DATA_DIR / "history.csv"

nlp = spacy.load("en_core_web_sm")

FALLBACK_LOCATIONS = [
    "Paris", "London", "New York", "Washington", "Los Angeles",
    "Baghdad", "Moscow", "Kyiv", "Jerusalem", "Tel Aviv", "Damascus",
    "Beirut", "Istanbul", "Cairo", "Tehran", "Delhi", "Mumbai",
    "Beijing", "Shanghai", "Tokyo", "Seoul", "Hong Kong", "Bangkok",
    "Manila", "Jakarta", "Sydney", "Melbourne", "Lagos", "Nairobi",
    "Khartoum", "Tripoli", "Tunis", "Algiers", "Sanaa", "Kabul",
    "Islamabad", "Karachi", "Mexico City", "Bogota", "Sao Paulo",
    "Rio de Janeiro", "Buenos Aires", "Santiago", "Caracas", "Lima",
    "Brussels", "Berlin", "Rome", "Madrid", "Athens", "Warsaw",
    "Budapest", "Bucharest", "Gaza", "Syria", "Israel", "Ukraine",
    "Russia", "Iran", "Iraq", "Afghanistan", "Pakistan", "India",
    "China", "Taiwan", "Sudan", "Yemen", "Lebanon", "Turkey",
    "Egypt", "West Bank", "Ramallah", "Doha", "Dubai", "Riyadh",
    "Jeddah", "Amman"
]

REGION_MAP = {
    "Paris": "Europe",
    "London": "Europe",
    "Brussels": "Europe",
    "Berlin": "Europe",
    "Rome": "Europe",
    "Madrid": "Europe",
    "Athens": "Europe",
    "Warsaw": "Europe",
    "Budapest": "Europe",
    "Bucharest": "Europe",
    "Kyiv": "Europe",
    "Moscow": "Europe",
    "Ukraine": "Europe",
    "Russia": "Europe",
    "Jerusalem": "Middle East",
    "Tel Aviv": "Middle East",
    "Damascus": "Middle East",
    "Beirut": "Middle East",
    "Cairo": "Middle East",
    "Tehran": "Middle East",
    "Baghdad": "Middle East",
    "Gaza": "Middle East",
    "Israel": "Middle East",
    "Syria": "Middle East",
    "Iran": "Middle East",
    "Iraq": "Middle East",
    "Lebanon": "Middle East",
    "Turkey": "Middle East",
    "Yemen": "Middle East",
    "West Bank": "Middle East",
    "Ramallah": "Middle East",
    "Doha": "Middle East",
    "Dubai": "Middle East",
    "Riyadh": "Middle East",
    "Jeddah": "Middle East",
    "Amman": "Middle East",
    "Delhi": "Asia-Pacific",
    "Mumbai": "Asia-Pacific",
    "Beijing": "Asia-Pacific",
    "Shanghai": "Asia-Pacific",
    "Tokyo": "Asia-Pacific",
    "Seoul": "Asia-Pacific",
    "Hong Kong": "Asia-Pacific",
    "Bangkok": "Asia-Pacific",
    "Manila": "Asia-Pacific",
    "Jakarta": "Asia-Pacific",
    "India": "Asia-Pacific",
    "China": "Asia-Pacific",
    "Taiwan": "Asia-Pacific",
    "Pakistan": "Asia-Pacific",
    "Afghanistan": "Asia-Pacific",
    "Islamabad": "Asia-Pacific",
    "Karachi": "Asia-Pacific",
    "Sydney": "Asia-Pacific",
    "Melbourne": "Asia-Pacific",
    "New York": "North America",
    "Washington": "North America",
    "Los Angeles": "North America",
    "Mexico City": "Latin America",
    "Bogota": "Latin America",
    "Sao Paulo": "Latin America",
    "Rio de Janeiro": "Latin America",
    "Buenos Aires": "Latin America",
    "Santiago": "Latin America",
    "Caracas": "Latin America",
    "Lima": "Latin America",
    "Lagos": "Africa",
    "Nairobi": "Africa",
    "Khartoum": "Africa",
    "Tripoli": "Africa",
    "Tunis": "Africa",
    "Algiers": "Africa",
    "Sudan": "Africa",
    "Egypt": "Africa",
    "Sanaa": "Middle East"
}

SOURCE_CONFIDENCE = {
    "Reuters": "High",
    "BBC News": "High",
    "Associated Press": "High",
    "AP News": "High",
    "Bloomberg": "High",
    "Financial Times": "High",
    "Al Jazeera English": "Medium",
    "CNN": "Medium",
    "The Guardian": "Medium",
    "NBC News": "Medium"
}

SEVERITY_WEIGHTS = {
    "attack": 3,
    "terror": 3,
    "terrorism": 3,
    "bomb": 3,
    "explosion": 3,
    "missile": 3,
    "shooting": 3,
    "hostage": 3,
    "riot": 2,
    "clash": 2,
    "protest": 2,
    "unrest": 2,
    "violence": 2,
    "border": 1,
    "election": 1,
    "military": 2,
    "strike": 1,
    "crisis": 2
}


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_history():
    ensure_data_dir()
    if HISTORY_FILE.exists():
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame(columns=["date", "high_count", "medium_count", "low_count", "watchlist_matches"])


def save_history(high_count, medium_count, low_count, watchlist_matches):
    ensure_data_dir()

    today = datetime.utcnow().strftime("%Y-%m-%d")
    row = pd.DataFrame([{
        "date": today,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "watchlist_matches": watchlist_matches
    }])

    if HISTORY_FILE.exists():
        existing = pd.read_csv(HISTORY_FILE)
        combined = pd.concat([existing, row], ignore_index=True)
        combined.to_csv(HISTORY_FILE, index=False)
    else:
        row.to_csv(HISTORY_FILE, index=False)


def fetch_news():
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={KEYWORDS}&language=en&sortBy=publishedAt&pageSize=20&apiKey={API_KEY}"
    )

    response = requests.get(url, timeout=20)

    if response.status_code != 200:
        raise Exception(
            f"News API request failed. Status: {response.status_code}. Response: {response.text}"
        )

    return response.json().get("articles", [])


def score_risk(text):
    text = (text or "").lower()
    score = 0

    for term, weight in SEVERITY_WEIGHTS.items():
        if term in text:
            score += weight

    return score


def classify_risk(score):
    if score >= 5:
        return "HIGH"
    if score >= 3:
        return "MEDIUM"
    return "LOW"


def get_source_confidence(source):
    return SOURCE_CONFIDENCE.get(source, "Low")


def extract_location(text):
    if not text:
        return None

    doc = nlp(text)

    # Prefer geopolitical entities first
    for ent in doc.ents:
        if ent.label_ == "GPE":
            cleaned = ent.text.strip()
            if cleaned:
                return cleaned

    # Then broader location entities
    for ent in doc.ents:
        if ent.label_ == "LOC":
            cleaned = ent.text.strip()
            if cleaned:
                return cleaned

    # Fallback to keyword matching
    text_lower = text.lower()
    for location in FALLBACK_LOCATIONS:
        if location.lower() in text_lower:
            return location

    return None


def geocode_location(location_name, geolocator):
    if not location_name:
        return None

    try:
        location = geolocator.geocode(
            location_name,
            timeout=10,
            exactly_one=True
        )
        if location:
            return {
                "name": location_name,
                "lat": location.latitude,
                "lon": location.longitude
            }
    except (GeocoderTimedOut, GeocoderServiceError, Exception):
        return None

    return None


def get_region(location_name):
    if not location_name:
        return "Unknown"

    for known_name, region in REGION_MAP.items():
        if known_name.lower() in location_name.lower():
            return region

    return "Other"


def watchlist_match(text, watchlist_terms):
    if not watchlist_terms:
        return False

    text_lower = (text or "").lower()
    return any(term.lower() in text_lower for term in watchlist_terms)


def generate_key_judgements(risk_levels, region_counts, watchlist_matches):
    high_count = risk_levels.count("HIGH")
    medium_count = risk_levels.count("MEDIUM")

    judgements = []

    if medium_count > high_count and medium_count > 0:
        judgements.append(
            "Current reporting is primarily driven by protest, unrest, and lower-intensity disruptive activity."
        )
    elif high_count > 0:
        judgements.append(
            "Current reporting includes at least one high-severity incident with potential operational relevance."
        )

    if region_counts:
        top_region = max(region_counts, key=region_counts.get)
        judgements.append(
            f"Reporting is most concentrated in {top_region}, indicating a possible regional clustering of incidents."
        )

    if watchlist_matches > 0:
        judgements.append(
            "Watchlist-matched reporting is present in current results and may warrant prioritised monitoring."
        )
    else:
        judgements.append("No watchlist terms were matched in current reporting.")

    while len(judgements) < 3:
        judgements.append(
            "The current reporting picture remains fluid and should be monitored for escalation or geographic spread."
        )

    return judgements[:3]


def generate_analyst_assessment(risk_levels, region_counts, watchlist_matches):
    high_count = risk_levels.count("HIGH")
    medium_count = risk_levels.count("MEDIUM")
    low_count = risk_levels.count("LOW")

    assessment = "\nANALYST ASSESSMENT:\n\n"

    if high_count > 0:
        assessment += (
            "Current reporting indicates elevated threat activity, including at least one high-risk incident. "
            "This suggests a need for close monitoring of fast-moving developments.\n\n"
        )
    elif medium_count > 0:
        assessment += (
            "Current reporting indicates ongoing unrest and protest activity. "
            "While no immediate high-risk pattern dominates reporting, the situation may escalate quickly.\n\n"
        )
    else:
        assessment += (
            "Current reporting suggests a low immediate threat environment, though monitoring should continue for changes.\n\n"
        )

    assessment += "Key trends:\n"
    assessment += f"- High-risk incidents: {high_count}\n"
    assessment += f"- Medium-risk incidents: {medium_count}\n"
    assessment += f"- Low-risk incidents: {low_count}\n"

    if region_counts:
        top_region = max(region_counts, key=region_counts.get)
        assessment += f"- Most affected region: {top_region}\n"

    assessment += f"- Watchlist matches: {watchlist_matches}\n\n"

    assessment += "Operational outlook:\n"
    if high_count >= 2:
        assessment += (
            "Multiple high-risk incidents were identified in current reporting. "
            "This suggests a heightened operating environment and may warrant closer monitoring of affected regions.\n\n"
        )
    elif medium_count >= 3:
        assessment += (
            "Current reporting is dominated by protest and unrest activity. "
            "These developments may create disruption risks for personnel, travel, and business operations.\n\n"
        )
    else:
        assessment += (
            "No dominant high-severity trend is evident in current reporting, although emerging incidents should continue to be reviewed.\n\n"
        )

    assessment += "Recommendation:\n"
    assessment += "Continue monitoring for escalation, especially in locations with repeated reporting or watchlist relevance.\n"

    return assessment


def generate_brief(max_articles=10, watchlist_terms=None):
    if watchlist_terms is None:
        watchlist_terms = []

    articles = fetch_news()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    report = f"GLOBAL INTELLIGENCE BRIEF\nGenerated: {now}\n\n"
    risk_levels = []
    mapped_events = []
    unmapped_articles = []
    region_counts = {}
    watchlist_matches = 0

    geolocator = Nominatim(user_agent="osint_threat_monitor")

    for article in articles[:max_articles]:
        title = article.get("title", "No title")
        description = article.get("description", "No description")
        source = article.get("source", {}).get("name", "Unknown")
        published_at = article.get("publishedAt", "Unknown")
        url = article.get("url", "")

        combined_text = f"{title} {description}"
        score = score_risk(combined_text)
        risk = classify_risk(score)
        confidence = get_source_confidence(source)
        risk_levels.append(risk)

        found_location = extract_location(combined_text)
        region = get_region(found_location)
        geo = geocode_location(found_location, geolocator)
        is_watchlist_match = watchlist_match(combined_text, watchlist_terms)

        if is_watchlist_match:
            watchlist_matches += 1

        if region != "Unknown":
            region_counts[region] = region_counts.get(region, 0) + 1

        if geo:
            mapped_events.append({
                "title": title,
                "source": source,
                "risk": risk,
                "score": score,
                "confidence": confidence,
                "location": geo["name"],
                "region": region,
                "lat": geo["lat"],
                "lon": geo["lon"],
                "published_at": published_at,
                "url": url,
                "watchlist_match": is_watchlist_match
            })
        else:
            unmapped_articles.append({
                "title": title,
                "source": source,
                "risk": risk,
                "score": score,
                "confidence": confidence,
                "detected_location": found_location if found_location else "None",
                "published_at": published_at,
                "url": url,
                "watchlist_match": is_watchlist_match
            })

        report += f"Title: {title}\n"
        report += f"Source: {source}\n"
        report += f"Risk Level: {risk}\n"
        report += f"Severity Score: {score}\n"
        report += f"Confidence: {confidence}\n"
        report += f"Summary: {description}\n"
        report += f"Detected Location: {found_location if found_location else 'Unknown'}\n"
        report += f"Region: {region}\n"
        report += f"Watchlist Match: {'Yes' if is_watchlist_match else 'No'}\n"
        report += f"Published: {published_at}\n"
        report += f"URL: {url}\n"
        report += "-" * 50 + "\n"

    key_judgements = generate_key_judgements(risk_levels, region_counts, watchlist_matches)
    report += "\nTOP 3 KEY JUDGEMENTS:\n\n"
    for idx, judgement in enumerate(key_judgements, start=1):
        report += f"{idx}. {judgement}\n"
    report += "\n"
    report += generate_analyst_assessment(risk_levels, region_counts, watchlist_matches)

    high_count = risk_levels.count("HIGH")
    medium_count = risk_levels.count("MEDIUM")
    low_count = risk_levels.count("LOW")

    save_history(high_count, medium_count, low_count, watchlist_matches)

    summary = {
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "watchlist_matches": watchlist_matches,
        "region_counts": region_counts,
        "key_judgements": key_judgements
    }

    return report, mapped_events, unmapped_articles, summary
