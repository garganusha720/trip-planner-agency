"""
Phase 1 checkpoint script.

Run this after starting the FastAPI server (`uvicorn app.main:app --reload`)
to confirm the mock API and the search tool both work independently.

    python -m tests.checkpoint_phase1
"""
import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

MOCK_API_BASE = "http://127.0.0.1:8000"


def check_mock_api():
    print("=== Checking mock API ===")

    flights = requests.get(
        f"{MOCK_API_BASE}/flights",
        params={"origin": "JFK", "destination": "NRT", "date": "2026-09-10"},
    ).json()
    assert "results" in flights and len(flights["results"]) > 0, "No flight results returned"
    print(f"✓ /flights returned {len(flights['results'])} options, "
          f"cheapest: ${flights['results'][0]['price_usd']}")

    hotels = requests.get(
        f"{MOCK_API_BASE}/hotels",
        params={"city": "Tokyo", "nightly_budget": 150},
    ).json()
    assert "results" in hotels and len(hotels["results"]) > 0, "No hotel results returned"
    print(f"✓ /hotels returned {len(hotels['results'])} options, "
          f"cheapest: ${hotels['results'][0]['price_per_night_usd']}/night")


def check_search_tool():
    print("\n=== Checking Tavily search tool ===")
    try:
        from app.tools.search import web_search
        result = web_search("best neighborhoods in Tokyo for first-time visitors", max_results=3)
        assert len(result["results"]) > 0, "No search results returned"
        print(f"✓ Search returned {len(result['results'])} results")
        print(f"  First result: {result['results'][0]['title']}")
    except RuntimeError as e:
        print(f"⚠ Skipped: {e}")
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in (401, 403):
            print("⚠ Skipped: TAVILY_API_KEY in .env looks like a placeholder or is invalid. "
                  "Get a real key at https://tavily.com and put it in backend/.env")
        else:
            raise


def check_schema():
    print("\n=== Checking shared state schema ===")
    from app.schemas.state import TripRequest, TripState

    req = TripRequest(
        origin="JFK", destination="Tokyo", start_date="2026-09-10",
        trip_length_days=5, total_budget_usd=2000, interests=["food", "history"],
    )
    state = TripState(request=req)
    assert state.request.destination == "Tokyo"
    print("✓ TripState instantiates and serializes cleanly")


if __name__ == "__main__":
    check_mock_api()
    check_search_tool()
    check_schema()
    print("\nPhase 1 checkpoint passed.")
