"""
Trend Scanner - Main Entry Point
Runs scrapers on a schedule, feeds results through the LLM analyzer, and stores scored trends.
"""

import os
import time
import schedule
from datetime import datetime

from scrapers.google_trends import scrape_google_trends
from scrapers.reddit import scrape_reddit
from scrapers.tiktok import scrape_tiktok
from scrapers.israeli_news import scrape_israeli_news
from agent.analyzer import analyze_batch
from db.models import insert_raw_trend, insert_scored_trend, get_unscored_trends

SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL_MINUTES", 30))


def run_scrapers():
    """Run all scrapers and insert raw trends into the database."""
    print(f"\n{'='*60}")
    print(f"[Scanner] Starting scan at {datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    # Each tuple is (source_name_for_db, scraper_function)
    # source_name is stored in raw_trends.source — keep it short and consistent
    scrapers = [
        ("google_trends", scrape_google_trends),
        ("reddit",        scrape_reddit),
        ("tiktok",        scrape_tiktok),
        ("israeli_news",  scrape_israeli_news),
    ]

    # Collect (source_name, trend_dict) pairs from all scrapers
    all_trends = []
    for source_name, scraper_fn in scrapers:
        try:
            print(f"\n[Scanner] Running {source_name}...")
            trends = scraper_fn()
            for t in trends:
                all_trends.append((source_name, t))
        except Exception as e:
            print(f"[Scanner] Error in {source_name}: {e}")

    # Insert raw trends into DB
    # insert_raw_trend() handles deduplication — returns None for duplicates
    inserted = 0
    for source_name, trend in all_trends:
        trend_id = insert_raw_trend(
            source=source_name,
            keyword=trend["keyword"],
            title=trend.get("title"),
            description=trend.get("description"),
            url=trend.get("url"),
            region=trend.get("region", "IL"),
            language=trend.get("language", "he"),
            popularity_score=trend.get("popularity_score", 0),
            raw_data=trend.get("raw_data"),
        )
        if trend_id:
            inserted += 1

    print(f"\n[Scanner] Inserted {inserted} new trends (skipped {len(all_trends) - inserted} duplicates)")
    return inserted


def run_analyzer():
    """Fetch unscored trends and run them through the LLM agent."""
    print(f"\n[Analyzer] Fetching unscored trends...")
    unscored = get_unscored_trends(limit=20)

    if not unscored:
        print("[Analyzer] No new trends to analyze")
        return

    print(f"[Analyzer] Analyzing {len(unscored)} trends...")
    results = analyze_batch(unscored)

    # Store scored trends
    stored = 0
    for result in results:
        scores = {
            "niche_relevance": result.get("niche_relevance", 0),
            "monetization_score": result.get("monetization_score", 0),
            "urgency_score": result.get("urgency_score", 0),
            "competition_score": result.get("competition_score", 0),
            "hebrew_gap": result.get("hebrew_gap", 0),
        }

        scored_id = insert_scored_trend(
            raw_trend_id=result.get("_raw_trend_id"),
            topic=result.get("topic", ""),
            summary=result.get("summary", ""),
            scores=scores,
            suggested_format=result.get("suggested_format", "short_video"),
            suggested_angle=result.get("suggested_angle", ""),
            affiliate_opportunities=result.get("affiliate_opportunities", ""),
            content_language=result.get("content_language", "he"),
        )
        if scored_id:
            stored += 1

    print(f"[Analyzer] Stored {stored} scored trends")

    # Show top opportunities
    print(f"\n{'='*60}")
    print("[Analyzer] TOP OPPORTUNITIES:")
    print(f"{'='*60}")
    top = sorted(results, key=lambda x: (
        x.get("monetization_score", 0) * 0.3 +
        x.get("hebrew_gap", 0) * 0.25 +
        x.get("niche_relevance", 0) * 0.15 +
        x.get("competition_score", 0) * 0.15 +
        x.get("urgency_score", 0) * 0.15
    ), reverse=True)[:5]

    for i, t in enumerate(top, 1):
        print(f"\n#{i}: {t.get('topic', 'N/A')}")
        print(f"    Summary: {t.get('summary', '')[:100]}")
        print(f"    Format: {t.get('suggested_format', 'N/A')}")
        print(f"    Angle: {t.get('suggested_angle', '')[:100]}")
        print(f"    Affiliate: {t.get('affiliate_opportunities', 'none')[:100]}")
        print(f"    Scores: relevance={t.get('niche_relevance')}, "
              f"money={t.get('monetization_score')}, "
              f"urgency={t.get('urgency_score')}, "
              f"competition={t.get('competition_score')}, "
              f"hebrew_gap={t.get('hebrew_gap')}")


def full_scan():
    """Complete scan cycle: scrape → analyze → score."""
    try:
        run_scrapers()
        run_analyzer()
        print(f"\n[Scanner] Next scan in {SCAN_INTERVAL} minutes...")
    except Exception as e:
        print(f"[Scanner] Error in scan cycle: {e}")


def main():
    print(f"""
    ╔══════════════════════════════════════════╗
    ║       TREND SCANNER v1.0                ║
    ║       Scanning for opportunities...     ║
    ║       Interval: {SCAN_INTERVAL} minutes             ║
    ╚══════════════════════════════════════════╝
    """)

    # Wait a few seconds for DB to be fully ready
    print("[Scanner] Waiting for services to initialize...")
    time.sleep(5)

    # Run immediately on startup
    full_scan()

    # Schedule recurring scans
    schedule.every(SCAN_INTERVAL).minutes.do(full_scan)

    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    main()
