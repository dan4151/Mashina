# Trend Scanner - AI Content Monetization Engine

## What This Project Is

An automated system that scans the web for trending topics, analyzes them with a local LLM, and scores them for content creation and monetization potential. Target market: Israeli audience (Hebrew + English), AI/tech niche, TikTok and Instagram.

## Owner Context (Important for AI Assistants)

- Owner is comfortable with Python, MySQL, agents, and Ollama — but is **not** a professional developer
- **Always keep code simple and well-commented** — explain what each block does
- Environment: Windows 11 + Docker Desktop + WSL2
- GPU: NVIDIA 4070 Ti (12GB VRAM)
- All services run in Docker containers
- LLM runs on the **Windows host** via Ollama, accessed from Docker via `host.docker.internal`
- Never suggest solutions that require a Linux-native setup or complex DevOps tooling

---

## Architecture

```
Scrapers (every 30 min)
    ↓
raw_trends table (MySQL)   ← deduped via processed_keywords
    ↓
LLM Analyzer (Qwen3 8B via Ollama)
    ↓
scored_trends table (MySQL)
    ↓
[Future: Content Strategy → Script Writer → Media → Publisher → Analytics]
```

### Docker Services (docker-compose.yml)

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| `mysql` | `trend-db` | 3306 | MySQL 8.0, database: `trends` |
| `scanner` | `trend-scanner` | — | Python service: scrapers + LLM analyzer |

- `scanner` waits for `mysql` health check before starting
- `scanner` has `extra_hosts: host.docker.internal:host-gateway` so it can reach Ollama on Windows
- Both services configured via `.env`

---

## Project Structure

```
Mashina/
├── docker-compose.yml          # Service orchestration
├── .env                        # Secrets + config (never commit real values)
├── CLAUDE.md                   # This file
├── README.md                   # User-facing quick start guide
├── db/
│   └── init.sql                # MySQL schema — runs automatically on first DB start
└── scanner/
    ├── Dockerfile               # FROM python:3.11-slim, installs requirements
    ├── requirements.txt         # Python dependencies (pinned versions)
    ├── main.py                  # Entrypoint: scheduler + orchestration
    ├── agent/
    │   ├── __init__.py
    │   └── analyzer.py          # Ollama LLM client + JSON response parsing
    ├── db/
    │   ├── __init__.py
    │   └── models.py            # Connection pool + all DB CRUD functions
    └── scrapers/
        ├── __init__.py
        ├── google_trends.py     # pytrends: Israel trending + rising AI queries
        ├── reddit.py            # Public Reddit JSON API (no auth needed)
        ├── producthunt.py       # Product Hunt RSS feed
        └── israeli_news.py      # Geektime, Calcalist, Globes RSS feeds
```

---

## Environment Variables (.env)

```
MYSQL_ROOT_PASSWORD=trendscanner123
OLLAMA_HOST=host.docker.internal
OLLAMA_PORT=11434
OLLAMA_MODEL=qwen3:8b
SCAN_INTERVAL_MINUTES=30
```

These are passed into the `scanner` container via `environment:` in docker-compose.yml and read with `os.environ.get()` in Python code.

---

## Database Schema (db/init.sql)

### `raw_trends` — Raw scraper output

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT AUTO_INCREMENT PK | |
| `source` | VARCHAR(50) | `google_trends`, `reddit`, `producthunt`, `israeli_news` |
| `keyword` | VARCHAR(500) | Short identifier for deduplication |
| `title` | VARCHAR(1000) | Human-readable title |
| `description` | TEXT | Optional excerpt/summary |
| `url` | VARCHAR(2000) | Link to source |
| `region` | VARCHAR(10) | `IL` or `global` |
| `language` | VARCHAR(10) | `he` or `en` |
| `popularity_score` | INT | Source-specific metric (0–100) |
| `raw_data` | JSON | Full original data blob |
| `scraped_at` | TIMESTAMP | Auto-set on insert |

Indexes: `source`, `scraped_at`, `keyword(100)`

