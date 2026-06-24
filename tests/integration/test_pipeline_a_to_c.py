"""
tests/integration/test_pipeline_a_to_c.py
==========================================

Integration tests for the full Agent A seed → Agent B generation → Agent C
validation pipeline.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA — PORTFOLIO PROOF-OF-CONCEPT

Validates:
    - End-to-end pipeline executes without errors
    - No data leakage between agents (Agent B receives only seed params, not coords)
    - End-to-end latency is acceptable
    - Successful validation rate is measurable
    - Pipeline integrity: approved count + rejected count = total generated
"""

import time
from typing import Dict, List, Tuple

import pytest

from src.prototype.agent_b_parallel_swarm_generator import generate_phantom_swarm
from src.prototype.agent_c_spatial_hash_validator import SpatialHashValidator


# ============================================================================
# SIMULATED AGENT A OUTPUT (no real coordinates passed to Agent B)
# ============================================================================

def agent_a_produce_seed_params(real_convoy: List[Tuple[float, float]]) -> Dict:
    """
    Simulate Agent A abstracting a real convoy into seed parameters.

    CRITICAL: Agent A must NOT pass real convoy coordinates to Agent B.
    It outputs only abstract seed parameters (multiplier, region bounds, seed).
    This prevents data leakage between agents.

    Args:
        real_convoy: The real convoy coordinates (kept inside Agent A's boundary).

    Returns:
        Dict of abstract seed parameters — no coordinates included.
    """
    # Agent A extracts regional bounding box (approximate — NOT exact coords)
    lat_center = sum(lat for lat, _ in real_convoy) / len(real_convoy)
    lon_center = sum(lon for _, lon in real_convoy) / len(real_convoy)
    # Abstract to a ±5° regional box — no waypoint-level detail passes through
    return {
        "region_lat_range": (lat_center - 5.0, lat_center + 5.0),
        "region_lon_range": (lon_center - 5.0, lon_center + 5.0),
        "multiplier": 100,
        "seed": 42,
        "speed_min_kmh": 35.0,
        "speed_max_kmh": 55.0,
        "waypoints_per_phantom": 8,
    }


# ============================================================================
# TESTS
# ============================================================================

class TestPipelineEndToEnd:
    """Full A→B→C pipeline must complete and return sane results."""

    def test_pipeline_runs_without_errors(self, mock_real_convoy):
        """
        Agent A → Agent B → Agent C pipeline must execute without exceptions.
        """
        # Agent A
        seed_params = agent_a_produce_seed_params(mock_real_convoy)

        # Agent B
        phantoms = generate_phantom_swarm(
            num_phantoms=seed_params["multiplier"],
            seed=seed_params["seed"],
            n_workers=1,
        )

        # Agent C
        validator = SpatialHashValidator(exclusion_km=5.0)
        validator.add_real_waypoints(mock_real_convoy)
        result = validator.validate_batch([p["waypoints"] for p in phantoms])

        assert result["approved_count"] + result["rejected_count"] == len(phantoms)
        print(f"\n  Pipeline: {seed_params['multiplier']}x phantoms → "
              f"{result['approved_count']} approved, {result['rejected_count']} rejected")

    def test_pipeline_integrity_approved_plus_rejected_equals_total(self, mock_real_convoy):
        """
        Approved + rejected must always equal total generated.

        This validates that Agent C processes every phantom exactly once.
        """
        seed_params = agent_a_produce_seed_params(mock_real_convoy)
        phantoms = generate_phantom_swarm(
            num_phantoms=200, seed=42, n_workers=1
        )
        validator = SpatialHashValidator(exclusion_km=5.0)
        validator.add_real_waypoints(mock_real_convoy)
        result = validator.validate_batch([p["waypoints"] for p in phantoms])
        total = result["approved_count"] + result["rejected_count"]
        assert total == 200, f"Expected 200, got {total}"

    def test_end_to_end_latency_under_10_seconds(self, mock_real_convoy):
        """
        Full pipeline (Agent A params + 1000x Agent B + Agent C) must complete
        in under 10 seconds.
        """
        t0 = time.perf_counter()

        seed_params = agent_a_produce_seed_params(mock_real_convoy)
        phantoms = generate_phantom_swarm(
            num_phantoms=1000, seed=42, n_workers=1
        )
        validator = SpatialHashValidator(exclusion_km=5.0)
        validator.add_real_waypoints(mock_real_convoy)
        result = validator.validate_batch([p["waypoints"] for p in phantoms])

        elapsed_s = time.perf_counter() - t0
        print(f"\n  End-to-end (1000x): {elapsed_s:.2f}s  "
              f"({result['approved_count']} approved)")
        assert elapsed_s < 10.0, (
            f"End-to-end latency {elapsed_s:.2f}s exceeds 10s budget"
        )


