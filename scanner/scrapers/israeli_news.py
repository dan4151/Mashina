"""Israeli tech news scraper - fetches from Geektime, Calcalist Tech, etc."""

import feedparser
import time

# Israeli tech news RSS feeds
FEEDS = [
    {"name": "Geektime", "url": "https://www.geektime.co.il/feed/", "language": "he"},
    {"name": "Calcalist Tech", "url": "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml", "language": "he"},
    {"name": "Globes Tech", "url": "https://www.globes.co.il/webservice/rss/rssfeeder.asmx/FeederC?iID=585", "language": "he"},
]

AI_KEYWORDS_HE = [
    "בינה מלאכותית", "AI", "למידת מכונה", "צ'אט", "GPT", "רובוט",
    "אוטומציה", "סטארטאפ", "טכנולוגיה", "מודל שפה", "דיפ לרנינג",
]

AI_KEYWORDS_EN = [
    "ai", "artificial intelligence", "machine learning", "gpt", "llm",
    "startup", "automation", "robot", "deep learning", "neural",
]


def scrape_israeli_news():
    """
    Scrape Israeli tech news sites for AI/tech stories.
    Returns list of dicts with: keyword, title, description, popularity_score, raw_data
    """
    trends = []

    for feed_info in FEEDS:
        try:
            print(f"[Israeli News] Fetching {feed_info['name']}...")
            feed = feedparser.parse(feed_info["url"])

            for entry in feed.entries[:15]:
                title = entry.get("title", "")
                description = entry.get("summary", "")
                link = entry.get("link", "")
                text_lower = f"{title} {description}".lower()

                # Check if AI/tech related
                keywords = AI_KEYWORDS_HE + AI_KEYWORDS_EN
                is_relevant = any(kw.lower() in text_lower for kw in keywords)

                if is_relevant:
                    trends.append({
                        "keyword": title[:200],
                        "title": title,
                        "description": description[:500],
                        "url": link,
                        "popularity_score": 60,
                        "region": "IL",
                        "language": feed_info["language"],
                        "raw_data": {
                            "source_name": feed_info["name"],
                            "type": "israeli_news",
                            "published": entry.get("published", ""),
                        },
                    })

            time.sleep(1)

        except Exception as e:
            print(f"[Israeli News] Error with {feed_info['name']}: {e}")
            continue

    print(f"[Israeli News] Found {len(trends)} AI-related articles")
    return trends
