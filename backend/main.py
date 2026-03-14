from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
from database import get_db, init_db, SessionLocal
from models import Cluster, Article, Source
from engine.scraper import scrape_all_sources, SOURCES
from engine.llm_processor import cluster_and_summarize_articles
from datetime import datetime
import dateutil.parser

app = FastAPI(title="Balanced News Aggregator API")

# Global status tracker
refresh_status = {
    "status": "idle",
    "message": "Ready",
    "last_refresh": None,
    "articles_scraped": 0,
    "clusters_created": 0
}

# Setup CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow all. Update in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Balanced News Aggregator API"}

@app.get("/api/status")
def get_status():
    return refresh_status

@app.get("/api/feed")
def get_feed(category: str = None, db: Session = Depends(get_db)):
    query = db.query(Cluster).order_by(desc(Cluster.created_at))
    if category:
        query = query.filter(Cluster.category == category)
    
    clusters = query.limit(20).all()
    
    result = []
    for cluster in clusters:
        articles = []
        for article in cluster.articles:
            articles.append({
                "source_name": article.source.name,
                "location": article.source.location,
                "political_orientation": article.source.political_orientation,
                "known_bias": article.source.known_bias,
                "url": article.original_url,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "titles": {
                    "native": article.original_title,
                    "en": article.title_en,
                    "he": article.title_he
                },
                "bias_warnings": {
                    "en": article.bias_warning_en,
                    "he": article.bias_warning_he
                }
            })
            
        result.append({
            "id": cluster.id,
            "titles": {
                "en": cluster.average_title_en,
                "he": cluster.average_title_he
            },
            "summaries": {
                "en": cluster.comparative_summary_en,
                "he": cluster.comparative_summary_he
            },
            "timestamp": cluster.created_at.isoformat() if cluster.created_at else None,
            "category": cluster.category,
            "sources": articles
        })
    return result

def run_refresh_logic():
    global refresh_status
    db = SessionLocal()
    try:
        refresh_status["status"] = "processing"
        refresh_status["message"] = "Scraping news sources..."
        
        # 1. Scrape
        raw_articles = scrape_all_sources()
        refresh_status["articles_scraped"] = len(raw_articles)
        
        # 2. Cluster
        def update_status(msg):
            refresh_status["message"] = msg
        
        clustered_events = cluster_and_summarize_articles(raw_articles, status_callback=update_status)
        refresh_status["clusters_created"] = len(clustered_events)
        refresh_status["message"] = "Finalizing database updates..."
        
        if not clustered_events:
             refresh_status["status"] = "idle"
             refresh_status["message"] = "Scrape finished, but no events found."
             return

        # 3. Atomic Save: Use a single transaction for everything
        # This prevents the "empty site" window
        db.query(Article).delete()
        db.query(Cluster).delete()
        
        # Ensure sources exist
        for name, meta in SOURCES.items():
            if not db.query(Source).filter(Source.name == name).first():
                db.add(Source(
                    name=name, location=meta["location"], 
                    political_orientation=meta["orientation"], 
                    known_bias=meta["bias"], base_url=meta["url"]
                ))
        db.flush() # Ensure sources are available for lookups
        
        for event in clustered_events:
            # Map category to allowed set or default to General News
            cat = event.get("category", "General News")
            if cat not in ["General News", "Economics", "Culture", "Technology", "Geopolitics"]:
                cat = "General News"

            db_cluster = Cluster(
                average_title_en=event.get("average_title_en", ""),
                average_title_he=event.get("average_title_he", ""),
                comparative_summary_en=event.get("comparative_summary_en", ""),
                comparative_summary_he=event.get("comparative_summary_he", ""),
                category=cat
            )
            db.add(db_cluster)
            db.flush()
            
            for art in event.get("articles", []):
                source_rec = db.query(Source).filter(Source.name == art["source"]).first()
                if source_rec:
                    # Fix: Convert ISO string back to datetime object if needed
                    pub_at = art.get("published_at")
                    if isinstance(pub_at, str):
                        try:
                            pub_at = dateutil.parser.parse(pub_at)
                        except:
                            pub_at = None
                    
                    db_article = Article(
                        original_title=art["title"],
                        title_en=art.get("title_en", ""),
                        title_he=art.get("title_he", ""),
                        original_url=art["url"],
                        published_at=pub_at,
                        bias_warning_en=art.get("bias_warning_en", ""),
                        bias_warning_he=art.get("bias_warning_he", ""),
                        source_id=source_rec.id,
                        cluster_id=db_cluster.id
                    )
                    db.add(db_article)
        db.commit()
        
        refresh_status["status"] = "idle"
        refresh_status["message"] = "Success"
        refresh_status["last_refresh"] = datetime.now().isoformat()
        
    except Exception as e:
        db.rollback()
        print(f"Background refresh error: {e}")
        refresh_status["status"] = "idle"
        refresh_status["message"] = f"Error: {str(e)}"
    finally:
        db.close()

@app.post("/api/refresh")
def refresh_feed(background_tasks: BackgroundTasks):
    global refresh_status
    if refresh_status["status"] == "processing":
        return {"status": "processing", "message": "A refresh is already underway."}
    
    background_tasks.add_task(run_refresh_logic)
    
    refresh_status["status"] = "processing"
    refresh_status["message"] = "Refresh started in background."
    
    return {"status": "processing", "message": "Refresh started."}