class TestNoDataLeakage:
    """Agent B must not receive real convoy coordinates from Agent A."""

    def test_seed_params_contain_no_real_waypoint_coordinates(
        self, mock_real_convoy
    ):
        """
        Seed parameters from Agent A must not contain exact waypoint coordinates.

        Checks that no key named 'waypoints', 'coordinates', 'real_convoy',
        'lat_lon', or similar appears in the seed param dict.
        """
        seed_params = agent_a_produce_seed_params(mock_real_convoy)
        forbidden_keys = {"waypoints", "coordinates", "real_convoy", "lat_lon",
                          "exact_coords", "ground_truth"}
        present = forbidden_keys & set(seed_params.keys())
        assert len(present) == 0, (
            f"Seed params contain forbidden keys (data leakage): {present}"
        )

    def test_real_convoy_coordinates_not_in_seed_params(self, mock_real_convoy):
        """
        The exact lat/lon values of the real convoy must not appear in seed params.
        """
        seed_params = agent_a_produce_seed_params(mock_real_convoy)
        real_lats = {lat for lat, _ in mock_real_convoy}
        real_lons = {lon for _, lon in mock_real_convoy}

        # Flatten all numeric values in seed params
        all_values = set()
        for v in seed_params.values():
            if isinstance(v, (int, float)):
                all_values.add(v)
            elif isinstance(v, (tuple, list)):
                all_values.update(float(x) for x in v if isinstance(x, (int, float)))

        leaked_lats = real_lats & all_values
        leaked_lons = real_lons & all_values
        assert len(leaked_lats) == 0, f"Real latitudes leaked to Agent B: {leaked_lats}"
        assert len(leaked_lons) == 0, f"Real longitudes leaked to Agent B: {leaked_lons}"


class TestValidationRate:
    """Successful validation rate must be measurable and reasonable."""

    def test_high_approval_rate_for_random_phantoms(self, mock_real_convoy):
        """
        Randomly generated phantoms should have a very high approval rate
        (> 98%) since they are unlikely to land within 5 km of the real convoy.
        """
        phantoms = generate_phantom_swarm(num_phantoms=500, seed=42, n_workers=1)
        validator = SpatialHashValidator(exclusion_km=5.0)
        validator.add_real_waypoints(mock_real_convoy)
        result = validator.validate_batch([p["waypoints"] for p in phantoms])
        approval_rate = result["approved_count"] / 500
        print(f"\n  Approval rate (500 random phantoms): {approval_rate:.4f}")
        assert approval_rate > 0.98, (
            f"Approval rate {approval_rate:.4f} unexpectedly low — check bounding boxes"
        )

    def test_pipeline_with_multiple_real_convoys(
        self, mock_real_convoys_multiple
    ):
        """
        Pipeline must correctly handle multiple simultaneous real convoys.
        """
        validator = SpatialHashValidator(exclusion_km=5.0)
        for convoy in mock_real_convoys_multiple:
            validator.add_real_waypoints(convoy)

        phantoms = generate_phantom_swarm(num_phantoms=300, seed=42, n_workers=1)
        result = validator.validate_batch([p["waypoints"] for p in phantoms])
        total = result["approved_count"] + result["rejected_count"]
        assert total == 300, f"Not all phantoms processed: {total}/300"
        print(f"\n  Multi-convoy: {len(mock_real_convoys_multiple)} real convoys, "
              f"{result['rejected_count']} rejections in 300 phantoms")
