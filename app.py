import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
import xml.etree.ElementTree as ET

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Global Threat Monitor", layout="wide")

st.markdown("<style>header {visibility:hidden;}</style>", unsafe_allow_html=True)
st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)

st.markdown("""
<div style="font-size:38px;font-weight:800;text-align:center;">
🌍 Global Threat Monitor
</div>
<div style="text-align:center;color:#9fb0cf;margin-bottom:25px;">
AI Intelligence • Multi-Source Threat Detection • SOC Simulation
</div>
""", unsafe_allow_html=True)

# =========================
# API KEY
# =========================
def get_key():
    try:
        return st.secrets["NEWSAPI_KEY"]
    except:
        return None

API_KEY = get_key()

# =========================
# LOCATIONS
# =========================
LOCATIONS = {
    "london": (51.5074, -0.1278),
    "paris": (48.8566, 2.3522),
    "new york": (40.7128, -74.0060),
    "dubai": (25.2048, 55.2708),
    "tokyo": (35.6762, 139.6503),
    "sydney": (-33.8688, 151.2093),
}

def extract_location(text):
    text = text.lower()
    for loc in LOCATIONS:
        if loc in text:
            return loc.title()
    return "Global"

def coords(loc):
    return LOCATIONS.get(loc.lower(), (20, 0))

# =========================
# SEVERITY
# =========================
def severity_score(text):
    score = 20
    text = text.lower()

    if any(x in text for x in ["ransomware","attack","breach","explosion"]):
        score += 40
    if any(x in text for x in ["protest","fraud","phishing"]):
        score += 20

    return min(score, 100)

def severity_label(score):
    if score >= 70: return "High"
    if score >= 40: return "Medium"
    return "Low"

# =========================
# MITRE
# =========================
def mitre(text):
    if "phishing" in text.lower(): return "T1566"
    if "ransomware" in text.lower(): return "T1486"
    if "ddos" in text.lower(): return "T1498"
    return "T1595"

# =========================
# AI SUMMARY (SIMULATED)
# =========================
def generate_ai_summary(df):
    top = df.head(3)

    summary = "EXECUTIVE INTELLIGENCE SUMMARY\n\n"
    for _, row in top.iterrows():
        summary += f"- {row['title']} ({row['severity']})\n"

    summary += "\nASSESSMENT:\n"
    summary += "Current threat landscape shows elevated cyber and civil risk indicators.\n"
    summary += "High severity events may impact critical infrastructure and operations.\n"

    return summary

# =========================
# MULTI-SOURCE FETCH
# =========================
@st.cache_data(ttl=600)
def fetch_news():
    data = []

    # NewsAPI
    if API_KEY:
        try:
            url = f"https://newsapi.org/v2/everything?q=cyber OR attack OR protest&apiKey={API_KEY}"
            articles = requests.get(url).json().get("articles", [])
            for a in articles:
                data.append({
                    "title": a.get("title"),
                    "desc": a.get("description"),
                    "source": a.get("source", {}).get("name"),
                    "time": a.get("publishedAt")
                })
        except:
            pass

    # RSS fallback
    try:
        rss = requests.get("https://rss.nytimes.com/services/xml/rss/nyt/World.xml")
        root = ET.fromstring(rss.content)
        for item in root.findall(".//item")[:10]:
            data.append({
                "title": item.find("title").text,
                "desc": item.find("description").text,
                "source": "NYTimes",
                "time": item.find("pubDate").text
            })
    except:
        pass

    return data

articles = fetch_news()

# =========================
# PROCESS
# =========================
rows = []

for a in articles:
    text = f"{a.get('title','')} {a.get('desc','')}"
    loc = extract_location(text)
    lat, lon = coords(loc)

    score = severity_score(text)

    rows.append({
        "title": a.get("title"),
        "source": a.get("source"),
        "time": a.get("time"),
        "location": loc,
        "lat": lat,
        "lon": lon,
        "score": score,
        "severity": severity_label(score),
        "mitre": mitre(text),
        "desc": a.get("desc")
    })

df = pd.DataFrame(rows)

# fallback
if df.empty:
    df = pd.DataFrame({
        "title":["Cyber attack London","Protest Paris"],
        "source":["Sim","Sim"],
        "time":pd.date_range(end=datetime.now(), periods=2),
        "location":["London","Paris"],
        "lat":[51.5,48.8],
        "lon":[-0.12,2.35],
        "score":[80,50],
        "severity":["High","Medium"],
        "mitre":["T1486","T1595"],
        "desc":["sim","sim"]
    })

df["time"] = pd.to_datetime(df["time"], errors="coerce")

# =========================
# METRICS
# =========================
c1,c2,c3 = st.columns(3)
c1.metric("Incidents", len(df))
c2.metric("High Risk", (df["severity"]=="High").sum())
c3.metric("Sources", df["source"].nunique())

# =========================
# MAP
# =========================
st.subheader("🗺️ Intelligence Map")

m = folium.Map(location=[20,0], zoom_start=2, tiles="CartoDB dark_matter")

HeatMap([[r["lat"],r["lon"],r["score"]/100] for _,r in df.iterrows()]).add_to(m)

cluster = MarkerCluster().add_to(m)

for _,r in df.iterrows():
    folium.Marker(
        [r["lat"],r["lon"]],
        popup=r["title"]
    ).add_to(cluster)

st_folium(m, height=500)

# =========================
# CLICKABLE INCIDENTS
# =========================
st.subheader("🎯 Incident Explorer")

selected = st.selectbox("Select incident", df["title"])

incident = df[df["title"]==selected].iloc[0]

st.markdown(f"""
### {incident['title']}

**Location:** {incident['location']}  
**Severity:** {incident['severity']} ({incident['score']})  
**MITRE:** {incident['mitre']}

{incident['desc']}
""")

# =========================
# MITRE GRID
# =========================
st.subheader("📊 MITRE Coverage")

mitre_counts = df["mitre"].value_counts().reset_index()
mitre_counts.columns = ["Technique","Count"]

fig = px.bar(mitre_counts, x="Technique", y="Count")
fig.update_layout(template="plotly_dark")

st.plotly_chart(fig, use_container_width=True)

# =========================
# AI BRIEF
# =========================
st.subheader("🧠 AI Intelligence Summary")

brief = generate_ai_summary(df)

st.markdown(f"""
<div style='background:#0f172a;padding:15px;border-radius:10px;white-space:pre-wrap;'>
{brief}
</div>
""", unsafe_allow_html=True)

# =========================
# EXPORT
# =========================
st.download_button("Download Brief", brief, "brief.txt")
