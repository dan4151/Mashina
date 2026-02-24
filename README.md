# Trend Scanner v1.0

AI-powered trend scanner for the Israeli market. Scrapes Google Trends, Reddit, Product Hunt, and Israeli tech news, then uses a local LLM to analyze and score each trend for content creation and monetization potential.

## Prerequisites

- Docker Desktop (running)
- Ollama installed on Windows with a model pulled
- NVIDIA GPU with drivers installed

## Quick Start

### 1. Pull an Ollama model (run on Windows, not in Docker)
```bash
ollama pull qwen3:8b
```

### 2. Make sure Ollama is running
```bash
ollama serve
```
(It usually auto-starts, check system tray)

### 3. Start the scanner
```bash
cd trend-scanner
docker-compose up --build
```

### 4. Watch the logs
```bash
docker-compose logs -f scanner
```

### 5. Check results in MySQL
```bash
docker exec -it trend-db mysql -u root -ptrendscanner123 trends

-- Top scored trends
SELECT topic, overall_score, monetization_score, hebrew_gap, suggested_format, suggested_angle 
FROM scored_trends 
ORDER BY overall_score DESC 
LIMIT 10;
```

## Architecture

```
[Google Trends IL] ──┐
[Reddit AI subs]  ───┤
[Product Hunt]    ───┼──→ Raw Trends DB ──→ LLM Analyzer ──→ Scored Trends DB
[Israeli News]    ───┘         (MySQL)        (Ollama)           (MySQL)
```

## Scoring Weights

| Factor | Weight | Description |
|--------|--------|-------------|
| Monetization | 30% | Affiliate/ad revenue potential |
| Hebrew Gap | 25% | Lack of existing Hebrew content |
| Niche Relevance | 15% | Fit with AI/tech niche |
| Competition | 15% | Low competition = high score |
| Urgency | 15% | Time sensitivity |

## Configuration

Edit `.env` to change settings:
- `SCAN_INTERVAL_MINUTES` - How often to scan (default: 30)
- `OLLAMA_MODEL` - Which model to use (default: llama3.1:8b)
