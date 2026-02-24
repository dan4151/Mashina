CREATE DATABASE IF NOT EXISTS trends;
USE trends;

-- Raw trends collected from all sources
CREATE TABLE raw_trends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(50) NOT NULL COMMENT 'google_trends, reddit, producthunt, tiktok, news',
    keyword VARCHAR(500) NOT NULL,
    title VARCHAR(1000),
    description TEXT,
    url VARCHAR(2000),
    region VARCHAR(10) DEFAULT 'IL' COMMENT 'ISO country code',
    language VARCHAR(10) DEFAULT 'he',
    popularity_score INT DEFAULT 0 COMMENT 'Source-specific popularity metric',
    raw_data JSON COMMENT 'Full raw response from source',
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_source (source),
    INDEX idx_scraped (scraped_at),
    INDEX idx_keyword (keyword(100))
);

-- Agent-analyzed and scored trends
CREATE TABLE scored_trends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    raw_trend_id INT,
    topic VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL COMMENT 'Agent summary of the trend',
    niche_relevance TINYINT DEFAULT 0 COMMENT '1-10: How relevant to AI/tech niche',
    monetization_score TINYINT DEFAULT 0 COMMENT '1-10: Affiliate/ad potential',
    urgency_score TINYINT DEFAULT 0 COMMENT '1-10: How time-sensitive',
    competition_score TINYINT DEFAULT 0 COMMENT '1-10: 10=low competition (good)',
    hebrew_gap TINYINT DEFAULT 0 COMMENT '1-10: 10=no Hebrew content exists (good)',
    overall_score TINYINT DEFAULT 0 COMMENT 'Weighted combined score',
    suggested_format VARCHAR(50) COMMENT 'short_video, reel, carousel, story',
    suggested_angle TEXT COMMENT 'Agent suggestion for content angle',
    affiliate_opportunities TEXT COMMENT 'Specific products/tools to promote',
    content_language VARCHAR(10) DEFAULT 'he' COMMENT 'he or en',
    status ENUM('new', 'assigned', 'in_production', 'published', 'skipped') DEFAULT 'new',
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_trend_id) REFERENCES raw_trends(id),
    INDEX idx_status (status),
    INDEX idx_overall (overall_score DESC),
    INDEX idx_analyzed (analyzed_at)
);

-- Track what we already processed to avoid duplicates
CREATE TABLE processed_keywords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    keyword_hash VARCHAR(64) NOT NULL UNIQUE,
    keyword VARCHAR(500) NOT NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    times_seen INT DEFAULT 1
);
