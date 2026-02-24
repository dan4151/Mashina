# Trend Scanner - AI Content Monetization Engine

## What This Project Is
An automated system that scans the web for trending topics, analyzes them with a local LLM, and scores them for content creation and monetization potential. Target market: Israeli audience (Hebrew + English), AI/tech niche, TikTok and Instagram.

## Owner Context
- I am good with Python, MySQL, agents, and Ollama but I am NOT a developer
- Keep code simple, well-commented, and explain what things do
- I run Windows 11 with Docker Desktop + WSL2
- GPU: NVIDIA 4070 Ti 12GB VRAM
- All services run in Docker containers
- LLM runs on host via Ollama (accessed from Docker via host.docker.internal)

## Architecture
```
Scrapers (every 30 min) → Raw Trends (MySQL) → LLM Agent (Qwen3 8B via Ollama) → Scored Trends (MySQL)
```

### Services (Docker Compose)
- **mysql** (trend-db): MySQL 8.0 on port 3306, database name: `trends`
- **scanner** (trend-scanner): Python service that runs scrapers + LLM analyzer on schedule

### Data Flow
1. Scrapers collect trends from: Google Trends IL, Reddit AI subs, Product Hunt, Israeli tech news RSS
2. Raw trends stored in `raw_trends` table (deduped via `processed_keywords`)
3. LLM analyzer (Qwen3 8B) scores each trend on: niche_relevance, monetization_score, urgency_score, competition_score, hebrew_gap
4. Scored trends stored in `scored_trends` table with suggested content format, angle, and affiliate opportunities

### Scoring Weights
- Monetization: 30%
- Hebrew gap: 25%
- Niche relevance: 15%
- Competition: 15%
- Urgency: 15%

## Tech Stack
- Python 3.11
- MySQL 8.0
- Ollama with Qwen3 8B (runs on host Windows, not in Docker)
- Docker + Docker Compose
- Key libraries: pytrends, requests, beautifulsoup4, feedparser, ollama, schedule, mysql-connector-python

## Project Structure
```
trend-scanner/
├── docker-compose.yml          # MySQL + scanner services
├── .env                        # Config (model, DB creds, scan interval)
├── db/
│   └── init.sql                # MySQL schema (raw_trends, scored_trends, processed_keywords)
├── scanner/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # Entry point + scheduler
│   ├── scrapers/
│   │   ├── google_trends.py    # Google Trends Israel
│   │   ├── reddit.py           # Reddit AI/tech subreddits (public JSON API)
│   │   ├── producthunt.py      # Product Hunt RSS feed
│   │   └── israeli_news.py     # Geektime, Calcalist, Globes RSS
│   ├── agent/
│   │   └── analyzer.py         # LLM trend analyzer (Ollama/Qwen3)
│   └── db/
│       └── models.py           # DB connection pool + CRUD helpers
```

## Running
```bash
# Make sure Ollama is running on Windows with qwen3:8b pulled
ollama serve
# Start everything
docker-compose up --build
# Watch scanner logs
docker-compose logs -f scanner
# Query top trends
docker exec -it trend-db mysql -u root -ptrendscanner123 trends -e "SELECT topic, overall_score, suggested_angle FROM scored_trends ORDER BY overall_score DESC LIMIT 10;"
```

## What's Next (Roadmap)
These are the agents/services to build next, in order:

### Phase 2 - Content Strategy Agent
- Reads top scored trends from MySQL
- Decides which ones to produce content for
- Plans content: format (reel, carousel, story), language (he/en/both), posting schedule
- Updates scored_trends status from 'new' to 'assigned'

### Phase 3 - Script Writer Agent
- Takes assigned trends and writes TikTok/Reel scripts
- Uses Qwen3 for English, needs testing for Hebrew (may need Gemma 3 12B)
- Outputs: hook, script body, CTA, hashtags, affiliate link placement

### Phase 4 - Media Generator
- Stable Diffusion (local) for images/thumbnails
- TTS for voiceover (Hebrew + English)
- AI avatar video via HeyGen API (cloud, free tier)
- FFmpeg for video assembly

### Phase 5 - Publisher Agent
- Posts to TikTok and Instagram via APIs
- Schedules posts for optimal times
- Tracks post performance

### Phase 6 - Analytics Agent
- Monitors published content performance
- Feeds data back to improve scoring and strategy
- A/B testing different content angles

## Important Notes
- All API access is currently FREE (no paid APIs)
- Ollama connects from Docker via host.docker.internal:11434
- Scanner runs every 30 minutes (configurable via SCAN_INTERVAL_MINUTES in .env)
- Hebrew content is the main competitive advantage - focus on hebrew_gap score
- Monetization is through affiliate links to AI tools/products
