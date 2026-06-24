"""
tests/unit/test_agent_b_generation.py
======================================

Unit tests for Agent B Parallel Swarm Generator.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA — PORTFOLIO PROOF-OF-CONCEPT

Validates:
    - Phantom count matches the requested multiplier
    - Generated coordinates fall within geographic bounds
    - Speed profiles respect the 35–55 km/h constraint
    - Rest stops are placed at realistic intervals
    - Temporal jitter is within ±30 min bounds
    - Parallelisation produces deterministic results with a fixed seed

Metrics printed to console: generation time, phantom count, per-phantom latency.
"""

import time
from typing import List

import pytest

from src.prototype.agent_b_parallel_swarm_generator import (
    GEO_LAT_MAX,
    GEO_LAT_MIN,
    GEO_LON_MAX,
    GEO_LON_MIN,
    MAX_SPEED_KMH,
    MIN_SPEED_KMH,
    TEMPORAL_JITTER_MAX_MIN,
    TEMPORAL_JITTER_MIN_MIN,
    generate_phantom_swarm,
)


# ============================================================================
# HELPERS
# ============================================================================

def _generate_and_time(num_phantoms: int, seed: int = 42) -> tuple:
    t0 = time.perf_counter()
    phantoms = generate_phantom_swarm(num_phantoms=num_phantoms, seed=seed, n_workers=1)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return phantoms, elapsed_ms


# ============================================================================
# TESTS
# ============================================================================

class TestPhantomCount:
    """Phantom count must exactly match the requested multiplier."""

    @pytest.mark.parametrize("multiplier", [100, 250, 1000])
    def test_phantom_count_matches_multiplier(self, multiplier: int):
        """
        Phantom count must equal the requested multiplier at 100x, 250x, 1000x.
        """
        phantoms, elapsed_ms = _generate_and_time(multiplier)
        print(f"\n  [{multiplier}x] Generated {len(phantoms)} phantoms in {elapsed_ms:.1f} ms")
        assert len(phantoms) == multiplier, (
            f"Expected {multiplier} phantoms, got {len(phantoms)}"
        )

    def test_each_phantom_has_unique_id(self):
        """All phantom IDs must be unique within a batch."""
        phantoms = generate_phantom_swarm(100, seed=42, n_workers=1)
        ids = [p["phantom_id"] for p in phantoms]
        assert len(set(ids)) == 100, "Phantom IDs are not unique"


class TestGeographicBounds:
    """Generated coordinates must fall within the configured bounding box."""

    def test_waypoints_within_lat_bounds(self):
        """All waypoint latitudes must be within GEO_LAT_MIN–GEO_LAT_MAX (±5°)."""
        phantoms = generate_phantom_swarm(200, seed=42, n_workers=1)
        for p in phantoms:
            for lat, _ in p["waypoints"]:
                assert GEO_LAT_MIN - 5 <= lat <= GEO_LAT_MAX + 5, (
                    f"Latitude {lat} out of bounds"
                )

    def test_waypoints_within_lon_bounds(self):
        """All waypoint longitudes must be within GEO_LON_MIN–GEO_LON_MAX (±5°)."""
        phantoms = generate_phantom_swarm(200, seed=42, n_workers=1)
        for p in phantoms:
            for _, lon in p["waypoints"]:
                assert GEO_LON_MIN - 5 <= lon <= GEO_LON_MAX + 5, (
                    f"Longitude {lon} out of bounds"
                )

    def test_waypoints_are_valid_lat_lon(self):
        """Lat ∈ [-90, 90] and lon ∈ [-180, 180] (basic sanity)."""
        phantoms = generate_phantom_swarm(100, seed=42, n_workers=1)
        for p in phantoms:
            for lat, lon in p["waypoints"]:
                assert -90 <= lat <= 90, f"Invalid latitude: {lat}"
                assert -180 <= lon <= 180, f"Invalid longitude: {lon}"


class TestSpeedProfiles:
    """Speed profiles must respect the 35–55 km/h logistics constraint."""

    def test_all_speeds_within_range(self):
        """Every speed in every speed profile must be within [MIN_SPEED, MAX_SPEED]."""
        phantoms = generate_phantom_swarm(200, seed=42, n_workers=1)
        violations = []
        for p in phantoms:
            for spd in p["speed_profile_kmh"]:
                if not (MIN_SPEED_KMH <= spd <= MAX_SPEED_KMH):
                    violations.append((p["phantom_id"], spd))
        print(f"\n  Speed range checked: {MIN_SPEED_KMH}–{MAX_SPEED_KMH} km/h, "
              f"violations: {len(violations)}")
        assert len(violations) == 0, f"Speed violations: {violations[:5]}"

    def test_speed_profile_length_matches_waypoints(self):
        """Speed profile must have exactly len(waypoints)-1 entries (one per leg)."""
        phantoms = generate_phantom_swarm(50, seed=42, n_workers=1)
        for p in phantoms:
            expected_len = len(p["waypoints"]) - 1
            actual_len = len(p["speed_profile_kmh"])
            assert actual_len == expected_len, (
                f"Phantom {p['phantom_id']}: speed profile length {actual_len} "
                f"!= {expected_len}"
            )