### `scored_trends` — LLM analysis results

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT AUTO_INCREMENT PK | |
| `raw_trend_id` | INT FK | References `raw_trends.id` |
| `topic` | VARCHAR(500) | Cleaned topic name from LLM |
| `summary` | TEXT | LLM-generated summary |
| `niche_relevance` | TINYINT | 1–10: fit for AI/tech niche |
| `monetization_score` | TINYINT | 1–10: affiliate link potential |
| `urgency_score` | TINYINT | 1–10: time-sensitivity |
| `competition_score` | TINYINT | 1–10: **10 = low competition** (good) |
| `hebrew_gap` | TINYINT | 1–10: **10 = no Hebrew content exists** (good) |
| `overall_score` | TINYINT | Weighted combination (see weights below) |
| `suggested_format` | VARCHAR(50) | `short_video`, `reel`, `carousel`, `story` |
| `suggested_angle` | TEXT | LLM content angle recommendation |
| `affiliate_opportunities` | TEXT | LLM-suggested affiliate products |
| `content_language` | VARCHAR(10) | `he`, `en`, or `both` |
| `status` | ENUM | `new` → `assigned` → `in_production` → `published` / `skipped` |
| `analyzed_at` | TIMESTAMP | Auto-set on insert |

Indexes: `status`, `overall_score DESC`, `analyzed_at`

### `processed_keywords` — Deduplication table

| Column | Type | Notes |
|--------|------|-------|
| `id` | INT AUTO_INCREMENT PK | |
| `keyword_hash` | VARCHAR(64) UNIQUE | SHA256 of `"source:keyword"` |
| `keyword` | VARCHAR(500) | |
| `first_seen` | TIMESTAMP | |
| `last_seen` | TIMESTAMP | Updated on each repeat encounter |
| `times_seen` | INT | Incremented on each encounter |

**Deduplication rule**: A keyword hash seen within the last **6 hours** is skipped. After 6 hours, the same keyword can be re-processed (trends evolve).

---

## Scoring System

```python
overall_score = round(
    monetization_score  * 0.30 +
    hebrew_gap          * 0.25 +
    niche_relevance     * 0.15 +
    competition_score   * 0.15 +
    urgency_score       * 0.15
)
```

**Weight rationale:**
- Monetization (30%): Primary goal — affiliate revenue
- Hebrew gap (25%): Main competitive advantage — very little Hebrew AI content exists
- Niche relevance (15%): Must stay on-topic (AI/tech)
- Competition (15%): Lower competition = easier to rank/gain views
- Urgency (15%): Timely content performs better

---

## Code Conventions & Patterns

### Module Responsibilities

| File | Responsibility |
|------|---------------|
| `main.py` | Scheduler only — calls scrapers and analyzer, logs output |
| `scrapers/*.py` | Return a list of dicts matching the `raw_trends` column schema |
| `db/models.py` | All DB interaction — no SQL anywhere else |
| `agent/analyzer.py` | All Ollama/LLM interaction — prompt engineering + JSON parsing |

### Scraper Return Format

Every scraper returns `list[dict]`. Each dict **must** have these keys:

```python
{
    "keyword": str,           # Short, dedup-friendly string (max 200 chars)
    "title": str,             # Full display title
    "description": str,       # Optional excerpt (empty string if none)
    "url": str,               # Link to original source
    "popularity_score": int,  # 0–100 (use fixed values if no metric available)
    "region": str,            # "IL" for Israeli sources, "global" for international
    "language": str,          # "he" or "en"
    "raw_data": dict,         # Any extra source-specific data (stored as JSON)
}
```

The `source` field is added by `insert_raw_trend()` in `models.py` — scrapers don't set it.

### Popularity Score Conventions

| Source | Score approach |
|--------|---------------|
| Google Trends | `100 - (rank * 5)` for trending; raw value for rising |
| Reddit | `min(upvotes, 100)` |
| Product Hunt | Fixed `70` (curated products are generally high-value) |
| Israeli News | Fixed `60` |

