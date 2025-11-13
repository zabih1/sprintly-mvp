#!/usr/bin/env python3
"""
Simple test script for the matching engine.
Run this to verify the scoring logic works correctly.
"""

from app.services.match_scorer import (
    calculate_match_factors,
    calculate_overall_match_score
)

# Mock Entity class for testing
class MockEntity:
    def __init__(self, sector_focus=None, stage_focus=None, location=None,
                 check_size_min=None, check_size_max=None):
        self.sector_focus = sector_focus or []
        self.stage_focus = stage_focus or []
        self.location = location
        self.check_size_min = check_size_min
        self.check_size_max = check_size_max

def test_sector_matching():
    """Test sector matching logic."""
    print("=== Testing Sector Matching ===")

    # Test entity with fintech focus
    entity = MockEntity(sector_focus=["Fintech", "Financial Services"])

    # Query: "fintech startup"
    factors = calculate_match_factors(entity, "fintech startup")
    print(f"Query 'fintech startup' -> factors: {factors}")

    # Query: "healthcare company"
    factors = calculate_match_factors(entity, "healthcare company")
    print(f"Query 'healthcare company' -> factors: {factors}")

    print()

def test_stage_matching():
    """Test stage matching logic."""
    print("=== Testing Stage Matching ===")

    # Test entity with seed stage focus
    entity = MockEntity(stage_focus=["Seed", "Pre-seed"])

    # Query: "seed round"
    factors = calculate_match_factors(entity, "seed round")
    print(f"Query 'seed round' -> factors: {factors}")

    # Query: "series a investment"
    factors = calculate_match_factors(entity, "series a investment")
    print(f"Query 'series a investment' -> factors: {factors}")

    print()

def test_geography_matching():
    """Test geography matching logic."""
    print("=== Testing Geography Matching ===")

    # Test entity in Dubai
    entity = MockEntity(location="Dubai")

    # Query: "dubai startup"
    factors = calculate_match_factors(entity, "dubai startup")
    print(f"Query 'dubai startup' -> factors: {factors}")

    # Query: "uae fintech"
    factors = calculate_match_factors(entity, "uae fintech")
    print(f"Query 'uae fintech' -> factors: {factors}")

    # Query: "mena region"
    factors = calculate_match_factors(entity, "mena region")
    print(f"Query 'mena region' -> factors: {factors}")

    print()

def test_overall_scoring():
    """Test overall scoring calculation."""
    print("=== Testing Overall Scoring ===")

    # Complete matching entity
    entity = MockEntity(
        sector_focus=["Fintech"],
        stage_focus=["Seed"],
        location="Dubai",
        check_size_min=50000,
        check_size_max=200000
    )

    # Perfect match query
    score = calculate_overall_match_score(entity, "fintech seed dubai", similarity_score=0.9)
    print(f"Perfect match 'fintech seed dubai' (sim=0.9) -> score: {score}")

    # Partial match query
    score = calculate_overall_match_score(entity, "fintech dubai", similarity_score=0.7)
    print(f"Partial match 'fintech dubai' (sim=0.7) -> score: {score}")

    # No match query
    score = calculate_overall_match_score(entity, "healthcare series a", similarity_score=0.3)
    print(f"No match 'healthcare series a' (sim=0.3) -> score: {score}")

    print()

if __name__ == "__main__":
    print("Testing Matching Engine Logic\n")

    test_sector_matching()
    test_stage_matching()
    test_geography_matching()
    test_overall_scoring()

    print("All tests completed!")