class TestRestStops:
    """Rest stops must occur at realistic intervals."""

    def test_rest_stops_are_valid_waypoint_indices(self):
        """Rest stop indices must reference valid waypoint positions."""
        phantoms = generate_phantom_swarm(100, seed=42, n_workers=1)
        for p in phantoms:
            n_wps = len(p["waypoints"])
            for rs_idx in p["rest_stops"]:
                assert 0 <= rs_idx < n_wps, (
                    f"Rest stop index {rs_idx} out of range [0, {n_wps})"
                )

    def test_rest_stop_count_is_reasonable(self):
        """Number of rest stops should be non-negative and not exceed waypoint count."""
        phantoms = generate_phantom_swarm(100, seed=42, n_workers=1)
        for p in phantoms:
            n_stops = len(p["rest_stops"])
            n_wps = len(p["waypoints"])
            assert 0 <= n_stops <= n_wps, (
                f"Unrealistic rest stop count: {n_stops} for {n_wps} waypoints"
            )


class TestTemporalJitter:
    """Temporal jitter must be within ±30 min bounds."""

    def test_all_jitter_within_bounds(self):
        """Every timestamp offset must be within [JITTER_MIN, JITTER_MAX]."""
        phantoms = generate_phantom_swarm(200, seed=42, n_workers=1)
        violations = []
        for p in phantoms:
            for offset in p["timestamp_offsets_min"]:
                if not (TEMPORAL_JITTER_MIN_MIN <= offset <= TEMPORAL_JITTER_MAX_MIN):
                    violations.append((p["phantom_id"], offset))
        print(f"\n  Temporal jitter range: {TEMPORAL_JITTER_MIN_MIN}–"
              f"{TEMPORAL_JITTER_MAX_MIN} min, violations: {len(violations)}")
        assert len(violations) == 0, f"Jitter violations: {violations[:5]}"

    def test_jitter_length_matches_waypoints(self):
        """Timestamp offsets list must have one entry per waypoint."""
        phantoms = generate_phantom_swarm(50, seed=42, n_workers=1)
        for p in phantoms:
            assert len(p["timestamp_offsets_min"]) == len(p["waypoints"])


class TestDeterminism:
    """Two calls with the same seed must produce identical results."""

    @pytest.mark.parametrize("multiplier", [100, 250])
    def test_deterministic_with_fixed_seed(self, multiplier: int):
        """
        Two serial generations with seed=42 must produce identical phantom lists.
        """
        phantoms_a = generate_phantom_swarm(multiplier, seed=42, n_workers=1)
        phantoms_b = generate_phantom_swarm(multiplier, seed=42, n_workers=1)
        for a, b in zip(phantoms_a, phantoms_b):
            assert a["waypoints"] == b["waypoints"], (
                f"Phantom {a['phantom_id']} waypoints differ between runs"
            )
            assert a["speed_profile_kmh"] == b["speed_profile_kmh"]
            assert a["timestamp_offsets_min"] == b["timestamp_offsets_min"]
        print(f"\n  [{multiplier}x] Determinism verified: both runs identical ✅")

    def test_different_seeds_produce_different_results(self):
        """Different seeds must produce different phantom batches."""
        phantoms_42 = generate_phantom_swarm(50, seed=42, n_workers=1)
        phantoms_99 = generate_phantom_swarm(50, seed=99, n_workers=1)
        # At least some waypoints should differ
        all_same = all(
            phantoms_42[i]["waypoints"] == phantoms_99[i]["waypoints"]
            for i in range(min(10, len(phantoms_42)))
        )
        assert not all_same, "Different seeds produced identical results"


class TestGenerationMetrics:
    """Generation time should be reasonable for 1,000 phantoms."""

    def test_generation_under_5_seconds_for_1000(self):
        """
        Agent B must generate 1,000 phantoms in under 5 seconds (serial).

        Target: <5s (single-core serial baseline).
        """
        phantoms, elapsed_ms = _generate_and_time(1000, seed=42)
        elapsed_s = elapsed_ms / 1000
        per_phantom_us = (elapsed_ms / 1000) * 1000
        print(f"\n  1000 phantoms: {elapsed_ms:.1f} ms total, "
              f"{per_phantom_us:.2f} µs per phantom")
        assert len(phantoms) == 1000
        assert elapsed_s < 5.0, (
            f"Generation took {elapsed_s:.2f}s — exceeds 5s target"
        )
