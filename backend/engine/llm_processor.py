import os
import json
import random
from typing import List, Dict, Any
from groq import Groq
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Initialize a pool of clients from environment variables
API_KEYS = []
# Check for GROQ_API_KEY, GROQ_API_KEY_2, GROQ_API_KEY_3, etc.
env_names = ["GROQ_API_KEY"] + [f"GROQ_API_KEY_{i}" for i in range(2, 11)]

for name in env_names:
    key = os.environ.get(name)
    if key and key.startswith("gsk_"):
        API_KEYS.append(key)

# Deduplicate
API_KEYS = list(dict.fromkeys(API_KEYS))

# Create a pool of Groq clients
CLIENTS = [Groq(api_key=key) for key in API_KEYS]
if not CLIENTS:
    # Final fallback if absolutely nothing is set
    fallback_key = os.environ.get("GROQ_API_KEY", "dummy_key")
    CLIENTS = [Groq(api_key=fallback_key)]

print(f"DEBUG: Initialized AI Engine with {len(CLIENTS)} active API keys.")

def get_random_client():
    return random.choice(CLIENTS)

def get_cluster_groups(articles: List[Dict]) -> List[List[int]]:
    """Step 1: Fast ID-only Pre-Clustering to reduce payload."""
    articles_json = json.dumps([{
        "id": i,
        "title": a.get("title"),
        "source": a.get("source"),
    } for i, a in enumerate(articles)], ensure_ascii=False)
    
    prompt = f"""
Input Articles JSON: {articles_json}

Task: Group similar articles into cohesive events.
Action: Output ONLY a JSON array of arrays, where each inner array contains the integer IDs of articles reporting on the exact same underlying event (e.g. merge Israeli/Global sources on the same strike).
Rules:
1. Be granular. Separate highly diverse topics.
2. Every article ID from the input MUST appear exactly once in the output.
3. No descriptions, just arrays of IDs.
Example Output Format: [[0, 2], [1], [3, 4, 5]]
"""
    try:
        client = get_random_client()
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": 'You are a grouping agent. You MUST output a JSON object with a "groups" key containing arrays of article IDs.'},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500,
        )
        resp_content = completion.choices[0].message.content.strip()
        parsed = json.loads(resp_content)
        return parsed.get("groups", [[i] for i in range(len(articles))])
    except Exception as e:
        print(f"Grouping error: {e}")
        return [[i] for i in range(len(articles))]

def process_single_cluster(group_ids: List[int], articles: List[Dict], client_idx: int = 0) -> Dict:
    """Step 2: High-Quality Summarization and Formatting for ONE event cluster."""
    group_articles = [articles[i] for i in group_ids if i < len(articles)]
    if not group_articles: return None
    
    # Select client based on index to distribute load evenly in parallel threads
    client = CLIENTS[client_idx % len(CLIENTS)]
    
    articles_payload = json.dumps([{
        "id": i,
        "title": a.get("title"),
        "source": a.get("source"),
        "time": a.get("published_at").strftime("%H:%M") if a.get("published_at") else "Unknown",
        "snippet": a.get("summary")[:200] if a.get("summary") else ""
    } for i, a in zip(group_ids, group_articles)], ensure_ascii=False)

    prompt = f"""
Event Input JSON (Articles covering the same event): {articles_payload}

Task: Analyze these articles and synthesize a single event report.
Output ONLY a JSON object with:
"average_title_en": (String) Factual neutral English title
"average_title_he": (String) Factual neutral Hebrew title
"comparative_summary_en": (String) 2-3 sentence English summary explaining core facts. Highlight how different sources framed the event if there are discrepancies.
"comparative_summary_he": (String) Same summary translated into natural Hebrew.
"category": EXACTLY one of: "General News", "Economics", "Culture", "Technology", "Geopolitics".
"article_details": Array of objects updating the input articles:
    - "id": Exact ID from input
    - "title_en": Translated to English (if Hebrew) or identical
    - "title_he": Translated to Hebrew (if English) or identical
"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a neutral news synthesis JSON API."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1500,
        )
        parsed = json.loads(completion.choices[0].message.content.strip())
        
        from backend.engine.scraper import SOURCES
        
        hydrated_articles = []
        updates = {item.get("id"): item for item in parsed.get("article_details", [])}
        
        for idx_col, a in zip(group_ids, group_articles):
            art_obj = dict(a)
            update = updates.get(idx_col, {})
            
            art_obj["title_en"] = update.get("title_en", a["title"])
            art_obj["title_he"] = update.get("title_he", a["title"])
            
            source_meta = SOURCES.get(a["source"], {})
            ori = source_meta.get("orientation", "")
            bias = source_meta.get("bias", "")
            
            if ori and bias:
                art_obj["bias_warning_en"] = f"{ori} | {bias}"
                art_obj["bias_warning_he"] = f"{ori} | {bias}"
            else:
                art_obj["bias_warning_en"] = "Unknown orientation"
                art_obj["bias_warning_he"] = "נטייה לא מוגדרת"
            
            # Use provided string ISO or format if still object
            if isinstance(a.get("published_at"), datetime):
                art_obj["published_at"] = a["published_at"].isoformat()
            
            hydrated_articles.append(art_obj)
            
        return {
            "average_title_en": parsed.get("average_title_en", "Unknown Event"),
            "average_title_he": parsed.get("average_title_he", "אירוע לא ידוע"),
            "comparative_summary_en": parsed.get("comparative_summary_en", "No summary available."),
            "comparative_summary_he": parsed.get("comparative_summary_he", "ללא תקציר"),
            "category": parsed.get("category", "General News"),
            "articles": hydrated_articles
        }

    except Exception as e:
        print(f"Summarization error: {e}")
        return None

def cluster_and_summarize_articles(articles: List[Dict], status_callback=None) -> List[Dict]:
    """Master pipeline: Groups statically, then processes in parallel using multi-keys."""
    if not articles: return []
    
    if status_callback: status_callback("AI is grouping 50+ articles into events...")
    groups = get_cluster_groups(articles)
    
    total_groups = len([g for g in groups if g])
    if status_callback: status_callback(f"Found {total_groups} events. AI is summarizing each using {len(CLIENTS)} keys...")
    
    final_clusters = []
    completed_count = 0
    
    with ThreadPoolExecutor(max_workers=min(len(groups), len(CLIENTS) * 2)) as executor:
        futures = [executor.submit(process_single_cluster, grp, articles, i) for i, grp in enumerate(groups) if grp]
        
        for future in as_completed(futures):
            res = future.result()
            completed_count += 1
            if status_callback: 
                status_callback(f"AI Summarized {completed_count}/{total_groups} events...")
            if res:
                final_clusters.append(res)
                
    return final_clusters


