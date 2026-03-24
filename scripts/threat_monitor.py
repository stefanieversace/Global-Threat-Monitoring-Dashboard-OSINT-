import requests
import streamlit as st
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

API_KEY = st.secrets["NEWS_API_KEY"]

KEYWORDS = "terrorism OR protest OR conflict OR attack OR unrest"

KNOWN_LOCATIONS = [
    "Paris", "London", "New York", "Baghdad", "Moscow", "Kyiv", "Jerusalem",
    "Tel Aviv", "Damascus", "Beirut", "Istanbul", "Cairo", "Tehran", "Delhi",
    "Mumbai", "Beijing", "Shanghai", "Tokyo", "Seoul", "Hong Kong", "Bangkok",
    "Manila", "Jakarta", "Sydney", "Melbourne", "Lagos", "Nairobi", "Khartoum",
    "Tripoli", "Tunis", "Algiers", "Sanaa", "Kabul", "Islamabad", "Karachi",
    "Mexico City", "Bogota", "Sao Paulo", "Rio de Janeiro", "Buenos Aires",
    "Santiago", "Caracas", "Lima", "Brussels", "Berlin", "Rome", "Madrid",
    "Athens", "Warsaw", "Budapest", "Bucharest", "Gaza", "Syria", "Israel",
    "Ukraine", "Russia", "Iran", "Iraq", "Afghanistan", "Pakistan", "India",
    "China", "Taiwan", "Sudan", "Yemen", "Lebanon", "Turkey", "Egypt"
]

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

def classify_risk(text):
    text = (text or "").lower()

    if any(word in text for word in ["bomb", "explosion", "attack", "terror"]):
        return "HIGH"
    elif any(word in text for word in ["protest", "clash", "riot", "unrest"]):
        return "MEDIUM"
    else:
        return "LOW"

def generate_analyst_assessment(risk_levels):
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
    assessment += f"- Low-risk incidents: {low_count}\n\n"

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
    assessment += "Continue monitoring for escalation, especially in locations with repeated reporting.\n"

    return assessment

def extract_location(text):
    if not text:
        return None

    text_lower = text.lower()

    for location in KNOWN_LOCATIONS:
        if location.lower() in text_lower:
            return location

    return None

def geocode_location(location_name, geolocator):
    if not location_name:
        return None

    try:
        location = geolocator.geocode(location_name, timeout=10)
        if location:
            return {
                "name": location_name,
                "lat": location.latitude,
                "lon": location.longitude
            }
    except (GeocoderTimedOut, GeocoderServiceError):
        return None

    return None

def generate_brief():
    articles = fetch_news()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    report = f"GLOBAL INTELLIGENCE BRIEF\nGenerated: {now}\n\n"
    risk_levels = []
    mapped_events = []
    unmapped_articles = []

    geolocator = Nominatim(user_agent="osint_threat_monitor")

    for article in articles[:10]:
        title = article.get("title", "No title")
        description = article.get("description", "No description")
        source = article.get("source", {}).get("name", "Unknown")
        published_at = article.get("publishedAt", "Unknown")
        url = article.get("url", "")

        combined_text = f"{title} {description}"
        risk = classify_risk(combined_text)
        risk_levels.append(risk)

        found_location = extract_location(combined_text)
        geo = geocode_location(found_location, geolocator)

        if geo:
            mapped_events.append({
                "title": title,
                "source": source,
                "risk": risk,
                "location": geo["name"],
                "lat": geo["lat"],
                "lon": geo["lon"],
                "published_at": published_at,
                "url": url
            })
        else:
            unmapped_articles.append({
                "title": title,
                "source": source,
                "risk": risk,
                "detected_location": found_location if found_location else "None",
                "published_at": published_at,
                "url": url
            })

        report += f"Title: {title}\n"
        report += f"Source: {source}\n"
        report += f"Risk Level: {risk}\n"
        report += f"Summary: {description}\n"
        report += f"Detected Location: {found_location if found_location else 'Unknown'}\n"
        report += f"Published: {published_at}\n"
        report += f"URL: {url}\n"
        report += "-" * 50 + "\n"

    report += generate_analyst_assessment(risk_levels)
    return report, mapped_events, unmapped_articles
