"""
Phase 3 checkpoint script.

Tests the Budget Agent standalone, then chains Research -> Budget to
confirm data flows cleanly between agents (the core of "sequential
pipeline" for this project).

Requires the mock API running: uvicorn app.main:app --port 8000

    python -m tests.checkpoint_phase3
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def check_budget_agent():
    print("=== Checking Budget Agent (standalone) ===\n")
    from app.agents.budget_agent import get_budget

    result = get_budget(
        origin="JFK", destination="Lisbon", start_date="2026-09-10",
        trip_length_days=5, total_budget_usd=1500,
    )

    assert result.chosen_flight is not None, "No flight was chosen"
    assert result.chosen_hotel is not None, "No hotel was chosen"
    assert result.flight_cost_total > 0, "Flight cost should be positive"
    assert result.hotel_cost_total > 0, "Hotel cost should be positive"

    print(f"✓ Chose flight: {result.chosen_flight.airline} @ ${result.chosen_flight.price_usd}")
    print(f"✓ Chose hotel: {result.chosen_hotel.name} @ ${result.chosen_hotel.price_per_night_usd}/night")
    print(f"✓ Feasible: {result.feasible}, remaining daily budget: ${result.remaining_daily_budget}")

    # Also sanity-check the infeasible path doesn't crash and reports correctly
    tight_result = get_budget(
        origin="JFK", destination="Lisbon", start_date="2026-09-10",
        trip_length_days=5, total_budget_usd=200,
    )
    assert tight_result.feasible is False, "Expected infeasible result for a $200 budget"
    assert tight_result.feasibility_note is not None
    print(f"✓ Infeasible case correctly flagged: {tight_result.feasibility_note[:60]}...")


def check_research_to_budget_chain():
    print("\n=== Checking Research -> Budget chain ===\n")
    from app.agents.research_agent import research_destination
    from app.agents.budget_agent import get_budget

    research = research_destination(
        destination="Lisbon", interests=["food", "history"], trip_length_days=3,
    )
    budget = get_budget(
        origin="JFK", destination=research.destination, start_date="2026-09-10",
        trip_length_days=3, total_budget_usd=1200,
    )

    assert research.destination
    assert budget.chosen_flight is not None
    print(f"✓ Research found {len(research.attractions)} attractions for {research.destination}")
    print(f"✓ Budget agent priced the same destination: ${budget.flight_cost_total + budget.hotel_cost_total} total")
    print(f"✓ Data flowed cleanly from Research Agent's output into Budget Agent's input")


def check_full_chain():
    print("\n=== Checking full chain: Research -> Budget -> Itinerary ===\n")
    from app.agents.research_agent import research_destination
    from app.agents.budget_agent import get_budget
    from app.agents.itinerary_agent import build_itinerary

    trip_length_days = 3

    research = research_destination(
        destination="Lisbon", interests=["food", "history"], trip_length_days=trip_length_days,
    )
    budget = get_budget(
        origin="JFK", destination=research.destination, start_date="2026-09-10",
        trip_length_days=trip_length_days, total_budget_usd=1200,
    )
    itinerary = build_itinerary(research, budget, trip_length_days=trip_length_days)

    assert len(itinerary.days) == trip_length_days, (
        f"Expected {trip_length_days} days, got {len(itinerary.days)}"
    )
    total_activities = sum(len(d.activities) for d in itinerary.days)
    assert total_activities > 0, "Itinerary has no activities scheduled"

    print(f"✓ Itinerary built for {itinerary.destination}: "
          f"{len(itinerary.days)} days, {total_activities} activities total")
    for day in itinerary.days:
        names = ", ".join(a.name for a in day.activities)
        print(f"  Day {day.day_number}: {names}")


if __name__ == "__main__":
    check_budget_agent()
    check_research_to_budget_chain()
    check_full_chain()
    print("\nPhase 3 checkpoint passed.")
