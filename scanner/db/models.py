import os
import hashlib
import mysql.connector
from mysql.connector import pooling

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "trendscanner123"),
    "database": os.getenv("DB_NAME", "trends"),
}

pool = pooling.MySQLConnectionPool(pool_name="scanner_pool", pool_size=5, **db_config)


def get_connection():
    return pool.get_connection()


def insert_raw_trend(source, keyword, title=None, description=None, url=None,
                     region="IL", language="he", popularity_score=0, raw_data=None):
    """Insert a raw trend and return its ID. Skips if keyword was seen in last 6 hours."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        keyword_hash = hashlib.sha256(f"{source}:{keyword}".encode()).hexdigest()

        # Check if we already processed this recently
        cursor.execute(
            "SELECT id FROM processed_keywords WHERE keyword_hash = %s AND last_seen > NOW() - INTERVAL 6 HOUR",
            (keyword_hash,)
        )
        if cursor.fetchone():
            return None  # Skip duplicate

        # Upsert processed keyword
        cursor.execute("""
            INSERT INTO processed_keywords (keyword_hash, keyword)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE last_seen = NOW(), times_seen = times_seen + 1
        """, (keyword_hash, keyword))

        # Insert raw trend
        import json
        cursor.execute("""
            INSERT INTO raw_trends (source, keyword, title, description, url, region, language, popularity_score, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (source, keyword, title, description, url, region, language, popularity_score,
              json.dumps(raw_data) if raw_data else None))

        trend_id = cursor.lastrowid
        conn.commit()
        return trend_id
    except Exception as e:
        print(f"[DB] Error inserting trend: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def insert_scored_trend(raw_trend_id, topic, summary, scores, suggested_format,
                        suggested_angle, affiliate_opportunities, content_language="he"):
    """Insert an analyzed/scored trend."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        overall = calculate_overall_score(scores)
        cursor.execute("""
            INSERT INTO scored_trends 
            (raw_trend_id, topic, summary, niche_relevance, monetization_score, 
             urgency_score, competition_score, hebrew_gap, overall_score,
             suggested_format, suggested_angle, affiliate_opportunities, content_language)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (raw_trend_id, topic, summary,
              scores.get("niche_relevance", 0),
              scores.get("monetization_score", 0),
              scores.get("urgency_score", 0),
              scores.get("competition_score", 0),
              scores.get("hebrew_gap", 0),
              overall,
              suggested_format, suggested_angle, affiliate_opportunities, content_language))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"[DB] Error inserting scored trend: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def get_unscored_trends(limit=20):
    """Get raw trends that haven't been analyzed yet."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT r.* FROM raw_trends r
            LEFT JOIN scored_trends s ON s.raw_trend_id = r.id
            WHERE s.id IS NULL
            ORDER BY r.scraped_at DESC
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def calculate_overall_score(scores):
    """Weighted score - monetization and hebrew gap matter most."""
    weights = {
        "niche_relevance": 0.15,
        "monetization_score": 0.30,
        "urgency_score": 0.15,
        "competition_score": 0.15,
        "hebrew_gap": 0.25,
    }
    total = sum(scores.get(k, 0) * w for k, w in weights.items())
    return round(total)
