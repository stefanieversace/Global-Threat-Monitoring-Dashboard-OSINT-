import requests
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

API_KEY = "YOUR_API_KEY_HERE"

KEYWORDS = "terrorism OR protest OR conflict OR attack OR unrest"

KNOWN_LOCATIONS = [
    "Paris", "London", "New York", "Baghdad", "Moscow", "Kyiv", "Jerusalem",
    "Tel Aviv", "Damascus", "Beirut", "Istanbul", "Cairo", "Tehran", "Delhi",
    "Mumbai", "Beijing", "Shanghai", "Tokyo", "Seoul", "Hong Kong", "Bangkok",
    "Manila", "Jakarta", "Sydney", "Melbourne", "Lagos", "Nairobi", "Khartoum",
    "Tripoli", "Tunis", "Algiers", "Sanaa", "Kabul", "Islamabad", "Karachi",
    "Mexico City", "Bogota", "Sao Paulo", "Rio de Janeiro", "Buenos Aires",
    "Santiago", "Caracas", "Lima", "Brussels", "Berlin", "Rome", "Madrid",
    "Athens", "Warsaw", "Budapest", "Bucharest"
]

def fetch_news():
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={KEYWORDS}&language=en&sortBy=publishedAt&pageSize=20&apiKey={API_KEY}"
    )
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json().get("articles", [])

def classify_risk(text):
    text = text.lower()

    if any(word in text for word in ["bomb", "explosion", "attack", "terror"]):
        return "HIGH"
    elif any(word in text for word in ["protest", "clash", "riot"]):
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

    assessment += "Recommendation:\n"
    assessment += "Continue monitoring for escalation, especially in locations with repeated reporting.\n"

    return assessment

def extract_location(text):
    for location in KNOWN_LOCATIONS:
        if location.lower() in text.lower():
            return location
    return None

def geocode_location(location_name):
    if not location_name:
        return None

    geolocator = Nominatim(user_agent="osint_threat_monitor")

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

    for article in articles[:10]:
        title = article.get("title", "No title")
        description = article.get("description", "No description")
        source = article.get("source", {}).get("name", "Unknown")

        combined_text = f"{title} {description}"
        risk = classify_risk(combined_text)
        risk_levels.append(risk)

        found_location = extract_location(combined_text)
        geo = geocode_location(found_location)

        if geo:
            mapped_events.append({
                "title": title,
                "source": source,
                "risk": risk,
                "location": geo["name"],
                "lat": geo["lat"],
                "lon": geo["lon"]
            })

        report += f"Title: {title}\n"
        report += f"Source: {source}\n"
        report += f"Risk Level: {risk}\n"
        report += f"Summary: {description}\n"
        report += f"Detected Location: {found_location if found_location else 'Unknown'}\n"
        report += "-" * 50 + "\n"

    report += generate_analyst_assessment(risk_levels)
    return report, mapped_events

if __name__ == "__main__":
    brief, mapped_events = generate_brief()

    with open("output/daily_brief.txt", "w") as f:
        f.write(brief)

    print("Brief generated successfully.")
    print(f"Mapped events: {len(mapped_events)}")
