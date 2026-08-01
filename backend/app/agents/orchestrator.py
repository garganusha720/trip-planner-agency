"""
Orchestrator: wires Research -> Budget -> Itinerary -> Validator into a
LangGraph state graph with a conditional feedback loop.

This is the piece that turns a fixed pipeline into a real "agency": if the
Validator finds conflicts, the graph routes back to the Itinerary Agent
with the specific problems to fix, re-plans, and re-validates — up to
`max_retries` times before giving up and returning the best attempt with
a caveat.

Run standalone:
    python -m app.agents.orchestrator "Lisbon" "food,history" 3 "JFK" "2026-09-10" 1200
    python -m app.agents.orchestrator "Jaipur" "history,food" 4 "DEL" "2026-11-15" 15000 INR
"""
import sys

from langgraph.graph import END, StateGraph

from app.agents.budget_agent import get_budget
from app.agents.itinerary_agent import build_itinerary
from app.agents.research_agent import research_destination
from app.agents.validator_agent import validate_itinerary
from app.schemas.state import TripRequest, TripState


# ---------------------------------------------------------------------------
# Node functions — each takes the full state and returns a dict of the
# fields it changed. LangGraph merges these into the state automatically.
# ---------------------------------------------------------------------------

def research_node(state: TripState) -> dict:
    print(f"\n[orchestrator] -> research_agent: researching {state.request.destination}")
    research = research_destination(
        destination=state.request.destination,
        interests=state.request.interests,
        trip_length_days=state.request.trip_length_days,
        currency=state.request.currency,
    )
    print(f"[orchestrator] <- research_agent: found {len(research.attractions)} attractions")
    return {"research": research}


def budget_node(state: TripState) -> dict:
    print(f"[orchestrator] -> budget_agent: pricing {state.request.origin} -> {state.request.destination} "
          f"({state.request.cabin_class}, {state.request.hotel_min_rating}+ stars)")
    budget = get_budget(
        origin=state.request.origin,
        destination=state.request.destination,
        start_date=state.request.start_date,
        trip_length_days=state.request.trip_length_days,
        total_budget=state.request.total_budget,
        currency=state.request.currency,
        cabin_class=state.request.cabin_class,
        hotel_min_rating=state.request.hotel_min_rating,
    )
    print(f"[orchestrator] <- budget_agent: feasible={budget.feasible}, "
          f"daily budget={budget.remaining_daily_budget} {budget.currency}")
    return {"budget": budget}


def itinerary_node(state: TripState) -> dict:
    attempt = state.retry_count + 1
    print(f"[orchestrator] -> itinerary_agent: building schedule (attempt {attempt})")
    if state.conflicts_to_fix:
        print(f"[orchestrator]    fixing {len(state.conflicts_to_fix)} conflict(s) from previous attempt")

    itinerary = build_itinerary(
        research=state.research,
        budget=state.budget,
        trip_length_days=state.request.trip_length_days,
        conflicts_to_fix=state.conflicts_to_fix or None,
    )
    print(f"[orchestrator] <- itinerary_agent: built {len(itinerary.days)}-day schedule")
    return {"itinerary": itinerary}


def validator_node(state: TripState) -> dict:
    print(f"[orchestrator] -> validator_agent: checking for conflicts")
    validation = validate_itinerary(state.itinerary)

    if validation.status == "conflict":
        print(f"[orchestrator] <- validator_agent: found {len(validation.conflicts)} conflict(s)")
        for c in validation.conflicts:
            print(f"                 - Day {c.day_number} [{c.conflict_type.value}]: {c.detail}")
        return {
            "validation": validation,
            "retry_count": state.retry_count + 1,
            "conflicts_to_fix": [c.detail for c in validation.conflicts],
        }

    print(f"[orchestrator] <- validator_agent: clean, no conflicts")
    return {"validation": validation}


def route_after_validation(state: TripState) -> str:
    """The conditional edge: this is the actual agent-handoff decision."""
    if state.validation.status == "ok":
        return "done"
    if state.retry_count >= state.max_retries:
        return "give_up"
    return "retry"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(TripState)

    graph.add_node("research", research_node)
    graph.add_node("budget", budget_node)
    graph.add_node("itinerary", itinerary_node)
    graph.add_node("validator", validator_node)

    graph.set_entry_point("research")
    graph.add_edge("research", "budget")
    graph.add_edge("budget", "itinerary")
    graph.add_edge("itinerary", "validator")

    # The conditional edge: this is what makes it a graph instead of a
    # straight line. On conflict, loop back to itinerary with the specific
    # problems to fix; otherwise stop (success or out of retries).
    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "retry": "itinerary",
            "done": END,
            "give_up": END,
        },
    )

    return graph.compile()


def plan_trip(
    origin: str,
    destination: str,
    start_date: str,
    trip_length_days: int,
    total_budget: float,
    interests: list[str],
    currency: str = "USD",
    cabin_class: str = "economy",
    hotel_min_rating: float = 0.0,
) -> TripState:
    app = build_graph()
    request = TripRequest(
        origin=origin, destination=destination, start_date=start_date,
        trip_length_days=trip_length_days, total_budget=total_budget,
        currency=currency, interests=interests,
        cabin_class=cabin_class, hotel_min_rating=hotel_min_rating,
    )
    final_state_dict = app.invoke(TripState(request=request))
    final_state = TripState(**final_state_dict)

    if final_state.validation and final_state.validation.status == "conflict":
        final_state.final_notes.append(
            f"Gave up after {final_state.retry_count} retries — itinerary still has "
            f"{len(final_state.validation.conflicts)} unresolved conflict(s). "
            f"Shown below is the best attempt."
        )

    return final_state


if __name__ == "__main__":
    if len(sys.argv) < 7:
        print('Usage: python -m app.agents.orchestrator "<destination>" "<interests,comma>" <days> "<origin>" "<start_date>" <budget> [currency]')
        sys.exit(1)

    destination = sys.argv[1]
    interests = [i.strip() for i in sys.argv[2].split(",")]
    trip_length_days = int(sys.argv[3])
    origin = sys.argv[4]
    start_date = sys.argv[5]
    total_budget = float(sys.argv[6])
    currency = sys.argv[7] if len(sys.argv) > 7 else "USD"

    result = plan_trip(
        origin=origin, destination=destination, start_date=start_date,
        trip_length_days=trip_length_days, total_budget=total_budget,
        interests=interests, currency=currency,
    )

    print(f"\n{'='*60}")
    print(f"FINAL ITINERARY: {result.itinerary.destination}")
    print(f"{'='*60}")
    print(f"Retries used: {result.retry_count}/{result.max_retries}")
    print(f"Final validation status: {result.validation.status}")
    for note in result.final_notes:
        print(f"NOTE: {note}")

    for day in result.itinerary.days:
        print(f"\nDay {day.day_number}:")
        for act in day.activities:
            print(f"  {act.start_time}-{act.end_time}  {act.name} ({act.neighborhood})")
