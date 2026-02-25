"""Google Trends scraper - fetches ALL trending searches in Israel (any topic)."""

from pytrends.request import TrendReq
import time


def scrape_google_trends():
    """
    Scrape Google Trends for Israel — returns whatever Israelis are searching for right now.
    No topic filter — we want everything that's trending, not just AI.
    """
    trends = []
    pytrends = TrendReq(hl='he-IL', tz=120)  # Israel timezone UTC+2

    try:
        # 1. Real-time trending searches in Israel (top 20)
        # These are the hottest searches happening right now — any topic
        print("[Google Trends] Fetching trending searches for Israel...")
        trending = pytrends.trending_searches(pn='israel')

        for idx, row in trending.iterrows():
            keyword = row[0]
            trends.append({
                "keyword": keyword,
                "title": keyword,
                "description": f"Trending search #{idx + 1} in Israel right now",
                "url": f"https://trends.google.com/trends/explore?geo=IL&q={keyword}",
                "popularity_score": max(100 - idx * 5, 10),  # #1 = 100, #2 = 95, etc.
                "region": "IL",
                "language": "he",
                "raw_data": {"rank": idx + 1, "type": "trending_search"},
            })

        time.sleep(2)

        # 2. Rising queries for broad Israeli interest topics
        # These seeds cover major content categories — not just tech
        broad_seeds = [
            "ישראל",        # "Israel" — catches current events
            "טיקטוק",       # "TikTok" — what's trending on TikTok itself
            "אינסטגרם",     # "Instagram"
            "ויראלי",       # "Viral"
        ]

        for seed in broad_seeds:
            try:
                pytrends.build_payload([seed], geo='IL', timeframe='now 7-d')
                related = pytrends.related_queries()

                if seed in related and related[seed]['rising'] is not None:
                    rising = related[seed]['rising']
                    for _, row in rising.head(8).iterrows():
                        trends.append({
                            "keyword": row['query'],
                            "title": row['query'],
                            "description": f"Rising search in Israel related to '{seed}'",
                            "url": f"https://trends.google.com/trends/explore?geo=IL&q={row['query']}",
                            "popularity_score": min(int(row.get('value', 50)), 100),
                            "region": "IL",
                            "language": "he",
                            "raw_data": {
                                "seed": seed,
                                "type": "rising_related",
                                "value": str(row.get('value', '')),
                            },
                        })

                time.sleep(2)  # Be polite to Google

            except Exception as e:
                print(f"[Google Trends] Error with seed '{seed}': {e}")
                continue

    except Exception as e:
        print(f"[Google Trends] Error: {e}")
        return []

    print(f"[Google Trends] Found {len(trends)} trends")
    return trends
