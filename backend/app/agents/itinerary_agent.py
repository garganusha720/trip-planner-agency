"""
Itinerary Builder Agent.

Takes the Research Agent's attractions and the Budget Agent's remaining
daily budget, and produces a day-by-day schedule (`Itinerary` — see
app/schemas/state.py). This is an LLM agent (not rule-based) because
building a good schedule means genuine judgment calls: grouping nearby
attractions, balancing categories, respecting opening hours, and staying
under budget — a loose constraint-satisfaction problem that's exactly
the kind of thing an LLM handles better than hand-written rules.

No tool use here — everything it needs is already in the data passed in,
so it's a single reasoning call, not a search loop.

Uses Google's Gemini API (same key as the Research Agent).

Run standalone:
    python -m app.agents.itinerary_agent
    (uses a small hardcoded example — see __main__ block)
"""
import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.schemas.state import BudgetResult, Itinerary, ResearchResult

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash-lite"

SYSTEM_PROMPT_TEMPLATE = """You are an itinerary-building agent for a trip-planning system.

You'll be given:
- A list of researched attractions (name, category, neighborhood, average
  visit duration, cost, opening hours) — costs are in {currency}
- The trip length in days
- The remaining daily budget in {currency} (spending money per day, after flights/hotel)

Build a realistic day-by-day schedule. Rules to follow:
- Group activities by neighborhood where possible to minimize backtracking
- Don't schedule more than ~3-4 major activities per day; leave time for
  meals, rest, and travel between locations
- Respect each attraction's opening hours when picking start times
- Keep each day's total estimated cost under the remaining daily budget
  where possible — if you can't fit good options under budget, note it's
  tight rather than silently going over
- Vary categories across the trip (don't put 3 museums back to back)
- Start days around 09:00, end by ~21:00

Respond with ONLY a single JSON object (no markdown fences, no commentary)
matching this exact shape:

{{
  "destination": "<string>",
  "currency": "{currency}",
  "days": [
    {{
      "day_number": <integer>,
      "activities": [
        {{
          "name": "<string>",
          "start_time": "<HH:MM>",
          "end_time": "<HH:MM>",
          "neighborhood": "<string>",
          "category": "<string>",
          "est_cost": <number, in {currency}>
        }}
      ]
    }}
  ]
}}

Only use attractions from the provided list — do not invent new ones.
"""


def build_itinerary(
    research: ResearchResult,
    budget: BudgetResult,
    trip_length_days: int,
    conflicts_to_fix: list[str] | None = None,
) -> Itinerary:
    currency = budget.currency or research.currency or "USD"
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(currency=currency)

    attractions_json = json.dumps(
        [a.model_dump() for a in research.attractions], indent=2
    )

    conflict_note = ""
    if conflicts_to_fix:
        conflict_list = "\n".join(f"- {c}" for c in conflicts_to_fix)
        conflict_note = f"""

IMPORTANT: A previous version of this itinerary had these scheduling
problems — fix them this time (adjust timing, reorder, or swap which day
an activity falls on; don't just shift by a few minutes if the real issue
is neighborhood distance):
{conflict_list}
"""

    user_message = f"""Destination: {research.destination}
Trip length: {trip_length_days} days
Remaining daily budget: {budget.remaining_daily_budget} {currency}

Available attractions:
{attractions_json}
{conflict_note}
Build the day-by-day itinerary now."""

    response = client.models.generate_content(
        model=MODEL,
        contents=user_message,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )

    text = (response.text or "").strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    if not text:
        raise RuntimeError("Itinerary agent returned no text.")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Itinerary agent did not return valid JSON.\nRaw output:\n{text}"
        ) from e

    return Itinerary(**data)


if __name__ == "__main__":
    from app.schemas.state import Attraction

    example_research = ResearchResult(
        destination="Lisbon, Portugal",
        currency="USD",
        best_time_to_visit="Spring or fall",
        attractions=[
            Attraction(name="Jerónimos Monastery", category="history", neighborhood="Belém",
                       avg_visit_minutes=90, est_cost=12, opening_hours="10:00-17:30"),
            Attraction(name="Time Out Market", category="food", neighborhood="Cais do Sodré",
                       avg_visit_minutes=75, est_cost=25, opening_hours="10:00-24:00"),
            Attraction(name="Castelo de São Jorge", category="landmark", neighborhood="Alfama",
                       avg_visit_minutes=120, est_cost=15, opening_hours="09:00-21:00"),
        ],
        local_tips=["Buy a Lisboa Card for public transport + attraction discounts"],
    )
    example_budget = BudgetResult(
        currency="USD", total_budget=1500, trip_length_days=3, remaining_daily_budget=60,
    )

    result = build_itinerary(example_research, example_budget, trip_length_days=3)

    print(f"\n=== Itinerary for {result.destination} ===")
    for day in result.days:
        print(f"\nDay {day.day_number}:")
        for act in day.activities:
            print(f"  {act.start_time}-{act.end_time}  {act.name} ({act.neighborhood}, {act.est_cost} {result.currency})")
