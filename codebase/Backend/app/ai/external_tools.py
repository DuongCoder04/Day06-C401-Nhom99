"""
External tool implementations — real-world data sources.

Each tool returns a structured dict that gets injected into the agent context
before LLM generates the final reply.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env once so tools work when called directly (not via app startup)
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


# ── Weather ───────────────────────────────────────────────────────────────────

def get_weather(city: str = "Ho Chi Minh City") -> dict[str, Any]:
    """
    Fetch current weather via OpenWeatherMap free API.
    Returns a structured dict with condition, temp, description in Vietnamese.

    Requires: OPENWEATHERMAP_API_KEY in env.
    Falls back to {"available": False} when key missing or request fails.
    """
    api_key = os.getenv("OPENWEATHERMAP_API_KEY", "").strip()
    if not api_key:
        return {"available": False, "reason": "no_api_key"}

    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={urllib.parse.quote(city)}&appid={api_key}&units=metric&lang=vi"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Yumi/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"available": False, "reason": "request_failed"}

    weather_id = data.get("weather", [{}])[0].get("id", 800)
    description = data.get("weather", [{}])[0].get("description", "")
    temp = round(data.get("main", {}).get("temp", 28))
    feels_like = round(data.get("main", {}).get("feels_like", 28))
    humidity = data.get("main", {}).get("humidity", 70)

    # Map OWM weather IDs to Yumi's internal condition tags
    if weather_id < 300:
        condition = "storm"
    elif weather_id < 600:
        condition = "rain"
    elif weather_id < 700:
        condition = "cold"
    elif weather_id == 800:
        condition = "clear"
    elif weather_id < 805:
        condition = "cloudy"
    else:
        condition = "cloudy"

    if temp >= 35:
        condition = "hot"
    elif temp <= 20:
        condition = "cold"

    return {
        "available": True,
        "city": data.get("name", city),
        "condition": condition,
        "temp": temp,
        "feels_like": feels_like,
        "humidity": humidity,
        "description": description,
        # Human-readable summary for LLM to use in reply
        "summary": _weather_summary(condition, temp, description),
    }


def _weather_summary(condition: str, temp: int, description: str) -> str:
    if condition == "rain":
        return f"Trời đang mưa, {temp}°C — nên chọn món nóng hoặc ấm bụng."
    if condition == "storm":
        return f"Trời mưa bão, {temp}°C — nên đặt đồ về nhà, ưu tiên món nóng."
    if condition == "cold":
        return f"Trời lạnh, {temp}°C — hợp với món nóng, lẩu hoặc súp."
    if condition == "hot":
        return f"Trời nóng, {temp}°C — nên chọn món mát, nhẹ hoặc đồ uống lạnh."
    return f"Thời tiết {description}, {temp}°C."


# ── Web Search ────────────────────────────────────────────────────────────────

def search_web(query: str, max_results: int = 3) -> dict[str, Any]:
    """
    Search the web via Tavily API for food-related queries.
    Returns top results with title, url, content snippet.

    Requires: TAVILY_API_KEY in env.
    Falls back to {"available": False} when key missing or request fails.
    """
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return {"available": False, "reason": "no_api_key"}

    body = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": True,
    }
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"available": False, "reason": "request_failed"}

    results = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")[:300],
        }
        for r in data.get("results", [])
    ]
    return {
        "available": True,
        "answer": data.get("answer", ""),
        "results": results,
    }
