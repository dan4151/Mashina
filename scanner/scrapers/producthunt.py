"""Product Hunt scraper - fetches trending AI/tech products for affiliate opportunities."""

import requests
from bs4 import BeautifulSoup
import feedparser
import time

HEADERS = {
    "User-Agent": "TrendScanner/1.0 (AI Content Research)"
}


def scrape_producthunt():
    """
    Scrape Product Hunt for new AI tools and products.
    Returns list of dicts with: keyword, title, description, popularity_score, raw_data
    """
    trends = []

    # Use the RSS feed - no API key needed
    try:
        print("[Product Hunt] Fetching RSS feed...")
        feed = feedparser.parse("https://www.producthunt.com/feed")

        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            description = entry.get("summary", "")
            link = entry.get("link", "")

            # Filter for AI/tech related products
            ai_keywords = [
                "ai", "gpt", "llm", "machine learning", "automation",
                "chatbot", "copilot", "generative", "neural", "model",
                "agent", "assistant", "artificial intelligence",
            ]
            text_lower = f"{title} {description}".lower()
            is_ai_related = any(kw in text_lower for kw in ai_keywords)

            if is_ai_related:
                trends.append({
                    "keyword": title[:200],
                    "title": title,
                    "description": description[:500],
                    "url": link,
                    "popularity_score": 70,  # Default for PH - these are curated
                    "region": "global",
                    "language": "en",
                    "raw_data": {
                        "type": "producthunt",
                        "published": entry.get("published", ""),
                    },
                })

    except Exception as e:
        print(f"[Product Hunt] Error: {e}")

    print(f"[Product Hunt] Found {len(trends)} AI-related products")
    return trends
