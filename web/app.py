"""
Trend Scanner Web Dashboard
A simple Flask app to browse the MySQL tables without writing SQL.
Runs on port 5000 — open http://localhost:5000 in your browser.
"""

import os
from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)


def get_db():
    """Open a fresh DB connection. Uses the same env vars as the scanner."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "mysql"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "trendscanner123"),
        database=os.getenv("DB_NAME", "trends"),
    )


@app.route("/")
def index():
    """
    Main dashboard — loads all data for both tabs in one request.
    Client-side JavaScript handles filtering/search so the page never reloads.
    """
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # --- Stats ---
        cursor.execute("SELECT COUNT(*) as n FROM raw_trends")
        raw_count = cursor.fetchone()["n"]

        cursor.execute("SELECT COUNT(*) as n FROM scored_trends")
        scored_count = cursor.fetchone()["n"]

        cursor.execute("SELECT COUNT(*) as n FROM processed_keywords")
        keywords_count = cursor.fetchone()["n"]

        # Count by source (for the stat cards)
        cursor.execute(
            "SELECT source, COUNT(*) as count FROM raw_trends GROUP BY source ORDER BY count DESC"
        )
        by_source = cursor.fetchall()

        # Count by status (for the stat cards)
        cursor.execute(
            "SELECT status, COUNT(*) as count FROM scored_trends GROUP BY status"
        )
        by_status = cursor.fetchall()

        # --- Scored trends (Top Opportunities tab) ---
        # Join with raw_trends to get the source name and original URL
        cursor.execute("""
            SELECT
                s.id, s.topic, s.summary,
                s.overall_score,
                s.niche_relevance, s.monetization_score,
                s.urgency_score, s.competition_score, s.hebrew_gap,
                s.suggested_format, s.suggested_angle,
                s.affiliate_opportunities, s.content_language,
                s.status, s.analyzed_at,
                r.source, r.url AS raw_url
            FROM scored_trends s
            JOIN raw_trends r ON s.raw_trend_id = r.id
            ORDER BY s.overall_score DESC
            LIMIT 200
        """)
        scored_trends = cursor.fetchall()

        # --- Raw trends (Raw Trends tab) ---
        cursor.execute("""
            SELECT id, source, title, keyword, region, language,
                   popularity_score, url, scraped_at
            FROM raw_trends
            ORDER BY scraped_at DESC
            LIMIT 200
        """)
        raw_trends = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "index.html",
            raw_count=raw_count,
            scored_count=scored_count,
            keywords_count=keywords_count,
            by_source=by_source,
            by_status=by_status,
            scored_trends=scored_trends,
            raw_trends=raw_trends,
        )

    except mysql.connector.Error as e:
        # Show a friendly error if the DB isn't ready yet
        return render_template("error.html", error=str(e)), 500


if __name__ == "__main__":
    # debug=False in production; set to True locally if you want auto-reload
    app.run(host="0.0.0.0", port=5000, debug=False)
