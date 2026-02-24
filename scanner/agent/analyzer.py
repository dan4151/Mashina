"""
Trend Analyzer Agent - Uses a local LLM (via Ollama) to analyze raw trends
and score them for content creation potential.
"""

import os
import json
import ollama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "host.docker.internal")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

# Configure ollama client to talk to host machine
client = ollama.Client(host=f"http://{OLLAMA_HOST}:{OLLAMA_PORT}")

SYSTEM_PROMPT = """You are a social media content strategist specializing in AI/tech content for the Israeli market.
You analyze trending topics and score them for content creation potential on TikTok and Instagram.

Your target audience:
- Hebrew-speaking Israelis interested in AI and technology
- English-speaking tech enthusiasts in Israel
- People looking for AI tool recommendations

Your content formats: TikTok short videos, Instagram Reels, carousel posts, stories.

Your monetization model: Affiliate links to AI tools/products, building an AI influencer brand.

For each trend, you MUST respond with ONLY a valid JSON object (no markdown, no explanation) with these fields:
{
    "topic": "concise topic name",
    "summary": "2-3 sentence summary of why this trend matters",
    "niche_relevance": <1-10>,
    "monetization_score": <1-10>,
    "urgency_score": <1-10>,
    "competition_score": <1-10, where 10=very low competition=good>,
    "hebrew_gap": <1-10, where 10=zero Hebrew content exists about this=good>,
    "suggested_format": "short_video|reel|carousel|story",
    "suggested_angle": "specific content angle and hook for the video",
    "affiliate_opportunities": "specific tools or products to link to, or 'none'",
    "content_language": "he|en|both"
}

Scoring guidelines:
- niche_relevance: Is this about AI, tech tools, or something the Israeli tech audience cares about?
- monetization_score: Can we link to affiliate products? Is there a tool to recommend? Higher = more $$$ potential.
- urgency_score: Is this breaking news that needs to go out NOW, or evergreen? Higher = more urgent.
- competition_score: How much Hebrew content exists about this already? 10 = nobody has covered this in Hebrew.
- hebrew_gap: Is there a real gap in Hebrew content here? 10 = total gap, huge opportunity.
"""


def analyze_trend(trend: dict) -> dict | None:
    """
    Send a raw trend to the LLM for analysis and scoring.
    Returns parsed scores dict or None on failure.
    """
    user_prompt = f"""Analyze this trending topic for content creation potential:

Source: {trend.get('source', 'unknown')}
Keyword: {trend.get('keyword', '')}
Title: {trend.get('title', '')}
Description: {trend.get('description', '')}
Region: {trend.get('region', 'IL')}
Language: {trend.get('language', 'he')}
Popularity: {trend.get('popularity_score', 0)}

Respond with ONLY the JSON object, no other text."""

    try:
        response = client.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            options={
                "temperature": 0.3,  # Low temp for consistent scoring
                "num_predict": 1000,
            },
        )

        content = response["message"]["content"].strip()

        # Try to extract JSON from response (LLMs sometimes wrap in markdown)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        # Validate required fields
        required = ["topic", "summary", "niche_relevance", "monetization_score",
                     "urgency_score", "competition_score", "hebrew_gap"]
        if not all(k in result for k in required):
            print(f"[Agent] Missing required fields in response")
            return None

        # Clamp scores to 1-10
        for key in ["niche_relevance", "monetization_score", "urgency_score",
                     "competition_score", "hebrew_gap"]:
            result[key] = max(1, min(10, int(result[key])))

        return result

    except json.JSONDecodeError as e:
        print(f"[Agent] Failed to parse JSON response: {e}")
        print(f"[Agent] Raw response: {content[:500]}")
        return None
    except Exception as e:
        print(f"[Agent] Error analyzing trend: {e}")
        return None


def analyze_batch(trends: list[dict]) -> list[dict]:
    """Analyze a batch of trends. Returns list of successfully analyzed results."""
    results = []
    for i, trend in enumerate(trends):
        print(f"[Agent] Analyzing {i+1}/{len(trends)}: {trend.get('keyword', '')[:60]}...")
        result = analyze_trend(trend)
        if result:
            result["_raw_trend_id"] = trend.get("id")
            results.append(result)
        else:
            print(f"[Agent] Skipped (analysis failed)")
    
    print(f"[Agent] Successfully analyzed {len(results)}/{len(trends)} trends")
    return results
