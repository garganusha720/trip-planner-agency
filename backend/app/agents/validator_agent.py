"""
Logistics Validator Agent.

Rule-based (no LLM) — checks a built itinerary for real scheduling
problems: overlapping time slots, and unrealistically tight gaps between
activities in different neighborhoods (no time to actually travel there).

Why rule-based: like the Budget Agent, this is deterministic logic, not
judgment. "Does 10:00-11:30 overlap with 11:00-12:00?" has one correct
answer — an LLM call here would just add latency and a chance of getting
simple arithmetic wrong.

Run standalone:
    python -m app.agents.validator_agent
    (runs against both a clean example and a deliberately broken one)
"""
from app.schemas.state import Conflict, ConflictType, Itinerary, ValidationResult

# Minimum minutes needed between the end of one activity and the start of
# the next, depending on whether they're in the same neighborhood or not.
# These are simple heuristics — swap in a real maps/distance API later for
# actual travel-time estimates without changing anything else downstream.
SAME_NEIGHBORHOOD_BUFFER_MIN = 10
DIFFERENT_NEIGHBORHOOD_BUFFER_MIN = 45


def _to_minutes(hhmm: str) -> int:
    """Convert 'HH:MM' to minutes since midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _same_area(neighborhood_a: str, neighborhood_b: str) -> bool:
    """Loosely compare neighborhoods — LLM-generated names are inconsistent
    (e.g. 'Alfama' vs 'Alfama/Castelo' for the same area), so treat one
    being a case-insensitive substring of the other as the same area rather
    than requiring an exact string match."""
    a, b = neighborhood_a.strip().lower(), neighborhood_b.strip().lower()
    return a == b or a in b or b in a


def validate_itinerary(itinerary: Itinerary) -> ValidationResult:
    conflicts: list[Conflict] = []

    for day in itinerary.days:
        # Sort by start time so we only need to compare each activity to
        # the one immediately after it, not every pair.
        sorted_activities = sorted(day.activities, key=lambda a: _to_minutes(a.start_time))

        for current, nxt in zip(sorted_activities, sorted_activities[1:]):
            current_end = _to_minutes(current.end_time)
            next_start = _to_minutes(nxt.start_time)
            gap = next_start - current_end

            if gap < 0:
                conflicts.append(Conflict(
                    day_number=day.day_number,
                    conflict_type=ConflictType.TIME_OVERLAP,
                    detail=(
                        f"'{current.name}' ({current.start_time}-{current.end_time}) overlaps "
                        f"with '{nxt.name}' ({nxt.start_time}-{nxt.end_time}) by {-gap} minutes."
                    ),
                    involved_activities=[current.name, nxt.name],
                ))
                continue  # don't also flag it as a travel-time issue

            same_neighborhood = _same_area(current.neighborhood, nxt.neighborhood)
            required_buffer = (
                SAME_NEIGHBORHOOD_BUFFER_MIN if same_neighborhood
                else DIFFERENT_NEIGHBORHOOD_BUFFER_MIN
            )

            if gap < required_buffer:
                conflicts.append(Conflict(
                    day_number=day.day_number,
                    conflict_type=ConflictType.UNREALISTIC_TRAVEL,
                    detail=(
                        f"Only {gap} minutes between '{current.name}' ending in "
                        f"{current.neighborhood} and '{nxt.name}' starting in "
                        f"{nxt.neighborhood} — needs at least {required_buffer} minutes."
                    ),
                    involved_activities=[current.name, nxt.name],
                ))

    if conflicts:
        return ValidationResult(status="conflict", conflicts=conflicts)
    return ValidationResult(status="ok", conflicts=[])


if __name__ == "__main__":
    from app.schemas.state import ItineraryDay, ScheduledActivity

    print("=== Testing against a CLEAN itinerary (should pass) ===\n")
    clean = Itinerary(
        destination="Lisbon, Portugal",
        days=[
            ItineraryDay(day_number=1, activities=[
                ScheduledActivity(name="Castelo de São Jorge", start_time="09:00", end_time="11:00",
                                   neighborhood="Alfama", category="landmark", est_cost=15),
                ScheduledActivity(name="Lisbon Cathedral", start_time="11:45", end_time="12:30",
                                   neighborhood="Alfama", category="history", est_cost=5),
            ]),
        ],
    )
    result = validate_itinerary(clean)
    print(f"Status: {result.status}, conflicts: {len(result.conflicts)}")

    print("\n=== Testing against a BROKEN itinerary (should catch both conflict types) ===\n")
    broken = Itinerary(
        destination="Lisbon, Portugal",
        days=[
            ItineraryDay(day_number=1, activities=[
                # Overlap: ends at 11:00, next starts at 10:30
                ScheduledActivity(name="Castelo de São Jorge", start_time="09:00", end_time="11:00",
                                   neighborhood="Alfama", category="landmark", est_cost=15),
                ScheduledActivity(name="Lisbon Cathedral", start_time="10:30", end_time="11:15",
                                   neighborhood="Alfama", category="history", est_cost=5),
                # Unrealistic travel: only 10 min to get across town to Belém
                ScheduledActivity(name="Jerónimos Monastery", start_time="11:25", end_time="12:30",
                                   neighborhood="Belém", category="history", est_cost=12),
            ]),
        ],
    )
    result = validate_itinerary(broken)
    print(f"Status: {result.status}, conflicts: {len(result.conflicts)}")
    for c in result.conflicts:
        print(f"  Day {c.day_number} [{c.conflict_type.value}]: {c.detail}")
