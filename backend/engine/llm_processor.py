import os
import json
from typing import List, Dict, Any
from groq import Groq

# Ensure GROQ_API_KEY is set in the environment
client = Groq(api_key=os.environ.get("GROQ_API_KEY", "dummy_key_for_testing"))

from concurrent.futures import ThreadPoolExecutor, as_completed

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
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"} if False else None, # Not strictly json object, we want a pure list or {"groups": [...]}
            messages=[
                {"role": "system", "content": 'You output simple JSON objects containing one key "groups" mapped to an array of ID arrays.'},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000,
        )
        resp = completion.choices[0].message.content.strip()
        # Fallback parsing in case the LLM gives us a raw array instead of {"groups": ...}
        if resp.startswith("["):
             return json.loads(resp)
        else:
             parsed = json.loads(resp)
             return parsed.get("groups", [])
    except Exception as e:
        print(f"Grouping error: {e}")
        # Make a dummy group per article
        return [[i] for i in range(len(articles))]

def process_single_cluster(group_ids: List[int], articles: List[Dict]) -> Dict:
    """Step 2: High-Quality Summarization and Formatting for ONE event cluster."""
    group_articles = [articles[i] for i in group_ids if i < len(articles)]
    if not group_articles: return None
    
    # Build payload containing both header and summary for the heavy model
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
        
        # Hydrate with all original article details + static biases
        from backend.engine.scraper import SOURCES # Lazy import to avoid circular iff needed
        
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
                # For a full scale app, translate these static tags too. Standard fallback is OK for now.
                art_obj["bias_warning_he"] = f"{ori} | {bias}"
            else:
                art_obj["bias_warning_en"] = "Unknown orientation"
                art_obj["bias_warning_he"] = "נטייה לא מוגדרת"
            
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

def cluster_and_summarize_articles(articles: List[Dict]) -> List[Dict]:
    """Master pipeline: Groups statically, then processes in parallel."""
    if not articles: return []
    
    print(f"Step 1: Identifying clusters among {len(articles)} articles...")
    groups = get_cluster_groups(articles)
    
    print(f"Found {len(groups)} distinct events. Step 2: Extracting comparative summaries concurrently...")
    
    final_clusters = []
    import time
    
    # Process sequentially to respect free-tier concurrent connection limits
    for grp in groups:
        if not grp:
            continue
            
        res = process_single_cluster(grp, articles)
        if res:
            final_clusters.append(res)
            
        time.sleep(1.5) # Prevent aggressive multi-request rate limiting
                
    return final_clusters

