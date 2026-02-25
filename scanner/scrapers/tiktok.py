"""
TikTok trends scraper - fetches trending hashtags in Israel via TikTok Creative Center.

TikTok doesn't have a public API, but their Creative Center
(ads.tiktok.com/business/creativecenter) exposes trend data
that can be queried without authentication.

If the API call fails (TikTok may add auth requirements in the future),
this scraper returns an empty list and logs a message — it never crashes
the rest of the pipeline.
"""

import requests
import time

# TikTok Creative Center trending hashtags API
# This is the same endpoint the Creative Center web app uses
TIKTOK_API_URL = "https://ads.tiktok.com/creative_radar_api/v1/popular_trend/hashtag/list"

HEADERS = {
    # Mimic a real browser so TikTok doesn't reject the request
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://ads.tiktok.com/business/creativecenter/trend-calendar/homepage/pc/en",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
}


def scrape_tiktok():
    """
    Fetch trending TikTok hashtags for Israel from TikTok's Creative Center.
    Returns list of dicts with: keyword, title, description, popularity_score, raw_data
    """
    trends = []

    try:
        print("[TikTok] Fetching trending hashtags for Israel...")

        params = {
            "period": "7",        # Last 7 days of trend data
            "page": "1",
            "limit": "20",        # Top 20 trending hashtags
            "country_code": "IL", # Israel
        }

        resp = requests.get(
            TIKTOK_API_URL,
            params=params,
            headers=HEADERS,
            timeout=15,
        )

        if resp.status_code != 200:
            # TikTok may require auth or block the request — fail silently
            print(f"[TikTok] API returned status {resp.status_code}. "
                  f"Creative Center access may require authentication.")
            return []

        data = resp.json()

        # The response structure can vary — try common field names
        hashtag_list = (
            data.get("data", {}).get("list", [])
            or data.get("data", {}).get("hashtag_list", [])
            or []
        )

        if not hashtag_list:
            print("[TikTok] No hashtag data in response — API structure may have changed.")
            return []

        for rank, item in enumerate(hashtag_list):
            # Different API versions use different field names
            tag_name = (
                item.get("hashtag_name")
                or item.get("name")
                or item.get("tag_name")
                or ""
            )
            if not tag_name:
                continue

            # Remove leading # if present
            keyword = tag_name.lstrip("#").strip()

            trends.append({
                "keyword": keyword[:200],
                "title": f"#{keyword}",
                "description": f"Trending TikTok hashtag in Israel (rank #{rank + 1} this week)",
                "url": f"https://www.tiktok.com/tag/{keyword}",
                "popularity_score": max(10, 100 - (rank * 5)),  # Rank 1 = 100, Rank 2 = 95, etc.
                "region": "IL",
                "language": "he",
                "raw_data": {
                    "type": "tiktok_hashtag",
                    "rank": rank + 1,
                    "publish_cnt": item.get("publish_cnt", 0),   # Number of videos with this tag
                    "video_views": item.get("video_views", 0),   # Total views
                },
            })

    except Exception as e:
        print(f"[TikTok] Error: {e}")
        return []

    print(f"[TikTok] Found {len(trends)} trending hashtags")
    return trends
