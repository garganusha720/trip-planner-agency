"""
Phase 4a checkpoint script.

Tests the Validator Agent standalone against clean and broken itineraries,
and against a real itinerary produced by the full Research -> Budget ->
Itinerary chain from Phase 3.

Requires the mock API running: uvicorn app.main:app --port 8000

    python -m tests.checkpoint_phase4a
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def check_validator_catches_conflicts():
    print("=== Checking validator catches deliberate conflicts ===\n")
    from app.schemas.state import Itinerary, ItineraryDay, ScheduledActivity
    from app.agents.validator_agent import validate_itinerary

    broken = Itinerary(
        destination="Test City",
        days=[
            ItineraryDay(day_number=1, activities=[
                ScheduledActivity(name="A", start_time="09:00", end_time="11:00",
                                   neighborhood="Downtown", category="museum", est_cost_usd=10),
                ScheduledActivity(name="B", start_time="10:30", end_time="11:15",
                                   neighborhood="Downtown", category="food", est_cost_usd=10),
                ScheduledActivity(name="C", start_time="11:25", end_time="12:30",
                                   neighborhood="Uptown", category="history", est_cost_usd=10),
            ]),
        ],
    )
    result = validate_itinerary(broken)
    assert result.status == "conflict", "Expected conflicts to be found"
    assert len(result.conflicts) == 2, f"Expected 2 conflicts, got {len(result.conflicts)}"
    print(f"✓ Correctly found {len(result.conflicts)} conflicts")
    for c in result.conflicts:
        print(f"  - [{c.conflict_type.value}] {c.detail}")


def check_validator_passes_clean():
    print("\n=== Checking validator passes a clean itinerary ===\n")
    from app.schemas.state import Itinerary, ItineraryDay, ScheduledActivity
    from app.agents.validator_agent import validate_itinerary

    clean = Itinerary(
        destination="Test City",
        days=[
            ItineraryDay(day_number=1, activities=[
                ScheduledActivity(name="A", start_time="09:00", end_time="11:00",
                                   neighborhood="Downtown", category="museum", est_cost_usd=10),
                ScheduledActivity(name="B", start_time="11:30", end_time="12:30",
                                   neighborhood="Downtown", category="food", est_cost_usd=10),
            ]),
        ],
    )
    result = validate_itinerary(clean)
    assert result.status == "ok", f"Expected no conflicts, got {result.conflicts}"
    print("✓ Clean itinerary correctly passed with no conflicts")


def check_validator_against_real_chain():
    print("\n=== Checking validator against a real generated itinerary ===\n")
    from app.agents.research_agent import research_destination
    from app.agents.budget_agent import get_budget
    from app.agents.itinerary_agent import build_itinerary
    from app.agents.validator_agent import validate_itinerary

    trip_length_days = 3
    research = research_destination(
        destination="Lisbon", interests=["food", "history"], trip_length_days=trip_length_days,
    )
    budget = get_budget(
        origin="JFK", destination=research.destination, start_date="2026-09-10",
        trip_length_days=trip_length_days, total_budget_usd=1200,
    )
    itinerary = build_itinerary(research, budget, trip_length_days=trip_length_days)
    result = validate_itinerary(itinerary)

    print(f"✓ Validated real itinerary: status = {result.status}")
    if result.conflicts:
        for c in result.conflicts:
            print(f"  - Day {c.day_number} [{c.conflict_type.value}]: {c.detail}")
    else:
        print("  (No conflicts — the LLM-built itinerary was already clean)")


if __name__ == "__main__":
    check_validator_catches_conflicts()
    check_validator_passes_clean()
    check_validator_against_real_chain()
    print("\nPhase 4a checkpoint passed.")