### Error Handling Pattern

All scrapers follow this pattern — they never crash the whole pipeline:

```python
try:
    # scraping logic
    return trends
except Exception as e:
    print(f"[ScraperName] Error: {e}")
    return []  # Always return empty list on failure
```

The analyzer also returns `None` per trend on parse failure and skips it.

### Database Access Pattern

All DB code uses a **connection pool** (`pool` in `models.py`):

```python
conn = pool.get_connection()
cursor = conn.cursor(dictionary=True)  # Returns rows as dicts
# ... do work ...
conn.commit()
cursor.close()
conn.close()  # Returns connection to pool, doesn't close it
```

Never create raw `mysql.connector.connect()` calls outside `models.py`.

### Rate Limiting

All scrapers include deliberate delays to avoid bans:

```python
import time
time.sleep(2)  # Between requests to the same service
```

- Google Trends: 2 seconds between pytrends calls
- Reddit: 2 seconds between subreddit requests
- Israeli News: 1 second between feed fetches

### LLM Response Parsing

The LLM is prompted to return JSON. The response may be wrapped in markdown fences (` ```json ... ``` `). The analyzer strips these before parsing:

```python
if "```json" in text:
    text = text.split("```json")[1].split("```")[0]
elif "```" in text:
    text = text.split("```")[1].split("```")[0]
```

All scores are clamped to 1–10 after parsing:
```python
score = max(1, min(10, int(raw_score)))
```

---

## LLM Configuration

| Setting | Value |
|---------|-------|
| Model | `qwen3:8b` (Alibaba Qwen 3, 8B parameters) |
| Host | `host.docker.internal:11434` (Ollama on Windows) |
| Temperature | `0.3` — low for consistent scoring |
| Max tokens | `1000` |
| Context | System prompt establishes Israeli market + monetization focus |

**System prompt role**: "social media content strategist for the Israeli market" specializing in AI/tech, TikTok, Instagram Reels, and affiliate monetization.

**Expected LLM JSON output fields:**
```json
{
  "topic": "Clean topic name",
  "summary": "2-3 sentence summary",
  "niche_relevance": 8,
  "monetization_score": 7,
  "urgency_score": 6,
  "competition_score": 9,
  "hebrew_gap": 10,
  "suggested_format": "short_video",
  "suggested_angle": "How this helps Israeli users",
  "affiliate_opportunities": "Cursor AI, GitHub Copilot",
  "content_language": "he"
}
```

---

## Data Sources

| Source | Type | Method | Rate limit |
|--------|------|--------|-----------|
| Google Trends Israel | Trending searches + rising AI queries | `pytrends` library | 2s delay |
| Reddit | Rising + hot posts from 7 AI subreddits | Public JSON API (no auth) | 2s delay |
| Product Hunt | New AI/tech products | RSS feed | None |
| Israeli News | AI/tech articles | RSS feeds (3 publications) | 1s delay |

### Reddit Subreddits Monitored
`artificial`, `ChatGPT`, `LocalLLaMA`, `MachineLearning`, `singularity`, `StableDiffusion`, `Israel`

### Israeli News RSS Sources
- Geektime: `https://www.geektime.co.il/feed/` (Hebrew)
- Calcalist Tech: `https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml` (Hebrew)
- Globes Tech: `https://www.globes.co.il/webservice/rss/rssfeeder.asmx/FeederC?iID=585` (Hebrew)

**Note**: `praw` is in requirements.txt but unused — Reddit scraper uses the public JSON API (`reddit.com/r/{sub}/rising.json`) which requires no authentication.

---

## How to Add a New Scraper

1. Create `scanner/scrapers/my_source.py`
2. Implement a function that returns `list[dict]` using the scraper return format above
3. Add error handling (return `[]` on any exception)
4. Add rate-limiting delays between requests
5. Import and call it in `main.py` inside `run_scrapers()`:
   ```python
   from scrapers.my_source import scrape_my_source
   trends = scrape_my_source()
   for t in trends:
       insert_raw_trend(t, source="my_source")
   ```

