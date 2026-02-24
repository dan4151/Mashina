"""Reddit scraper - fetches rising/hot posts from AI and tech subreddits."""

import requests
import time

# No API key needed - using public JSON endpoints
SUBREDDITS = [
    "artificial",
    "ChatGPT",
    "LocalLLaMA",
    "MachineLearning",
    "singularity",
    "StableDiffusion",
    "Israel",  # Local context
]

HEADERS = {
    "User-Agent": "TrendScanner/1.0 (AI Content Research)"
}


def scrape_reddit():
    """
    Scrape Reddit for trending AI/tech posts.
    Returns list of dicts with: keyword, title, description, popularity_score, raw_data
    """
    trends = []

    for subreddit in SUBREDDITS:
        try:
            # Fetch rising posts (these are gaining traction fast)
            url = f"https://www.reddit.com/r/{subreddit}/rising.json?limit=10"
            resp = requests.get(url, headers=HEADERS, timeout=15)

            if resp.status_code == 200:
                data = resp.json()
                posts = data.get("data", {}).get("children", [])

                for post in posts:
                    p = post["data"]
                    score = p.get("score", 0)
                    title = p.get("title", "")
                    
                    trends.append({
                        "keyword": title[:200],
                        "title": title,
                        "description": (p.get("selftext", "") or "")[:500],
                        "url": f"https://reddit.com{p.get('permalink', '')}",
                        "popularity_score": min(score, 100),
                        "region": "global",
                        "language": "en",
                        "raw_data": {
                            "subreddit": subreddit,
                            "score": score,
                            "num_comments": p.get("num_comments", 0),
                            "upvote_ratio": p.get("upvote_ratio", 0),
                            "type": "rising",
                        },
                    })

            time.sleep(2)  # Reddit rate limits

            # Also fetch hot posts
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=5"
            resp = requests.get(url, headers=HEADERS, timeout=15)

            if resp.status_code == 200:
                data = resp.json()
                posts = data.get("data", {}).get("children", [])

                for post in posts:
                    p = post["data"]
                    if p.get("stickied"):
                        continue
                    score = p.get("score", 0)
                    title = p.get("title", "")

                    trends.append({
                        "keyword": title[:200],
                        "title": title,
                        "description": (p.get("selftext", "") or "")[:500],
                        "url": f"https://reddit.com{p.get('permalink', '')}",
                        "popularity_score": min(score, 100),
                        "region": "global",
                        "language": "en",
                        "raw_data": {
                            "subreddit": subreddit,
                            "score": score,
                            "num_comments": p.get("num_comments", 0),
                            "upvote_ratio": p.get("upvote_ratio", 0),
                            "type": "hot",
                        },
                    })

            time.sleep(2)

        except Exception as e:
            print(f"[Reddit] Error scraping r/{subreddit}: {e}")
            continue

    print(f"[Reddit] Found {len(trends)} trends")
    return trends
