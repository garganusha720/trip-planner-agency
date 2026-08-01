"""
FastAPI app for the trip planner's mock data layer and the full agent
orchestrator.

Run with:
    uvicorn app.main:app --reload --port 8000

Then test:
    GET  /flights?origin=JFK&destination=NRT&date=2026-09-10
    GET  /hotels?city=Tokyo&nightly_budget=150
    POST /plan-trip  (see PlanTripRequest below for the body shape)
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.agents.orchestrator import plan_trip
from app.mock_api.flights import search_flights
from app.mock_api.hotels import search_hotels
from app.schemas.state import TripRequest, TripState

app = FastAPI(
    title="Trip Planner Mock Data API",
    description="Deterministic mock flights/hotels data for the AI Trip Planner Agency project.",
    version="0.1.0",
)

# Allows a browser-based frontend (e.g. a Next.js app from v0.dev, running on
# its own port like localhost:3000) to call this API directly. Without this,
# the browser blocks the request with a CORS error before it even reaches
# your route handlers. Streamlit didn't need this since it makes server-side
# requests, not browser-side ones.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for local dev; restrict this before deploying publicly
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/flights")
def get_flights(
    origin: str = Query(..., description="Origin airport/city code, e.g. JFK"),
    destination: str = Query(..., description="Destination airport/city code, e.g. NRT"),
    date: str = Query(..., description="Travel date, e.g. 2026-09-10"),
    currency: str = Query("USD", description="USD, INR, EUR, or GBP"),
    cabin_class: str = Query("economy", description="economy, premium_economy, business, or first"),
):
    results = search_flights(origin, destination, date, currency, cabin_class)
    return {
        "origin": origin,
        "destination": destination,
        "date": date,
        "currency": currency.upper(),
        "cabin_class": cabin_class,
        "results": results,
    }


@app.get("/hotels")
def get_hotels(
    city: str = Query(..., description="City name, e.g. Tokyo"),
    nightly_budget: float | None = Query(
        None, description="Optional max nightly budget (in the given currency) to filter results"
    ),
    currency: str = Query("USD", description="USD, INR, EUR, or GBP"),
    min_rating: float = Query(0.0, description="Minimum acceptable hotel star rating (0 = any)"),
):
    results = search_hotels(city, nightly_budget, currency, min_rating)
    return {
        "city": city,
        "nightly_budget": nightly_budget,
        "currency": currency.upper(),
        "min_rating": min_rating,
        "results": results,
    }


@app.post("/plan-trip", response_model=TripState)
def plan_trip_endpoint(trip_request: TripRequest):
    """
    Runs the full agent pipeline: Research -> Budget -> Itinerary ->
    Validator (with automatic retry-on-conflict via LangGraph).

    This can take 20-60+ seconds depending on how many retries the
    validator triggers — it's a synchronous call, so the client just
    waits for the full response rather than polling for a result.

    Example body:
    {
      "origin": "JFK",
      "destination": "Lisbon",
      "start_date": "2026-09-10",
      "trip_length_days": 3,
      "total_budget": 1200,
      "currency": "USD",
      "interests": ["food", "history"]
    }
    """
    try:
        result = plan_trip(
            origin=trip_request.origin,
            destination=trip_request.destination,
            start_date=trip_request.start_date,
            trip_length_days=trip_request.trip_length_days,
            total_budget=trip_request.total_budget,
            interests=trip_request.interests,
            currency=trip_request.currency,
            cabin_class=trip_request.cabin_class,
            hotel_min_rating=trip_request.hotel_min_rating,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return result
