"""Reddit scraper - fetches rising/hot posts from Israeli and Hebrew subreddits."""

import requests
import time

# Israeli and Hebrew-focused subreddits
# Goal: find what topics Israelis are discussing right now
SUBREDDITS = [
    "israel",           # Main Israeli subreddit — news, culture, current events
    "IsraelNews",       # Israeli news (English)
    "FIREPLACE_IL",     # Large Hebrew-language Israeli community — memes, trends, pop culture
    "israelipolitics",  # Politics and current events in Israel
    "telaviv",          # Tel Aviv culture, lifestyle, local trends
]

HEADERS = {
    # Reddit requires a User-Agent — identify ourselves clearly
    "User-Agent": "TrendScanner/1.0 (Israeli Market Research)"
}


def scrape_reddit():
    """
    Scrape Israeli Reddit communities for trending posts.
    Returns list of dicts with: keyword, title, description, popularity_score, raw_data
    """
    trends = []

    for subreddit in SUBREDDITS:
        try:
            # Rising posts = gaining traction fast right now
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
                        "region": "IL",
                        "language": "he",  # Israeli subreddits are HE-focused even when posting in EN
                        "raw_data": {
                            "subreddit": subreddit,
                            "score": score,
                            "num_comments": p.get("num_comments", 0),
                            "upvote_ratio": p.get("upvote_ratio", 0),
                            "type": "rising",
                        },
                    })

            time.sleep(2)  # Reddit rate limits — be respectful

            # Hot posts = currently most popular
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=5"
            resp = requests.get(url, headers=HEADERS, timeout=15)

            if resp.status_code == 200:
                data = resp.json()
                posts = data.get("data", {}).get("children", [])

                for post in posts:
                    p = post["data"]
                    if p.get("stickied"):
                        continue  # Skip pinned mod posts
                    score = p.get("score", 0)
                    title = p.get("title", "")

                    trends.append({
                        "keyword": title[:200],
                        "title": title,
                        "description": (p.get("selftext", "") or "")[:500],
                        "url": f"https://reddit.com{p.get('permalink', '')}",
                        "popularity_score": min(score, 100),
                        "region": "IL",
                        "language": "he",
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

    print(f"[Reddit] Found {len(trends)} trends from Israeli subreddits")
    return trends
