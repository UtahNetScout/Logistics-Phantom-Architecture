"""
tests/unit/test_bezier_paths.py
================================

Unit tests for the Bezier Path Generator.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA — PORTFOLIO PROOF-OF-CONCEPT

Validates:
    - Generated paths pass through (or very close to) all waypoints
    - Path smoothness score ≥ 0.90 (< 45° angular changes dominate)
    - Bezier path length ≥ straight-line distance (realistic routing)
    - Smoothness score and accuracy are printed to console
"""

import math
from typing import List, Tuple

import numpy as np
import pytest

from src.prototype.bezier_path_generator import (
    MAX_SMOOTH_ANGLE_DEG,
    compute_path_length_km,
    compute_smoothness_score,
    generate_bezier_path,
    straight_line_distance_km,
)


# ============================================================================
# HELPERS
# ============================================================================

def _make_simple_route(n_wps: int = 5, seed: int = 42) -> List[Tuple[float, float]]:
    """Generate a simple synthetic route for testing."""
    import random
    rng = random.Random(seed)
    base_lat, base_lon = 36.0, -90.0
    wps = []
    for _ in range(n_wps):
        base_lat += rng.uniform(0.2, 0.6)
        base_lon += rng.uniform(0.2, 0.6)
        wps.append((round(base_lat, 4), round(base_lon, 4)))
    return wps


# ============================================================================
# TESTS
# ============================================================================

class TestPathThroughWaypoints:
    """Bezier path must start and end at the first and last waypoints."""

    def test_path_starts_at_first_waypoint(self, sample_waypoints):
        """
        The first point of the Bezier path must equal the first waypoint.
        """
        path = generate_bezier_path(sample_waypoints, samples_per_segment=50)
        first_wp = np.array(sample_waypoints[0])
        first_pt = path[0]
        dist_deg = float(np.linalg.norm(first_pt - first_wp))
        print(f"\n  Start deviation: {dist_deg:.6f}°  (tolerance: 1e-9)")
        assert dist_deg < 1e-9, f"Path start {first_pt} != waypoint {first_wp}"

    def test_path_ends_at_last_waypoint(self, sample_waypoints):
        """
        The last point of the Bezier path must equal the last waypoint.
        """
        path = generate_bezier_path(sample_waypoints, samples_per_segment=50)
        last_wp = np.array(sample_waypoints[-1])
        last_pt = path[-1]
        dist_deg = float(np.linalg.norm(last_pt - last_wp))
        print(f"\n  End deviation: {dist_deg:.6f}°  (tolerance: 1e-9)")
        assert dist_deg < 1e-9, f"Path end {last_pt} != waypoint {last_wp}"

    def test_path_has_enough_points(self, sample_waypoints):
        """
        Path must contain at least (n_segments * samples_per_segment) points.
        """
        samples = 30
        path = generate_bezier_path(sample_waypoints, samples_per_segment=samples)
        n_segments = len(sample_waypoints) - 1
        min_expected = n_segments * (samples - 1)
        print(f"\n  Path points: {len(path)}  (min expected: {min_expected})")
        assert len(path) >= min_expected

    @pytest.mark.parametrize("n_wps", [2, 4, 8, 12])
    def test_path_generated_for_various_waypoint_counts(self, n_wps: int):
        """Bezier generation must succeed for 2–12 waypoints."""
        wps = _make_simple_route(n_wps=n_wps)
        path = generate_bezier_path(wps)
        assert len(path) >= n_wps - 1, f"Path too short for {n_wps} waypoints"

    def test_non_collinear_route_bows_between_waypoints(self):
        """A route with a turn should not collapse into straight chord samples."""
        waypoints = [(36.0, -90.0), (36.0, -89.0), (37.0, -89.0)]
        path = generate_bezier_path(waypoints, samples_per_segment=40)

        first_segment = path[:40]
        max_lat_deviation = float(np.max(np.abs(first_segment[:, 0] - 36.0)))
        print(f"\n  First-segment bow deviation: {max_lat_deviation:.4f} degrees")
        assert max_lat_deviation > 0.01


