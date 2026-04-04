# 🌍 Global OSINT Threat Monitoring Dashboard

A real-time Open-Source Intelligence (OSINT) dashboard that monitors global security events, assesses risk levels, and visualises threats on a dynamic world map.

Built to simulate workflows used in global intelligence and security operations centres.

---

## 🚀 Live Demo

👉 https://stefanieversace-global-threat-monitoring-dashboard-o-app-as1ple.streamlit.app/

---

## 🧠 Overview

This project collects and analyses open-source news data to:

* Identify emerging global security threats
* Classify incidents by risk severity
* Extract geographic locations using NLP
* Visualise incidents on a global map
* Generate structured intelligence briefings
* Highlight key trends and analyst judgements

---
## 🧾 Example Intelligence Brief

### 🔴 Key Developments
- Civil unrest in Paris disrupting transport networks  
- Ongoing phishing campaign targeting financial institutions  

### ⚠️ Risk Assessment
- Operational Risk: High  
- Geographic Impact: Europe  
- Affected Sectors: Media, Finance  

### 🧠 Analyst Insight

These developments present potential disruption risks to live events and financial systems. 
Organisations should monitor escalation and consider contingency planning.

---

## ⚙️ Features

### 🔍 Intelligence Collection

* Pulls real-time data from NewsAPI
* Filters for relevant security-related keywords

### 🧠 Risk Analysis

* Severity scoring model based on weighted keywords
* Classification into HIGH / MEDIUM / LOW risk

### 📍 Geospatial Mapping

* Uses NLP (spaCy) to extract locations from text
* Converts locations into coordinates using geocoding
* Displays incidents on an interactive map

### 📊 Dashboard & Insights

* Risk summary metrics
* Regional breakdown of incidents
* Trend tracking over time
* Watchlist filtering for custom monitoring

### 📝 Analyst Output

* Auto-generated intelligence brief
* Top 3 key judgements
* Operational assessment and recommendations

---

## 🏗️ Tech Stack

* Python
* Streamlit
* spaCy (NLP)
* Folium (mapping)
* Pandas
* Geopy
* NewsAPI

---

## 📂 Project Structure

```
osint-threat-monitor/
│── app.py
│── scripts/
│   ├── threat_monitor.py
│   └── __init__.py
│── data/
│   └── history.csv
│── requirements.txt
│── README.md
```

---

## ⚡ How It Works

1. Fetches latest global news articles
2. Applies keyword-based filtering for security relevance
3. Scores each article using a severity model
4. Extracts geographic entities using NLP
5. Maps incidents using geocoding
6. Generates structured intelligence outputs

---

## 🔐 Setup Instructions

### 1. Clone the repository

```
git clone https://github.com/stefanieversace/Global-Threat-Monitoring-Dashboard-OSINT-.git
cd Global-Threat-Monitoring-Dashboard-OSINT-
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Download NLP model

```
python -m spacy download en_core_web_sm
```

### 4. Add API key

Create a `.streamlit/secrets.toml` file:

```
NEWS_API_KEY = "your_api_key_here"
```

### 5. Run the app

```
streamlit run app.py
```

---

## 📈 Example Use Cases

* Monitoring global security risks
* Supporting executive travel risk assessments
* Identifying emerging geopolitical threats
* Demonstrating OSINT and intelligence analysis capabilities

---

## 🎯 Key Skills Demonstrated

* Open-source intelligence (OSINT)
* Threat and risk assessment
* NLP-based entity extraction
* Data analysis and visualisation
* Intelligence reporting and structured analysis

---

## 🔮 Future Improvements

* Multi-location extraction per article
* Real-time alert notifications
* Integration with social media intelligence
* Enhanced NLP for more accurate entity detection
* API expansion beyond NewsAPI

---

## 👩‍💻 Author

Stefanie Versace
https://www.linkedin.com/in/stefanie-versace-26766428a

---

## 📌 Notes

This project is designed as a portfolio demonstration of intelligence analysis workflows and does not represent a production-grade threat intelligence system.
