"""
Budget & Flights Agent.

Rule-based (no LLM) — calls the mock flights/hotels API, picks a sensible
flight + hotel combination respecting the traveler's cabin class and
minimum hotel rating preferences, and checks whether the trip fits within
budget. Returns a structured `BudgetResult` (see app/schemas/state.py).

Why rule-based: budget math doesn't need reasoning, it needs correctness.
A deterministic function is faster, cheaper, and easier to debug than an
LLM call here — save the LLM for agents that actually need judgment
(research, itinerary building, conflict resolution).

Run standalone:
    python -m app.agents.budget_agent "JFK" "Lisbon" "2026-09-10" 5 1500
    python -m app.agents.budget_agent "DEL" "Jaipur" "2026-11-15" 4 15000 INR 4.0 business
"""
import os
import sys

import requests
from dotenv import load_dotenv

from app.schemas.state import BudgetResult, FlightOption, HotelOption

load_dotenv()

MOCK_API_BASE_URL = os.getenv("MOCK_API_BASE_URL", "http://localhost:8000")


def _fetch_flights(origin: str, destination: str, date: str, currency: str, cabin_class: str) -> list[dict]:
    resp = requests.get(
        f"{MOCK_API_BASE_URL}/flights",
        params={
            "origin": origin, "destination": destination, "date": date,
            "currency": currency, "cabin_class": cabin_class,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["results"]


def _fetch_hotels(
    city: str, currency: str, nightly_budget: float | None = None, min_rating: float = 0.0
) -> list[dict]:
    params = {"city": city, "currency": currency, "min_rating": min_rating}
    if nightly_budget is not None:
        params["nightly_budget"] = nightly_budget
    resp = requests.get(f"{MOCK_API_BASE_URL}/hotels", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()["results"]


def get_budget(
    origin: str,
    destination: str,
    start_date: str,
    trip_length_days: int,
    total_budget: float,
    currency: str = "USD",
    cabin_class: str = "economy",
    hotel_min_rating: float = 0.0,
) -> BudgetResult:
    currency = currency.upper()
    flights = _fetch_flights(origin, destination, start_date, currency, cabin_class)
    if not flights:
        return BudgetResult(
            currency=currency,
            total_budget=total_budget,
            trip_length_days=trip_length_days,
            feasible=False,
            feasibility_note=f"No {cabin_class} flights found from {origin} to {destination}.",
        )

    # Rule: pick the cheapest flight within the requested cabin class.
    cheapest_flight = min(flights, key=lambda f: f["price"])
    flight_cost = cheapest_flight["price"]

    remaining_after_flight = total_budget - flight_cost
    max_nightly_budget = remaining_after_flight / trip_length_days if trip_length_days > 0 else 0

    hotels = _fetch_hotels(destination, currency, nightly_budget=max_nightly_budget, min_rating=hotel_min_rating)
    budget_fit_hotels = bool(hotels)

    if not hotels:
        # Nothing fits both the rating floor and the remaining budget —
        # relax the budget filter first (keep the rating requirement,
        # since that's an explicit preference) so we can still report a
        # realistic best-case gap rather than silently ignoring the request.
        hotels = _fetch_hotels(destination, currency, min_rating=hotel_min_rating)

    if not hotels and hotel_min_rating > 0:
        return BudgetResult(
            currency=currency,
            total_budget=total_budget,
            chosen_flight=FlightOption(**cheapest_flight),
            trip_length_days=trip_length_days,
            flight_cost_total=flight_cost,
            feasible=False,
            feasibility_note=(
                f"No hotels in {destination} meet the {hotel_min_rating}+ star requirement. "
                f"Try lowering the minimum rating."
            ),
        )

    if not hotels:
        return BudgetResult(
            currency=currency,
            total_budget=total_budget,
            chosen_flight=FlightOption(**cheapest_flight),
            trip_length_days=trip_length_days,
            flight_cost_total=flight_cost,
            feasible=False,
            feasibility_note=f"No hotels found in {destination}.",
        )

    # Rule: among affordable hotels (that already meet the rating floor),
    # pick the highest-rated one. If nothing was actually affordable, pick
    # the cheapest overall instead — showing the priciest option would
    # overstate how infeasible the trip is.
    best_hotel = max(hotels, key=lambda h: h["rating"]) if budget_fit_hotels else min(hotels, key=lambda h: h["price_per_night"])
    hotel_cost_per_night = best_hotel["price_per_night"]
    hotel_cost_total = hotel_cost_per_night * trip_length_days

    total_cost = flight_cost + hotel_cost_total
    remaining_daily_budget = (total_budget - total_cost) / trip_length_days if trip_length_days > 0 else 0
    feasible = total_cost <= total_budget

    # "Tight budget" warning threshold scales with currency so it's not
    # meaningless in currencies where $20 and ₹20 are very different amounts.
    tight_threshold = {"USD": 20, "EUR": 18, "GBP": 16, "INR": 1500}.get(currency, 20)

    feasibility_note = None
    if not feasible:
        shortfall = round(total_cost - total_budget, 2)
        feasibility_note = (
            f"Budget is {shortfall} {currency} short of covering the {cabin_class} flight "
            f"({flight_cost} {currency}) + {trip_length_days} nights at {best_hotel['name']} "
            f"({hotel_cost_total} {currency}). Consider a lower cabin class, fewer trip days, "
            f"a lower minimum hotel rating, or a higher budget."
        )
    elif remaining_daily_budget < tight_threshold:
        feasibility_note = (
            f"Trip fits budget but leaves only {round(remaining_daily_budget, 2)} {currency}/day "
            f"for food and activities — tight for {trip_length_days} days."
        )

    return BudgetResult(
        currency=currency,
        total_budget=total_budget,
        chosen_flight=FlightOption(**cheapest_flight),
        chosen_hotel=HotelOption(**best_hotel),
        trip_length_days=trip_length_days,
        flight_cost_total=flight_cost,
        hotel_cost_total=hotel_cost_total,
        remaining_daily_budget=round(remaining_daily_budget, 2),
        feasible=feasible,
        feasibility_note=feasibility_note,
    )


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print('Usage: python -m app.agents.budget_agent "<origin>" "<destination>" "<start_date>" <trip_length_days> <total_budget> [currency] [hotel_min_rating] [cabin_class]')
        sys.exit(1)

    origin = sys.argv[1]
    destination = sys.argv[2]
    start_date = sys.argv[3]
    trip_length_days = int(sys.argv[4])
    total_budget = float(sys.argv[5])
    currency = sys.argv[6] if len(sys.argv) > 6 else "USD"
    hotel_min_rating = float(sys.argv[7]) if len(sys.argv) > 7 else 0.0
    cabin_class = sys.argv[8] if len(sys.argv) > 8 else "economy"

    result = get_budget(origin, destination, start_date, trip_length_days, total_budget,
                         currency, cabin_class, hotel_min_rating)

    print(f"\n=== Budget check: {origin} -> {destination}, {trip_length_days} days, {total_budget} {currency} budget ===")
    print(f"Cabin class: {cabin_class} | Min hotel rating: {hotel_min_rating}+")
    print(f"Flight: {result.chosen_flight.airline} @ {result.chosen_flight.price} {currency} ({result.chosen_flight.stops} stops, {result.chosen_flight.cabin_class})")
    print(f"Hotel: {result.chosen_hotel.name} @ {result.chosen_hotel.price_per_night} {currency}/night (rating {result.chosen_hotel.rating})")
    print(f"Total flight cost: {result.flight_cost_total} {currency}")
    print(f"Total hotel cost: {result.hotel_cost_total} {currency}")
    print(f"Remaining daily budget: {result.remaining_daily_budget} {currency}")
    print(f"Feasible: {result.feasible}")
    if result.feasibility_note:
        print(f"Note: {result.feasibility_note}")