---

## How to Add a New Phase (e.g., Phase 2: Content Strategy Agent)

1. Create a new directory: `scanner/agent/content_strategy.py`
2. Read from `scored_trends` where `status = 'new'` using a new function in `models.py`
3. Process trends, then update `status` to `'assigned'` via another `models.py` function
4. Add a new scheduler job in `main.py` (e.g., `schedule.every(1).hours.do(run_content_strategy)`)
5. Keep the new agent in a separate file — don't mix concerns into `analyzer.py`

---

## Running the Project

```bash
# 1. On Windows host: make sure Ollama is running with the right model
ollama serve
ollama pull qwen3:8b

# 2. Start Docker services
docker-compose up --build

# 3. Watch scanner logs in real time
docker-compose logs -f scanner

# 4. Query top-scoring trends
docker exec -it trend-db mysql -u root -ptrendscanner123 trends \
  -e "SELECT topic, overall_score, suggested_angle FROM scored_trends ORDER BY overall_score DESC LIMIT 10;"

# 5. Check raw trends volume
docker exec -it trend-db mysql -u root -ptrendscanner123 trends \
  -e "SELECT source, COUNT(*) as count FROM raw_trends GROUP BY source;"

# 6. Stop everything
docker-compose down

# 7. Stop and wipe database (full reset)
docker-compose down -v
```

---

## Debugging Tips

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Scanner can't connect to MySQL | DB not ready yet | Wait — scanner retries on start |
| Analyzer returns no results | Ollama not running / wrong model | Check `ollama list` on Windows host |
| Google Trends returning empty | pytrends rate-limited | Add longer sleep or change keywords |
| `host.docker.internal` not resolving | Docker Desktop config | Verify `extra_hosts` in docker-compose.yml |
| All trends marked as duplicates | 6-hour dedup window | Query `processed_keywords` to verify hashes |
| LLM returning invalid JSON | Model temperature too high or model changed | Check `analyzer.py` temperature setting |

---

## Roadmap

### ✅ Phase 1 — Trend Scanner (COMPLETE)
- 4 scrapers (Google, Reddit, Product Hunt, Israeli news)
- MySQL deduplication
- LLM scoring via Ollama Qwen3 8B
- Weighted scoring formula

### Phase 2 — Content Strategy Agent
- Reads top-scored `new` trends from `scored_trends`
- Decides format, language, posting schedule
- Updates `status` to `assigned`

### Phase 3 — Script Writer Agent
- Generates TikTok/Reel scripts from assigned trends
- English: Qwen3 8B | Hebrew: test Gemma 3 12B
- Output: hook, body, CTA, hashtags, affiliate link placement

### Phase 4 — Media Generator
- Thumbnails: Stable Diffusion (local, GPU)
- Voiceover: TTS (Hebrew + English)
- Video: HeyGen API (AI avatar, free tier)
- Assembly: FFmpeg

### Phase 5 — Publisher Agent
- Posts to TikTok and Instagram via APIs
- Schedule for optimal times
- Track initial post metrics

### Phase 6 — Analytics Agent
- Monitor post performance over time
- Feed metrics back to scoring model
- A/B test different content angles

---

## Important Notes for AI Assistants

- **No paid APIs** — all current data sources are free
- **Hebrew is the competitive moat** — always prioritize `hebrew_gap` in reasoning about what to build
- **Don't over-engineer** — the owner prefers simple, readable code over clever abstractions
- **All scores are 1–10** — `competition_score` and `hebrew_gap` are inverted (10 = good/low competition)
- **The `source` field** is set by `insert_raw_trend()`, not by individual scrapers
- **Connection pool size is 5** — don't create more than 5 concurrent DB connections
- **`praw` is unused** — Reddit scraper uses public JSON endpoints, not the PRAW library
- **Ollama model may change** — always read from `OLLAMA_MODEL` env var, not hardcoded strings
- **Docker volume `mysql_data`** persists the database across container restarts — use `docker-compose down -v` for a full reset
