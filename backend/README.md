# Trip Planner — Phase 1 (Foundation)

This is the foundation layer for the AI Trip Planner Agency project: no LLM
agents yet, just the tools they'll call, working and tested on their own.

## What's here

```
backend/
  app/
    main.py              FastAPI app — mock flight/hotel endpoints
    mock_api/
      flights.py          Deterministic mock flight data generator
      hotels.py           Deterministic mock hotel data generator
    schemas/
      state.py            Shared Pydantic schema (TripState) all agents will use
    tools/
      search.py           Tavily web search wrapper (for the Research Agent, Phase 2)
  tests/
    checkpoint_phase1.py  Verifies everything above works end-to-end
  requirements.txt
  .env.example
```

## Setup

```bash
cd backend
pip install -r requirements.txt --break-system-packages   # or use a venv
cp .env.example .env
# then edit .env and add your real TAVILY_API_KEY
```

Get a free Tavily key at https://tavily.com (or swap in SerpAPI in
`app/tools/search.py` if you'd rather use that).

## Run it

Start the mock API:

```bash
uvicorn app.main:app --reload --port 8000
```

In another terminal, verify the checkpoint:

```bash
python -m tests.checkpoint_phase1
```

You should see:

```
=== Checking mock API ===
✓ /flights returned 4 options, cheapest: $277.95
✓ /hotels returned 2 options, cheapest: $48.76/night

=== Checking Tavily search tool ===
✓ Search returned 3 results
  First result: ...

=== Checking shared state schema ===
✓ TripState instantiates and serializes cleanly

Phase 1 checkpoint passed.
```

(If you haven't added a real Tavily key yet, that section will print a
skip warning instead of failing — that's expected.)

## Try the API directly

With the server running, visit `http://127.0.0.1:8000/docs` for Swagger UI,
or curl it directly:

```bash
curl "http://127.0.0.1:8000/flights?origin=JFK&destination=NRT&date=2026-09-10"
curl "http://127.0.0.1:8000/hotels?city=Tokyo&nightly_budget=150"
```

## Why the mock data is deterministic

Both `flights.py` and `hotels.py` seed their fake randomness from the
route/city string, so the same query always returns the same options.
This makes testing and demos predictable. When you're ready to go live,
swap these two files for real calls to Amadeus/Skyscanner — nothing else
in the pipeline needs to change, since the response shape stays the same.

## Next: Phase 2

Build the Destination Research Agent — one agent, one tool
(`app/tools/search.py`), structured JSON output. Test it standalone before
chaining it to anything else.
