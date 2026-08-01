"""
Mock flight search. Generates deterministic, realistic-looking flight
options based on origin/destination/date so responses are stable across
calls (useful for testing) but still vary by route.

Supports multiple currencies with realistic native price ranges (not just
a naive USD conversion) — e.g. domestic India flights are priced like
real INR domestic fares, not a dollar figure with a rupee symbol slapped on.

Swap this module out for a real provider (Amadeus, Skyscanner) later
without touching any agent code, as long as the response shape matches
`FlightOption` in app.schemas.state.
"""
import hashlib

AIRLINES_BY_CURRENCY = {
    "USD": ["SkyBridge Air", "Meridian Airlines", "Northwind Air", "Vantage Airways", "Cobalt Air"],
    "INR": ["IndiGo", "Air India", "Vistara", "SpiceJet", "Akasa Air"],
    "EUR": ["EuroWing", "Continental Air", "Nordic Airways", "Alpine Air", "Meridian Airlines"],
    "GBP": ["BritAir", "Isles Airways", "Meridian Airlines", "Northwind Air", "Cobalt Air"],
}

# Base price ranges are currency-native, not converted — reflects realistic
# fares in that market rather than a USD number with a different symbol.
BASE_PRICE_RANGE = {
    "USD": (150, 500),
    "INR": (3000, 9000),   # realistic domestic/regional India fares
    "EUR": (120, 450),
    "GBP": (100, 400),
}

# Cabin class multipliers on top of the economy base price — roughly
# reflects real-world fare ratios between cabins.
CABIN_CLASS_MULTIPLIER = {
    "economy": 1.0,
    "premium_economy": 1.6,
    "business": 3.2,
    "first": 5.5,
}


def _seeded_rng(seed_str: str):
    """Small deterministic pseudo-random generator so the same route+date
    always returns the same options (no external randomness dependency)."""
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)

    def rand(n_calls: int) -> float:
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        return (seed % 10000) / 10000

    return rand


def search_flights(
    origin: str, destination: str, date: str, currency: str = "USD", cabin_class: str = "economy"
) -> list[dict]:
    currency = currency.upper()
    cabin_class = cabin_class.lower()
    airlines = AIRLINES_BY_CURRENCY.get(currency, AIRLINES_BY_CURRENCY["USD"])
    low, high = BASE_PRICE_RANGE.get(currency, BASE_PRICE_RANGE["USD"])
    multiplier = CABIN_CLASS_MULTIPLIER.get(cabin_class, 1.0)

    rand = _seeded_rng(f"{origin}-{destination}-{date}-{currency}")
    options = []

    for i in range(4):
        r = rand(i)
        stops = 0 if r < 0.35 else (1 if r < 0.8 else 2)
        base = low + (high - low) * r
        stop_surcharge_ratio = 0.3  # each stop adds ~30% of the base range
        economy_price = base + stops * (high - low) * stop_surcharge_ratio
        price = round(economy_price * multiplier, 2)
        depart_hour = 6 + int(r * 16)
        flight_duration_hours = 2 + stops * 2 + int(r * 6)
        arrive_hour = (depart_hour + flight_duration_hours) % 24

        options.append({
            "airline": airlines[i % len(airlines)],
            "price": price,
            "depart_time": f"{depart_hour:02d}:00",
            "arrive_time": f"{arrive_hour:02d}:00",
            "stops": stops,
            "cabin_class": cabin_class,
        })

    return sorted(options, key=lambda f: f["price"])