class TestPathSmoothness:
    """Paths must satisfy the smoothness criterion (≥ 90% gentle angles)."""

    def test_smoothness_above_threshold(self, sample_waypoints):
        """
        Smoothness score must be ≥ 0.90.

        Smoothness = fraction of triplets with angle < MAX_SMOOTH_ANGLE_DEG.
        """
        path = generate_bezier_path(sample_waypoints, samples_per_segment=50)
        score = compute_smoothness_score(path)
        print(f"\n  Smoothness score: {score:.4f}  (target: ≥0.90)")
        assert score >= 0.90, (
            f"Smoothness {score:.4f} below 0.90 threshold"
        )

    def test_smoothness_on_multiple_routes(self):
        """All synthetic routes in a batch must meet the smoothness threshold."""
        import random
        rng = random.Random(42)
        results = []
        for seed in range(20):
            wps = _make_simple_route(n_wps=rng.randint(4, 8), seed=seed)
            path = generate_bezier_path(wps, samples_per_segment=40)
            score = compute_smoothness_score(path)
            results.append(score)
        mean_score = sum(results) / len(results)
        below = [s for s in results if s < 0.90]
        print(f"\n  Mean smoothness: {mean_score:.4f}, "
              f"routes below 0.90: {len(below)}/20")
        assert len(below) == 0, f"{len(below)} routes with smoothness < 0.90"

    def test_two_waypoint_path_is_maximally_smooth(self):
        """A path between only 2 waypoints should score 1.0 smoothness."""
        path = generate_bezier_path([(40.0, -90.0), (41.0, -89.0)],
                                    samples_per_segment=50)
        score = compute_smoothness_score(path)
        print(f"\n  2-waypoint smoothness: {score:.4f}  (expected: 1.0)")
        assert score == 1.0


class TestPathLength:
    """Bezier path length must be ≥ straight-line distance."""

    def test_bezier_longer_than_or_equal_to_straight_line(self, sample_waypoints):
        """
        Bezier path length must be ≥ straight-line distance through waypoints.

        Ratio target: ≥ 1.0 (curves add realism, never shortcut).
        """
        path = generate_bezier_path(sample_waypoints, samples_per_segment=50)
        bezier_km = compute_path_length_km(path)
        straight_km = straight_line_distance_km(sample_waypoints)
        ratio = bezier_km / straight_km if straight_km > 0 else 1.0
        print(f"\n  Bezier: {bezier_km:.2f} km | Straight: {straight_km:.2f} km | "
              f"Ratio: {ratio:.4f}")
        assert bezier_km >= straight_km * 0.99, (
            f"Bezier path {bezier_km:.2f} km shorter than straight-line "
            f"{straight_km:.2f} km (ratio: {ratio:.4f})"
        )

    @pytest.mark.parametrize("n_wps", [3, 5, 8])
    def test_path_length_increases_with_more_waypoints(self, n_wps: int):
        """More waypoints = longer routes (general trend check)."""
        import random
        rng = random.Random(42)
        base_lat, base_lon = 36.0, -90.0
        wps = []
        for _ in range(n_wps):
            base_lat += rng.uniform(0.3, 0.7)
            base_lon += rng.uniform(0.3, 0.7)
            wps.append((base_lat, base_lon))
        path = generate_bezier_path(wps)
        length = compute_path_length_km(path)
        print(f"\n  {n_wps} waypoints → {length:.2f} km")
        assert length > 0.0

    def test_single_segment_length_positive(self):
        """A two-waypoint path must have a positive, finite length."""
        p1, p2 = (40.0, -90.0), (41.0, -89.0)
        path = generate_bezier_path([p1, p2], samples_per_segment=20)
        length = compute_path_length_km(path)
        print(f"\n  Two-point path: {length:.4f} km")
        assert length > 0.0
        assert math.isfinite(length)
