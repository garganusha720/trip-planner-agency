"""
Mock hotel search. Same deterministic-seed approach as flights.py, with
currency-native price ranges rather than a naive USD conversion.
"""
import hashlib

HOTEL_NAME_PARTS_BY_CURRENCY = {
    "USD": [("The Wren", "Grand Meridian"), ("Harbor House", "City Central Inn"),
            ("The Linden", "Parkview Suites"), ("Old Town Lodge", "Skyline Residence")],
    "INR": [("Hotel Ganges View", "The Royal Rajwada"), ("City Comfort Inn", "Heritage Haveli"),
            ("The Metro Residency", "Palm Grove Resort"), ("Sunrise Lodge", "Taj Vista Inn")],
    "EUR": [("Hotel Alpina", "Grand Continental"), ("Riverside Inn", "Old Quarter Suites"),
            ("The Linden", "Parkview Suites"), ("Boutique Nordic", "Central Plaza")],
    "GBP": [("The Kensington", "Royal Crescent Inn"), ("Harbor House", "City Central Inn"),
            ("The Linden", "Parkview Suites"), ("Old Town Lodge", "Isles View Hotel")],
}
NEIGHBORHOODS = ["Old Town", "Downtown", "Riverside", "Arts District", "Near Airport"]

# Currency-native nightly price ranges.
NIGHTLY_PRICE_RANGE = {
    "USD": (40, 300),
    "INR": (1200, 8000),   # realistic budget-to-upscale India hotel range
    "EUR": (35, 280),
    "GBP": (35, 260),
}


def _seeded_rng(seed_str: str):
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)

    def rand(n_calls: int) -> float:
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        return (seed % 10000) / 10000

    return rand


def search_hotels(
    city: str,
    nightly_budget: float | None = None,
    currency: str = "USD",
    min_rating: float = 0.0,
) -> list[dict]:
    currency = currency.upper()
    name_parts = HOTEL_NAME_PARTS_BY_CURRENCY.get(currency, HOTEL_NAME_PARTS_BY_CURRENCY["USD"])
    low, high = NIGHTLY_PRICE_RANGE.get(currency, NIGHTLY_PRICE_RANGE["USD"])

    rand = _seeded_rng(f"hotels-{city}-{currency}")
    options = []

    for i in range(5):
        r = rand(i)
        tier_price = low + (high - low) * r
        rating = round(3.2 + r * 1.7, 1)
        name = name_parts[i % len(name_parts)][i % 2]

        options.append({
            "name": f"{name} {city.title()}" if i % 2 == 0 else name,
            "price_per_night": round(tier_price, 2),
            "rating": min(rating, 5.0),
            "neighborhood": NEIGHBORHOODS[i % len(NEIGHBORHOODS)],
        })

    if min_rating > 0:
        options = [h for h in options if h["rating"] >= min_rating]

    if nightly_budget is not None:
        options = [h for h in options if h["price_per_night"] <= nightly_budget * 1.15]

    return sorted(options, key=lambda h: h["price_per_night"])
