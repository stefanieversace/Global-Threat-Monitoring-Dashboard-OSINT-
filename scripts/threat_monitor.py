import requests
from datetime import datetime

API_KEY = "YOUR_API_KEY_HERE"

KEYWORDS = "terrorism OR protest OR conflict OR attack OR unrest"

def fetch_news():
    url = f"https://newsapi.org/v2/everything?q={KEYWORDS}&language=en&sortBy=publishedAt&pageSize=20&apiKey={API_KEY}"
    response = requests.get(url)
    return response.json().get("articles", [])

def classify_risk(text):
    text = text.lower()
    
    if any(word in text for word in ["bomb", "explosion", "attack", "terror"]):
        return "HIGH"
    elif any(word in text for word in ["protest", "clash", "riot"]):
        return "MEDIUM"
    else:
        return "LOW"

def generate_brief():
    articles = fetch_news()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    report = f"GLOBAL INTELLIGENCE BRIEF\nGenerated: {now}\n\n"
    
    for article in articles[:10]:
        title = article.get("title", "No title")
        description = article.get("description", "No description")
        source = article.get("source", {}).get("name", "Unknown")
        
        risk = classify_risk(title + description)
        
        report += f"Title: {title}\n"
        report += f"Source: {source}\n"
        report += f"Risk Level: {risk}\n"
        report += f"Summary: {description}\n"
        report += "-" * 50 + "\n"
    
    return report

if __name__ == "__main__":
    brief = generate_brief()
    
    with open("output/daily_brief.txt", "w") as f:
        f.write(brief)
    
    print("Brief generated successfully.")
