"""
Israeli news scraper - fetches articles from major Israeli news and entertainment sites.

No topic filter — we grab everything that's published, because we want to know
what Israelis are reading about right now, not just tech/AI.
The LLM analyzer decides what's worth creating content about.
"""

import feedparser
import time

# Major Israeli news sources with RSS feeds
# Covers news, tech, entertainment, and lifestyle — all in Hebrew
FEEDS = [
    # General news / most-read Israeli portals
    {"name": "Ynet",          "url": "https://www.ynet.co.il/Integration/StoryRss2.xml",                                   "language": "he"},
    {"name": "Walla News",    "url": "https://rss.walla.co.il/feed/1",                                                     "language": "he"},

    # Tech & startup focused
    {"name": "Geektime",      "url": "https://www.geektime.co.il/feed/",                                                   "language": "he"},
    {"name": "Calcalist Tech","url": "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml",                         "language": "he"},
    {"name": "Globes Tech",   "url": "https://www.globes.co.il/webservice/rss/rssfeeder.asmx/FeederC?iID=585",             "language": "he"},
]


def scrape_israeli_news():
    """
    Scrape Israeli news RSS feeds for any trending stories.
    No keyword filter — all articles pass through to the LLM for scoring.
    Returns list of dicts with: keyword, title, description, popularity_score, raw_data
    """
    trends = []

    for feed_info in FEEDS:
        try:
            print(f"[Israeli News] Fetching {feed_info['name']}...")
            feed = feedparser.parse(feed_info["url"])

            if not feed.entries:
                print(f"[Israeli News] No entries from {feed_info['name']} — feed may be unavailable")
                time.sleep(1)
                continue

            # Take the latest 15 articles from each source
            for entry in feed.entries[:15]:
                title = entry.get("title", "").strip()
                description = entry.get("summary", "").strip()
                link = entry.get("link", "")

                if not title:
                    continue  # Skip entries with no title

                trends.append({
                    "keyword": title[:200],
                    "title": title,
                    "description": description[:500],
                    "url": link,
                    "popularity_score": 60,  # Fixed value — news RSS has no engagement metric
                    "region": "IL",
                    "language": feed_info["language"],
                    "raw_data": {
                        "source_name": feed_info["name"],
                        "type": "israeli_news",
                        "published": entry.get("published", ""),
                    },
                })

            time.sleep(1)  # Small delay between feeds

        except Exception as e:
            print(f"[Israeli News] Error with {feed_info['name']}: {e}")
            continue

    print(f"[Israeli News] Found {len(trends)} articles")
    return trends
