"""
Shared state schema for the trip planner agency.

Every agent reads from and writes to a `TripState`. Keeping this in one
place means each agent's contract is explicit: what it expects to find
filled in, and what field it's responsible for filling in next.

Currency: cost fields are named generically (est_cost, price, etc. — not
est_cost_usd) since the same schema is used for USD, INR, or any other
currency. Check the `currency` field alongside any cost to know the unit.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

SUPPORTED_CURRENCIES = {"USD": "$", "INR": "\u20b9", "EUR": "\u20ac", "GBP": "\u00a3"}


def currency_symbol(currency: str) -> str:
    return SUPPORTED_CURRENCIES.get(currency.upper(), currency.upper() + " ")


# ---------------------------------------------------------------------------
# Research Agent output
# ---------------------------------------------------------------------------

class Attraction(BaseModel):
    name: str
    category: str  # e.g. "museum", "food", "nature", "nightlife", "history"
    neighborhood: str
    avg_visit_minutes: int = Field(..., description="Typical time to spend here, in minutes")
    est_cost: float = 0.0
    opening_hours: str = Field(
        default="09:00-18:00",
        description="Simplified daily hours, e.g. '09:00-18:00' or 'closed Mondays'",
    )
    notes: Optional[str] = None


class ResearchResult(BaseModel):
    destination: str
    currency: str = "USD"
    best_time_to_visit: Optional[str] = None
    attractions: list[Attraction] = Field(default_factory=list)
    local_tips: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Budget & Flights Agent output
# ---------------------------------------------------------------------------

class FlightOption(BaseModel):
    airline: str
    price: float
    depart_time: str
    arrive_time: str
    stops: int
    cabin_class: str = "economy"


class HotelOption(BaseModel):
    name: str
    price_per_night: float
    rating: float
    neighborhood: str


class BudgetResult(BaseModel):
    currency: str = "USD"
    total_budget: float
    chosen_flight: Optional[FlightOption] = None
    chosen_hotel: Optional[HotelOption] = None
    trip_length_days: int
    flight_cost_total: float = 0.0
    hotel_cost_total: float = 0.0
    remaining_daily_budget: float = 0.0
    feasible: bool = True
    feasibility_note: Optional[str] = None


# ---------------------------------------------------------------------------
# Itinerary Builder Agent output
# ---------------------------------------------------------------------------

class ScheduledActivity(BaseModel):
    name: str
    start_time: str  # "HH:MM"
    end_time: str    # "HH:MM"
    neighborhood: str
    category: str
    est_cost: float = 0.0


class ItineraryDay(BaseModel):
    day_number: int
    activities: list[ScheduledActivity] = Field(default_factory=list)


class Itinerary(BaseModel):
    destination: str
    currency: str = "USD"
    days: list[ItineraryDay] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Logistics Validator Agent output
# ---------------------------------------------------------------------------

class ConflictType(str, Enum):
    TIME_OVERLAP = "time_overlap"
    UNREALISTIC_TRAVEL = "unrealistic_travel"
    CLOSED_VENUE = "closed_venue"


class Conflict(BaseModel):
    day_number: int
    conflict_type: ConflictType
    detail: str
    involved_activities: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    status: str  # "ok" | "conflict"
    conflicts: list[Conflict] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# The full shared state passed through the graph
# ---------------------------------------------------------------------------

class TripRequest(BaseModel):
    origin: str
    destination: str
    start_date: str
    trip_length_days: int
    total_budget: float
    currency: str = Field(default="USD", description="e.g. USD, INR, EUR, GBP")
    interests: list[str] = Field(default_factory=list)
    hotel_min_rating: float = Field(
        default=0.0, ge=0.0, le=5.0,
        description="Minimum acceptable hotel star rating (0 = any)",
    )
    cabin_class: str = Field(
        default="economy",
        description="economy, premium_economy, business, or first",
    )


class TripState(BaseModel):
    request: TripRequest
    research: Optional[ResearchResult] = None
    budget: Optional[BudgetResult] = None
    itinerary: Optional[Itinerary] = None
    validation: Optional[ValidationResult] = None
    retry_count: int = 0
    max_retries: int = 3
    conflicts_to_fix: list[str] = Field(default_factory=list)
    final_notes: list[str] = Field(default_factory=list)
