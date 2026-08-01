"""
Thin wrapper around the Tavily search API.

Get a free API key at https://tavily.com and put it in backend/.env as:
    TAVILY_API_KEY=tvly-xxxxxxxx

Usage:
    python -m app.tools.search "best neighborhoods in Tokyo for first-time visitors"
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

TAVILY_URL = "https://api.tavily.com/search"


def web_search(query: str, max_results: int = 5) -> dict:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY not set. Add it to backend/.env (see comment at top of this file)."
        )

    response = requests.post(
        TAVILY_URL,
        json={
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": False,
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    return {
        "query": query,
        "results": [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "content": r.get("content"),
            }
            for r in data.get("results", [])
        ],
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.tools.search '<query>'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    result = web_search(query)
    print(f"\nQuery: {result['query']}\n")
    for i, r in enumerate(result["results"], 1):
        print(f"{i}. {r['title']}")
        print(f"   {r['url']}")
        print(f"   {r['content'][:150]}...\n")
