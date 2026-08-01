"""
Destination Research Agent.

Given a destination, trip length, and interests, this agent uses the
web_search tool (Tavily) to gather real information, then returns a
structured `ResearchResult` (see app/schemas/state.py) — a list of
attractions with category, neighborhood, estimated visit time, etc.

Uses Google's Gemini API — free tier, no card required. Get a key at
https://aistudio.google.com ("Get API key" button) and put it in
backend/.env as GEMINI_API_KEY.

Run standalone:
    python -m app.agents.research_agent "Tokyo" "food,history" 5
    python -m app.agents.research_agent "Jaipur" "history,food" 4 3 INR
"""
import json
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.schemas.state import ResearchResult
from app.tools.search import web_search as _raw_web_search

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Check aistudio.google.com for current free-tier model options if this
# stops working.
MODEL = "gemini-3.5-flash-lite"

MAX_TOOL_CALLS = 5

SYSTEM_PROMPT_TEMPLATE = """You are a destination research agent for a trip-planning system.

Given a destination, trip length, and traveler interests, research real
attractions using the web_search tool. Run 2-4 targeted searches covering
different angles (e.g. top sights, neighborhood guides, food, hidden gems
related to the stated interests) before answering — keep queries specific
so each search counts.

IMPORTANT: All prices/costs you report must be realistic amounts in {currency}
for this destination — not converted from another currency, actual native
{currency} prices as a local or regional traveler would see them.

When you have enough information, respond with ONLY a single JSON object
(no markdown fences, no commentary before or after) matching this exact shape:

{{
  "destination": "<string>",
  "currency": "{currency}",
  "best_time_to_visit": "<string or null>",
  "attractions": [
    {{
      "name": "<string>",
      "category": "<one of: museum, food, nature, nightlife, history, shopping, landmark>",
      "neighborhood": "<string>",
      "avg_visit_minutes": <integer>,
      "est_cost": <number, in {currency}>,
      "opening_hours": "<string, e.g. '09:00-18:00' or 'closed Mondays'>",
      "notes": "<string or null>"
    }}
  ],
  "local_tips": ["<string>", "..."]
}}

Include 8-15 attractions covering a mix of the traveler's stated interests.
Only include facts you found via search — do not invent opening hours or
prices you're unsure about; use reasonable estimates and say so in notes
if you're estimating.
"""


def web_search(query: str) -> str:
    """Search the web for current, specific information about a travel
    destination — attractions, neighborhoods, opening hours, local tips.

    Args:
        query: A specific search query, e.g. 'best museums in Kyoto for history lovers'

    Returns:
        JSON string of search results (titles, urls, short content snippets).
    """
    print(f"  [research agent] searching: {query}")
    try:
        result = _raw_web_search(query, max_results=3)
        # Trim aggressively — keeps token usage well under free-tier limits
        # regardless of provider, and speeds up responses too.
        trimmed = {
            "query": result["query"],
            "results": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": (r.get("content") or "")[:250],
                }
                for r in result.get("results", [])
            ],
        }
        return json.dumps(trimmed)
    except Exception as e:
        return json.dumps({"error": str(e)})


WEB_SEARCH_DECLARATION = types.FunctionDeclaration(
    name="web_search",
    description=(
        "Search the web for current, specific information about a travel "
        "destination — attractions, neighborhoods, opening hours, local tips."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "query": types.Schema(
                type="STRING",
                description="A specific search query, e.g. 'best museums in Kyoto for history lovers'",
            )
        },
        required=["query"],
    ),
)


def _extract_function_calls(response):
    """Return list of function_call parts from a response, or [] if none."""
    if not response.candidates:
        return []
    parts = response.candidates[0].content.parts or []
    return [p.function_call for p in parts if getattr(p, "function_call", None)]


def research_destination(
    destination: str, interests: list[str], trip_length_days: int, currency: str = "USD"
) -> ResearchResult:
    currency = currency.upper()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(currency=currency)

    user_message = (
        f"Research {destination} for a {trip_length_days}-day trip. "
        f"Traveler interests: {', '.join(interests) if interests else 'general sightseeing'}."
    )

    # Manual chat loop (rather than automatic function calling) so we have
    # explicit control over convergence: we keep exchanging tool calls for
    # tool results until the model stops calling tools and gives us text,
    # and we can force a final answer if it runs long.
    chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[types.Tool(function_declarations=[WEB_SEARCH_DECLARATION])],
        ),
    )

    response = chat.send_message(user_message)

    for i in range(MAX_TOOL_CALLS):
        function_calls = _extract_function_calls(response)
        if not function_calls:
            break  # model gave a final text answer

        response_parts = []
        for fc in function_calls:
            query = fc.args.get("query", "")
            result_json = web_search(query)
            # Gemini 3.x models require the function response to echo back
            # the call's id (not just its name) so it can be matched to the
            # correct call, especially when multiple calls happen in one turn.
            response_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        id=fc.id,
                        name=fc.name,
                        response={"result": result_json},
                    )
                )
            )

        # On the last allowed iteration, tell it explicitly to stop searching.
        if i == MAX_TOOL_CALLS - 2:
            response_parts.append(
                types.Part.from_text(
                    text="You've done enough research. Respond now with ONLY the final JSON object, no more tool calls."
                )
            )

        response = chat.send_message(response_parts)
    else:
        raise RuntimeError(f"Research agent did not converge after {MAX_TOOL_CALLS} tool-call rounds")

    text = (response.text or "").strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    if not text:
        raise RuntimeError(
            "Research agent returned no text — likely ended on an unresolved tool call. "
            "Try increasing MAX_TOOL_CALLS or simplifying the request."
        )

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Research agent did not return valid JSON.\nRaw output:\n{text}"
        ) from e

    return ResearchResult(**data)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print('Usage: python -m app.agents.research_agent "<destination>" "<interests,comma,separated>" <trip_length_days> [currency]')
        sys.exit(1)

    destination = sys.argv[1]
    interests = [i.strip() for i in sys.argv[2].split(",")]
    trip_length_days = int(sys.argv[3])
    currency = sys.argv[4] if len(sys.argv) > 4 else "USD"

    print(f"Researching {destination} ({trip_length_days} days, interests: {interests}, currency: {currency})...\n")
    result = research_destination(destination, interests, trip_length_days, currency)

    print(f"\n=== {result.destination} ===")
    print(f"Best time to visit: {result.best_time_to_visit}")
    print(f"\nFound {len(result.attractions)} attractions:")
    for a in result.attractions:
        print(f"  - {a.name} ({a.category}, {a.neighborhood}) — ~{a.avg_visit_minutes}min, {a.est_cost} {result.currency}")
    print(f"\nLocal tips:")
    for tip in result.local_tips:
        print(f"  - {tip}")
