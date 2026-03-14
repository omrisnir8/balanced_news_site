import feedparser
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timezone
import time
import calendar
from typing import List, Dict

# Headers are critical for many news sites to prevent 403 Forbidden
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

SOURCES = {
    "N12": {"url": "https://rcs.mako.co.il/rss/31750a2610f26110VgnVCM1000005201000aRCRD.xml", "location": "Israel", "orientation": "Center", "bias": "Mainstream commercial"},
    "Kan 11": {"url": "https://www.kan.org.il/rss/", "location": "Israel", "orientation": "Center", "bias": "Public broadcaster, factual"},
    "Ynet": {"url": "http://www.ynet.co.il/Integration/StoryRss2.xml", "location": "Israel", "orientation": "Center/Center-Right", "bias": "Mainstream commercial"},
    "Haaretz": {"url": "https://www.haaretz.co.il/cmlink/1.1470869", "location": "Israel", "orientation": "Left", "bias": "Liberal bias"},
    "Israel Hayom": {"url": "https://www.israelhayom.co.il/rss.xml", "location": "Israel", "orientation": "Right", "bias": "Conservative bias"},
    "Reshet 13": {"url": "https://13tv.co.il/rss/news/", "location": "Israel", "orientation": "Center", "bias": "Mainstream commercial"},
    "Now 14": {"url": "https://www.now14.co.il/feed/", "location": "Israel", "orientation": "Far-Right", "bias": "Strongly conservative bias"},
    "TheMarker": {"url": "https://www.themarker.com/cmlink/1.146022", "location": "Israel", "orientation": "Center-Left", "bias": "Economic focus, reformist"},
    "Calcalist": {"url": "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml", "location": "Israel", "orientation": "Center", "bias": "Economic & Tech focus"},

    # Global Sources
    "Reuters": {"url": "https://news.google.com/rss/search?q=source:Reuters", "location": "UK", "orientation": "Center", "bias": "Neutral, highly factual"},
    "Associated Press (AP)": {"url": "https://news.google.com/rss/search?q=source:%22Associated+Press%22", "location": "USA", "orientation": "Center", "bias": "Neutral, highly factual"},
    "Agence France-Presse (AFP)": {"url": "https://news.google.com/rss/search?q=source:%22AFP%22", "location": "France", "orientation": "Center", "bias": "Neutral, global news agency"},
    "BBC News": {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "location": "UK", "orientation": "Center", "bias": "Slight Center-Left leaning"},
    "Neue Zürcher Zeitung (NZZ)": {"url": "https://www.nzz.ch/international.rss", "location": "Switzerland", "orientation": "Center-Right", "bias": "Classical liberal, analytical European perspective"},
    "Al Jazeera": {"url": "https://news.google.com/rss/search?q=source:%22Al+Jazeera%22", "location": "Qatar", "orientation": "Middle East focus", "bias": "Anti-Israel / Pro-Palestinian"},
    "South China Morning Post (SCMP)": {"url": "https://www.scmp.com/rss/91/feed", "location": "Hong Kong", "orientation": "Pro-Beijing to Center", "bias": "Asian geopolitical perspective"},
    "The Hindu": {"url": "https://www.thehindu.com/news/international/feeder/default.rss", "location": "India", "orientation": "Center-Left", "bias": "Global South perspective"},
    
    # Technology, Culture, Economics & Travel
    "Bloomberg": {"url": "https://news.google.com/rss/search?q=source:%22Bloomberg%22", "location": "USA", "orientation": "Center", "bias": "Global markets and economics"},
    "Financial Times": {"url": "https://news.google.com/rss/search?q=source:%22Financial+Times%22", "location": "UK", "orientation": "Center", "bias": "Global markets and economics"},
    "Wired": {"url": "https://www.wired.com/feed/rss", "location": "USA", "orientation": "Center-Left", "bias": "Tech culture and consumer tech"},
    "The Verge": {"url": "https://www.theverge.com/rss/index.xml", "location": "USA", "orientation": "Center-Left", "bias": "Tech culture and consumer tech"},
    "National Geographic": {"url": "https://news.google.com/rss/search?q=source:%22National+Geographic%22", "location": "USA", "orientation": "Center", "bias": "Global culture, science"},
    "Condé Nast Traveler": {"url": "https://www.cntraveler.com/feed/rss", "location": "USA", "orientation": "Center", "bias": "High-end travel"},
}

def fetch_rss_feed(source_name: str, url: str) -> List[Dict]:
    """Fetches and parses an RSS feed using requests to bypass basic bot protection."""
    print(f"Fetching RSS from {source_name}: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        articles = []
        for entry in feed.entries[:3]: # Limit to prevent LLM token overflow on Groq free tier
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime.fromtimestamp(calendar.timegm(entry.published_parsed), tz=timezone.utc)
            else:
                 published = datetime.now(timezone.utc)
                 
            summary = ""
            if hasattr(entry, 'summary'):
                soup = BeautifulSoup(entry.summary, "html.parser")
                summary = soup.get_text()

            articles.append({
                "source": source_name,
                "title": entry.title,
                "url": entry.link,
                "published_at": published,
                "summary": summary
            })
        return articles
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
        return []

def scrape_all_sources() -> List[Dict]:
    """Iterates through configured sources and fetches latest articles."""
    all_articles = []
    for name, metadata in SOURCES.items():
         articles = fetch_rss_feed(name, metadata["url"])
         all_articles.extend(articles)
         
    return all_articles

if __name__ == "__main__":
    results = scrape_all_sources()
    print(f"Fetched {len(results)} articles.")
    if results:
        print(f"Sample: {results[0]}")
