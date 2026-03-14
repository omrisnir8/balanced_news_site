from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from database import get_db, init_db
from models import Cluster, Article, Source
from engine.scraper import scrape_all_sources, SOURCES
from engine.llm_processor import cluster_and_summarize_articles

app = FastAPI(title="Balanced News Aggregator API")

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

# Basic scaffolding for API routes
@app.get("/api/feed")
def get_feed(category: str = None, db: Session = Depends(get_db)):
    query = db.query(Cluster).order_by(desc(Cluster.created_at))
    if category:
        query = query.filter(Cluster.category == category)
    
    clusters = query.limit(20).all()
    
    # Simple serialization for now
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

@app.post("/api/refresh")
def refresh_feed(db: Session = Depends(get_db)):
    # 1. Scrape all configured sources
    raw_articles = scrape_all_sources()
    # 2. Pass raw mixed English/Hebrew articles to Multilingual LLM for Event Clustering
    clustered_events = cluster_and_summarize_articles(raw_articles)
    
    # 3. Save results to Database
    # (Clear existing for demonstration purposes, or implement deduplication)
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
    db.commit()
    
    for event in clustered_events:
        db_cluster = Cluster(
            average_title_en=event.get("average_title_en", ""),
            average_title_he=event.get("average_title_he", ""),
            comparative_summary_en=event.get("comparative_summary_en", ""),
            comparative_summary_he=event.get("comparative_summary_he", ""),
            category=event.get("category", "General News")
        )
        db.add(db_cluster)
        db.flush() # Get cluster ID
        
        for art in event.get("articles", []):
            source_rec = db.query(Source).filter(Source.name == art["source"]).first()
            if source_rec:
                db_article = Article(
                    original_title=art["title"],
                    title_en=art.get("title_en", ""),
                    title_he=art.get("title_he", ""),
                    original_url=art["url"],
                    published_at=art.get("published_at"),
                    bias_warning_en=art.get("bias_warning_en", ""),
                    bias_warning_he=art.get("bias_warning_he", ""),
                    source_id=source_rec.id,
                    cluster_id=db_cluster.id
                )
                db.add(db_article)
                
    db.commit()
    return {"status": "success", "message": f"Feed refreshed. Found {len(raw_articles)} articles, created {len(clustered_events)} clusters."}

