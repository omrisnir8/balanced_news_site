import feedparser
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timezone
import time
import calendar
from typing import List, Dict

# Headers are critical for many news sites to prevent 403 Forbidden
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

SOURCES = {
    "N12": {"url": "https://www.mako.co.il/mako-vod-rss/Article-c20e238cb050481026.htm", "location": "Israel", "orientation": "Center", "bias": "Mainstream commercial"},
    "Ynet": {"url": "http://www.ynet.co.il/Integration/StoryRss2.xml", "location": "Israel", "orientation": "Center/Center-Right", "bias": "Mainstream commercial"},
    "Haaretz": {"url": "https://www.haaretz.co.il/cmlink/1.1470869", "location": "Israel", "orientation": "Left", "bias": "Liberal bias"},
    "Israel Hayom": {"url": "https://www.israelhayom.co.il/rss.xml", "location": "Israel", "orientation": "Right", "bias": "Conservative bias"},
    "Kan 11": {"url": "https://www.kan.org.il/rss/", "location": "Israel", "orientation": "Center", "bias": "Public broadcaster, factual"},
    
    # Global Sources
    "Al Jazeera": {"url": "https://www.aljazeera.com/xml/rss/all.xml", "location": "Qatar", "orientation": "Middle East focus", "bias": "Anti-Israel / Pro-Palestinian"},
    "BBC News": {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "location": "UK", "orientation": "Center", "bias": "Slight Center-Left leaning"}
}

def fetch_rss_feed(source_name: str, url: str) -> List[Dict]:
    """Fetches and parses an RSS feed using requests to bypass basic bot protection."""
    print(f"Fetching RSS from {source_name}: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        articles = []
        for entry in feed.entries[:8]: # Limit
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
