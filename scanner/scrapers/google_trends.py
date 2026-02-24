"""Google Trends scraper - fetches trending searches in Israel."""

from pytrends.request import TrendReq
import time

def scrape_google_trends():
    """
    Scrape Google Trends for Israel.
    Returns list of dicts with: keyword, title, description, popularity_score, raw_data
    """
    trends = []
    pytrends = TrendReq(hl='he-IL', tz=120)  # Israel timezone UTC+2

    try:
        # 1. Real-time trending searches in Israel
        print("[Google Trends] Fetching trending searches for IL...")
        trending = pytrends.trending_searches(pn='israel')
        for idx, row in trending.iterrows():
            keyword = row[0]
            trends.append({
                "keyword": keyword,
                "title": f"Trending in Israel: {keyword}",
                "description": None,
                "url": f"https://trends.google.com/trends/explore?geo=IL&q={keyword}",
                "popularity_score": max(100 - idx * 5, 10),  # Top = higher score
                "region": "IL",
                "language": "he",
                "raw_data": {"rank": idx + 1, "type": "trending_search"},
            })

        time.sleep(2)  # Be nice to Google

        # 2. Related queries for AI/tech topics in Israel
        tech_seeds = ["AI", "בינה מלאכותית", "ChatGPT", "טכנולוגיה"]
        for seed in tech_seeds:
            try:
                pytrends.build_payload([seed], geo='IL', timeframe='now 7-d')
                related = pytrends.related_queries()

                if seed in related and related[seed]['rising'] is not None:
                    rising = related[seed]['rising']
                    for _, row in rising.head(10).iterrows():
                        trends.append({
                            "keyword": row['query'],
                            "title": f"Rising query for '{seed}': {row['query']}",
                            "description": f"Rising search related to {seed}",
                            "url": f"https://trends.google.com/trends/explore?geo=IL&q={row['query']}",
                            "popularity_score": min(int(row.get('value', 50)), 100),
                            "region": "IL",
                            "language": "he",
                            "raw_data": {"seed": seed, "type": "rising_related", "value": str(row.get('value', ''))},
                        })
                time.sleep(2)
            except Exception as e:
                print(f"[Google Trends] Error with seed '{seed}': {e}")
                continue

    except Exception as e:
        print(f"[Google Trends] Error: {e}")

    print(f"[Google Trends] Found {len(trends)} trends")
    return trends
