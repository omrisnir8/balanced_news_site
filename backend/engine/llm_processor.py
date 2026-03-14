import os
import json
from typing import List, Dict, Any
from groq import Groq

# Ensure GROQ_API_KEY is set in the environment
client = Groq(api_key=os.environ.get("GROQ_API_KEY", "dummy_key_for_testing"))

def cluster_and_summarize_articles(articles: List[Dict]) -> List[Dict]:
    """
    Takes a list of English/Translated articles, identifies similar events,
    and returns clustered events with an average title and comparative summary.
    """
    if not articles:
        return []
        
    # In a full system, we might use embeddings (e.g., SentenceTransformers) to pre-cluster.
    # For this implementation, we feed a batch to the LLM and ask it to cluster.
    
    articles_json = json.dumps([{
        "id": i,
        "title": a.get("title"),
        "source": a.get("source"),
        "time": a.get("published_at").strftime("%H:%M") if a.get("published_at") else "Unknown"
    } for i, a in enumerate(articles)], ensure_ascii=False)
    
    prompt = f"""
Input Articles JSON: {articles_json}

Task: You are an advanced multilingual news aggregation engine. 
Action: Analyze the list of headlines and snippets below. 
1. Cluster articles by EXACT underlying event (e.g. if an Israeli source in Hebrew and a UK source in English both report on the exact same missile strike, merge them).
2. It is CRITICALLY IMPORTANT to be granular. You MUST output many distinct clusters (usually 10 to 20 different clusters based on the different events in the input). 
3. NEVER group all articles into 1 or 2 mega-clusters. An event is small and specific (e.g. "IDF strikes target in Damascus", NOT generally "Middle East Conflict").
Output ONLY a JSON object with a single key `clusters` containing an array of objects.
Each object must have:
"average_title_en": (String) Factual neutral English title
"average_title_he": (String) Factual neutral Hebrew title
"comparative_summary_en": (String) 2-3 sentence English summary explaining core facts and highlighting how different sources framed the event.
"comparative_summary_he": (String) Same summary translated into natural Hebrew.
"category": EXACTLY one of: "General News", "Economics", "Culture", "Technology", "Geopolitics".
"articles": An array of objects representing the articles in this cluster. For EACH article, include:
   - "article_id": The exact integer ID from the input JSON.
   - "title_en": (String) The article's title translated to English (if originally Hebrew) or identical (if originally English).
   - "title_he": (String) The article's title translated to Hebrew (if originally English) or identical (if originally Hebrew).
   - "bias_warning_en": (String) A one-line bias/framing warning in English based on the publisher and title.
   - "bias_warning_he": (String) A one-line bias/framing warning in Hebrew.

Return ONLY the JSON. No markdown blocks.
"""

    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a neutral news aggregation JSON API. You always output valid JSON objects."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=4000,
        )
        response_text = completion.choices[0].message.content.strip()
        
        parsed_data = json.loads(response_text)
        clusters = parsed_data.get("clusters", [])
        
        # Rehydrate clusters with full article objects and bias warnings
        hydrated_clusters = []
        for cluster in clusters:
             matched_articles = []
             for article_data in cluster.get("articles", []):
                 idx = article_data.get("article_id")
                 if isinstance(idx, int) and idx < len(articles):
                     article_obj = dict(articles[idx]) # copy
                     article_obj["title_en"] = article_data.get("title_en", "")
                     article_obj["title_he"] = article_data.get("title_he", "")
                     article_obj["bias_warning_en"] = article_data.get("bias_warning_en", "")
                     article_obj["bias_warning_he"] = article_data.get("bias_warning_he", "")
                     matched_articles.append(article_obj)
                     
             if matched_articles: # Only keep non-empty clusters
                 hydrated_clusters.append({
                     "average_title_en": cluster.get("average_title_en"),
                     "average_title_he": cluster.get("average_title_he"),
                     "comparative_summary_en": cluster.get("comparative_summary_en"),
                     "comparative_summary_he": cluster.get("comparative_summary_he"),
                     "articles": matched_articles,
                     "category": cluster.get("category", "General News")
                 })
                 
        return hydrated_clusters

        
    except Exception as e:
        print(f"Clustering error: {e}")
        # Fallback for dev/missing keys: Create fake clusters across categories
        return [
            {
                "average_title_en": "Mock Economics Event (Rate Limit Hit)",
                "average_title_he": "אירוע זיוף (מגבלת קצב)",
                "comparative_summary_en": "This is a mock summary because the Groq API rate limit was hit. Please wait 1 minute.",
                "comparative_summary_he": "זהו תקציר זיוף עקב הגבלת קצב",
                "category": "Economics",
                "articles": articles[:min(2, len(articles))] # Grab first 2
            },
            {
                "average_title_en": "Mock General News (Rate Limit Hit)",
                "average_title_he": "אירוע זיוף (מגבלת קצב)",
                "comparative_summary_en": "This is a mock summary because the Groq API rate limit was hit. Please wait 1 minute.",
                "comparative_summary_he": "זהו תקציר זיוף עקב הגבלת קצב",
                "category": "General News",
                "articles": articles[min(2, len(articles)):min(4, len(articles))]
            }
        ]
