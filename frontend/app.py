"""
Trip Planner Agency — Streamlit frontend.

A form that calls the FastAPI backend's /plan-trip endpoint and displays
the resulting itinerary, budget breakdown, and agent handoff trace
(retry count, validation status). Supports multiple currencies (USD,
INR, EUR, GBP) with correct native symbols throughout.

Run with:
    streamlit run app.py

Requires the backend running separately:
    uvicorn app.main:app --port 8000
"""
import requests
import streamlit as st

st.set_page_config(page_title="Trip Planner Agency", page_icon="\U0001F9F3", layout="centered")

BACKEND_URL = "http://127.0.0.1:8001"

CURRENCY_SYMBOLS = {"USD": "$", "INR": "\u20b9", "EUR": "\u20ac", "GBP": "\u00a3"}


def fmt(amount: float, currency: str) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency, currency + " ")
    return f"{symbol}{amount:,.2f}"


# ---------------------------------------------------------------------------
# Visual theme — deep navy + warm gold, a travel-document / passport-stamp
# feel rather than the generic cream-and-terracotta look. Streamlit is
# themed via injected CSS since it doesn't expose a full custom stylesheet.
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Inter:wght@400;500;600&display=swap');

:root {
    --ink: #0f2438;
    --ink-soft: #33506b;
    --gold: #c9973d;
    --gold-soft: #e8d5ab;
    --paper: #fbf9f4;
    --line: #d9d2c3;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: var(--paper); }

h1, h2, h3 { font-family: 'Fraunces', serif !important; color: var(--ink) !important; }

.stamp-header {
    display: flex;
    align-items: baseline;
    gap: 0.6rem;
    border-bottom: 3px double var(--gold);
    padding-bottom: 0.6rem;
    margin-bottom: 0.4rem;
}

.status-banner {
    border-left: 4px solid var(--gold);
    background: white;
    padding: 0.85rem 1.1rem;
    border-radius: 4px;
    margin: 0.6rem 0 1.2rem 0;
    font-size: 0.95rem;
}
.status-banner.warn { border-left-color: #b5502e; }

.day-card {
    background: white;
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.9rem;
}
.day-card .day-label {
    font-family: 'Fraunces', serif;
    font-weight: 700;
    color: var(--gold);
    font-size: 0.85rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.activity-row {
    display: flex;
    gap: 0.9rem;
    padding: 0.35rem 0;
    border-bottom: 1px solid #f0ede4;
    font-size: 0.93rem;
}
.activity-row:last-child { border-bottom: none; }
.activity-time {
    color: var(--ink-soft);
    font-variant-numeric: tabular-nums;
    min-width: 108px;
    font-weight: 500;
}
.activity-meta { color: #8a8371; font-size: 0.85rem; }

.stButton > button {
    background: var(--ink) !important;
    color: white !important;
    border-radius: 4px !important;
    border: none !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
}
.stButton > button:hover { background: var(--gold) !important; color: var(--ink) !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="stamp-header">
    <span style="font-family:'Fraunces',serif; font-weight:700; font-size:1.9rem;">Trip Planner Agency</span>
</div>
<div style="color:#c9973d; font-family:'Inter',sans-serif; letter-spacing:0.18em; font-size:0.72rem; font-weight:600; text-transform:uppercase; margin-bottom:1.2rem;">
    Research &middot; Budget &middot; Itinerary &middot; Logistics Validator — orchestrated end to end
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Input form
# ---------------------------------------------------------------------------

with st.form("trip_form"):
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input("Origin (airport/city code)", value="JFK")
        destination = st.text_input("Destination", value="Lisbon")
        start_date = st.date_input("Start date").isoformat()
        cabin_class = st.selectbox(
            "Flight class",
            options=["economy", "premium_economy", "business", "first"],
            format_func=lambda c: c.replace("_", " ").title(),
        )
    with col2:
        trip_length_days = st.number_input("Trip length (days)", min_value=1, max_value=14, value=3)
        currency = st.selectbox("Currency", options=["USD", "INR", "EUR", "GBP"], index=0)
        total_budget = st.number_input(f"Total budget ({currency})", min_value=50, value=1200, step=50)
        hotel_min_rating = st.selectbox(
            "Minimum hotel rating",
            options=[0.0, 3.0, 3.5, 4.0, 4.5],
            format_func=lambda r: "Any" if r == 0 else f"{r}+ stars",
        )

    interests_input = st.text_input(
        "Interests (comma-separated)", value="food, history",
        help="e.g. food, history, nightlife, nature, shopping",
    )

    submitted = st.form_submit_button("Plan my trip", use_container_width=True)

# ---------------------------------------------------------------------------
# Call the backend and render results
# ---------------------------------------------------------------------------

if submitted:
    interests = [i.strip() for i in interests_input.split(",") if i.strip()]

    payload = {
        "origin": origin,
        "destination": destination,
        "start_date": start_date,
        "trip_length_days": int(trip_length_days),
        "total_budget": float(total_budget),
        "currency": currency,
        "interests": interests,
        "cabin_class": cabin_class,
        "hotel_min_rating": float(hotel_min_rating),
    }

    with st.spinner("Planning your trip — this runs several AI agents and can take up to a minute..."):
        try:
            response = requests.post(f"{BACKEND_URL}/plan-trip", json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.ConnectionError:
            st.error(
                f"Couldn't reach the backend at {BACKEND_URL}. "
                f"Make sure it's running: `uvicorn app.main:app --port 8000`"
            )
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"Backend returned an error: {e}")
            st.stop()

    result_currency = result["budget"].get("currency", currency)

    # --- Agent trace summary ---
    validation = result["validation"]
    retry_count = result["retry_count"]

    if validation["status"] == "ok" and retry_count == 0:
        st.markdown(
            '<div class="status-banner">✅ Itinerary built clean on the first attempt — '
            'no scheduling conflicts.</div>', unsafe_allow_html=True,
        )
    elif validation["status"] == "ok" and retry_count > 0:
        st.markdown(
            f'<div class="status-banner">✅ Itinerary built after {retry_count} retry(ies) — '
            f'the validator caught a conflict and the itinerary agent fixed it.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="status-banner warn">⚠️ Gave up after {retry_count} retries — the '
            f'itinerary below still has unresolved conflicts (shown below).</div>',
            unsafe_allow_html=True,
        )

    for note in result.get("final_notes", []):
        st.info(note)

    # --- Budget summary ---
    budget = result["budget"]
    st.subheader("Budget")
    b1, b2, b3 = st.columns(3)
    flight_class_label = budget['chosen_flight']['cabin_class'].replace('_', ' ').title()
    b1.metric("Flight", fmt(budget["flight_cost_total"], result_currency),
              f"{budget['chosen_flight']['airline']} · {flight_class_label} ({budget['chosen_flight']['stops']} stops)")
    b2.metric("Hotel (total)", fmt(budget["hotel_cost_total"], result_currency),
              f"{budget['chosen_hotel']['name']} · {budget['chosen_hotel']['rating']}★")
    b3.metric("Daily budget left", f"{fmt(budget['remaining_daily_budget'], result_currency)}/day")

    if not budget["feasible"]:
        st.error(f"Over budget: {budget.get('feasibility_note', '')}")
    elif budget.get("feasibility_note"):
        st.caption(f"ℹ️ {budget['feasibility_note']}")

    # --- Itinerary ---
    itinerary = result["itinerary"]
    st.subheader(f"Itinerary — {itinerary['destination']}")

    for day in itinerary["days"]:
        activities_html = "".join(
            f'<div class="activity-row">'
            f'<span class="activity-time">{a["start_time"]}–{a["end_time"]}</span>'
            f'<span>{a["name"]} <span class="activity-meta">'
            f'({a["neighborhood"]}, {fmt(a["est_cost"], result_currency)})</span></span>'
            f'</div>'
            for a in day["activities"]
        )
        st.markdown(
            f'<div class="day-card"><div class="day-label">Day {day["day_number"]}</div>'
            f'{activities_html}</div>',
            unsafe_allow_html=True,
        )

    # --- Validation details, if any conflicts remain ---
    if validation["conflicts"]:
        st.subheader("Unresolved conflicts")
        for c in validation["conflicts"]:
            st.markdown(f"- **Day {c['day_number']}** [{c['conflict_type']}]: {c['detail']}")

    # --- Research notes ---
    research = result["research"]
    if research.get("local_tips"):
        st.subheader("Local tips")
        for tip in research["local_tips"]:
            st.markdown(f"- {tip}")

    if research.get("best_time_to_visit"):
        st.caption(f"Best time to visit: {research['best_time_to_visit']}")
