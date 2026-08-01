"""
Phase 2 checkpoint script.

Runs the Research Agent standalone on a small test destination and
validates that the output matches the ResearchResult schema.

    python -m tests.checkpoint_phase2
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def check_research_agent():
    print("=== Checking Research Agent ===\n")

    from app.agents.research_agent import research_destination

    result = research_destination(
        destination="Lisbon",
        interests=["food", "history"],
        trip_length_days=3,
    )

    assert result.destination, "destination field is empty"
    assert len(result.attractions) >= 3, f"Expected several attractions, got {len(result.attractions)}"

    for a in result.attractions:
        assert a.avg_visit_minutes > 0, f"{a.name} has invalid avg_visit_minutes"

    print(f"\n✓ Research agent returned {len(result.attractions)} attractions for {result.destination}")
    print(f"✓ All attractions have valid schema fields")

    categories = {a.category for a in result.attractions}
    print(f"✓ Categories covered: {', '.join(sorted(categories))}")


if __name__ == "__main__":
    check_research_agent()
    print("\nPhase 2 checkpoint passed.")
