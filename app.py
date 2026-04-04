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

# =========================
# PREMIUM UI
# =========================
st.markdown("""
<style>
header {visibility:hidden;}

.stApp {
    background: radial-gradient(circle at top left, rgba(124,156,255,0.12), transparent 25%),
                radial-gradient(circle at top right, rgba(85,230,193,0.10), transparent 20%),
                linear-gradient(180deg, #05070d 0%, #0a1020 100%);
    color: #eef2ff;
}

.title {
    font-size: 42px;
    font-weight: 800;
    text-align: center;
}

.subtitle {
    text-align: center;
    color: #9fb0cf;
    margin-bottom: 30px;
}

.card {
    background: rgba(18,24,38,0.85);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 12px;
}

.alert-high { border-left: 4px solid #ff5c7c; }
.alert-medium { border-left: 4px solid #ffbf66; }
.alert-low { border-left: 4px solid #5ce1a5; }

.brief {
    background:#0f172a;
    padding:18px;
    border-radius:16px;
    white-space:pre-wrap;
    font-family:monospace;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("<div class='title'>🌍 Global Threat Monitor</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Elite OSINT Intelligence Platform • SOC Simulation</div>", unsafe_allow_html=True)

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
    "london": (51.5, -0.12),
    "paris": (48.8, 2.35),
    "new york": (40.7, -74),
    "dubai": (25.2, 55.2),
    "tokyo": (35.6, 139.6),
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

    if any(x in text for x in ["attack","breach","ransomware"]):
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
    return "T1595"

# =========================
# AI SUMMARY
# =========================
def generate_summary(df):
    text = "EXECUTIVE SUMMARY\n\n"
    for t in df.head(3)["title"]:
        text += f"- {t}\n"
    text += "\nThreat Level: Elevated\n"
    return text

# =========================
# FETCH DATA (MULTI SOURCE)
# =========================
@st.cache_data(ttl=600)
def fetch():
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

articles = fetch()

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
    folium.Marker([r["lat"],r["lon"]], popup=r["title"]).add_to(cluster)

st_folium(m, height=500)

# =========================
# INCIDENT EXPLORER
# =========================
st.subheader("🎯 Incident Explorer")

selected = st.selectbox("Select Incident", df["title"])
incident = df[df["title"]==selected].iloc[0]

st.markdown(f"""
### {incident['title']}

**Location:** {incident['location']}  
**Severity:** {incident['severity']} ({incident['score']})  
**MITRE:** {incident['mitre']}

{incident['desc']}
""")

# =========================
# ALERT CARDS
# =========================
st.subheader("🚨 Alerts")

for _,r in df.head(8).iterrows():
    level = "alert-high" if r["severity"]=="High" else "alert-medium" if r["severity"]=="Medium" else "alert-low"

    st.markdown(f"""
    <div class="card {level}">
        <b>{r['title']}</b><br>
        <small>{r['source']} • {r['location']}</small><br>
        <small>{r['severity']} ({r['score']}) • MITRE {r['mitre']}</small>
    </div>
    """, unsafe_allow_html=True)

# =========================
# MITRE CHART
# =========================
st.subheader("📊 MITRE Coverage")

mitre_df = df["mitre"].value_counts().reset_index()
mitre_df.columns = ["Technique","Count"]

fig = px.bar(mitre_df, x="Technique", y="Count")
fig.update_layout(template="plotly_dark")

st.plotly_chart(fig, use_container_width=True)

# =========================
# AI BRIEF
# =========================
st.subheader("🧠 Intelligence Summary")

brief = generate_summary(df)

st.markdown(f"<div class='brief'>{brief}</div>", unsafe_allow_html=True)

# =========================
# EXPORT
# =========================
st.download_button("⬇ Download Brief", brief, "brief.txt")
st.download_button("⬇ Download Data", df.to_csv(index=False), "data.csv")
