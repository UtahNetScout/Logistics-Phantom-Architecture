#!/usr/bin/env python3
"""
Bezier Path Generator - Logistics Phantom Architecture
======================================================

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA
PORTFOLIO PROOF-OF-CONCEPT — NOT OPERATIONAL TELEMETRY
NOT DEPLOYMENT-READY DECEPTION TOOLING

Generates smooth, realistic phantom convoy routes using piecewise cubic
Bezier interpolation through user-supplied geographic waypoints. Straight-line
point-to-point movement is an obvious synthetic artifact; Bezier curves
produce naturally curved paths consistent with real road networks.

Key Features:
    - Piecewise cubic Bezier curves passing through all input waypoints
    - Smoothness score: fraction of adjacent-segment angle changes < 45°
    - Path length always >= straight-line distance (realistic routing)
    - Deterministic output with fixed seeds

Usage:
    python3 bezier_path_generator.py

Author: Logistics Phantom Prototype
Date: 2026
"""

import math
import random
import time
from typing import List, Tuple

import numpy as np

# ============================================================================
# BANNER
# ============================================================================

BANNER = (
    "UNCLASSIFIED SYNTHETIC PROTOTYPE DATA | "
    "PORTFOLIO PROOF-OF-CONCEPT | "
    "NOT OPERATIONAL TELEMETRY"
)

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_SAMPLES_PER_SEGMENT: int = 50   # Interpolation points per Bezier segment
MAX_SMOOTH_ANGLE_DEG: float = 45.0      # Maximum acceptable angle change (degrees)

# ============================================================================
# BEZIER MATH
# ============================================================================


def _cubic_bezier(
    p0: np.ndarray,
    p1: np.ndarray,
    p2: np.ndarray,
    p3: np.ndarray,
    t: np.ndarray,
) -> np.ndarray:
    """
    Evaluate a cubic Bezier curve at parameter values t ∈ [0, 1].

    Args:
        p0, p1, p2, p3: Control points as 1-D arrays of shape (2,).
        t: Array of parameter values.

    Returns:
        Array of shape (len(t), 2) containing interpolated points.
    """
    t = t[:, np.newaxis]
    return (
        (1 - t) ** 3 * p0
        + 3 * (1 - t) ** 2 * t * p1
        + 3 * (1 - t) * t ** 2 * p2
        + t ** 3 * p3
    )


def _angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """Return the angle in degrees between two 2-D vectors."""
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-12 or n2 < 1e-12:
        return 0.0
    cos_theta = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return math.degrees(math.acos(cos_theta))


# ============================================================================
# PUBLIC API
# ============================================================================


def generate_bezier_path(
    waypoints: List[Tuple[float, float]],
    samples_per_segment: int = DEFAULT_SAMPLES_PER_SEGMENT,
    control_scale: float = 0.18,
) -> np.ndarray:
    """
    Generate a smooth Bezier path through a list of (lat, lon) waypoints.

    Constructs Catmull-Rom-style cubic Bezier segments between consecutive
    waypoints. Control points are derived from neighbouring waypoint tangents,
    so the curve passes through every supplied waypoint while smoothing turns.

    Args:
        waypoints: Ordered list of (lat, lon) tuples defining the route.
        samples_per_segment: Number of interpolated points per Bezier segment.
        control_scale: Fraction of segment length used for control point offset.

    Returns:
        NumPy array of shape (N, 2) containing smoothed (lat, lon) positions.
    """
    if len(waypoints) < 2:
        return np.array(waypoints, dtype=float)

    pts = np.array(waypoints, dtype=float)
    path_segments: List[np.ndarray] = []

    for i in range(len(pts) - 1):
        p0 = pts[i]
        p3 = pts[i + 1]
        p_prev = pts[i - 1] if i > 0 else p0
        p_next = pts[i + 2] if i + 2 < len(pts) else p3

        # Catmull-Rom tangent approximation converted to cubic Bezier controls.
        p1 = p0 + control_scale * (p3 - p_prev)
        p2 = p3 - control_scale * (p_next - p0)
        t_vals = np.linspace(0.0, 1.0, samples_per_segment, endpoint=(i == len(pts) - 2))
        segment = _cubic_bezier(p0, p1, p2, p3, t_vals)
        path_segments.append(segment)

    return np.vstack(path_segments)


def compute_path_length_km(path: np.ndarray) -> float:
    """
    Compute the total length of a path in kilometres using the Haversine formula.

    Args:
        path: Array of shape (N, 2) containing (lat, lon) in degrees.

    Returns:
        Total path length in kilometres.
    """
    if len(path) < 2:
        return 0.0
    R = 6371.0
    total = 0.0
    for i in range(len(path) - 1):
        lat1, lon1 = math.radians(path[i, 0]), math.radians(path[i, 1])
        lat2, lon2 = math.radians(path[i + 1, 0]), math.radians(path[i + 1, 1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        total += 2 * R * math.asin(math.sqrt(a))
    return total


def compute_smoothness_score(path: np.ndarray) -> float:
    """
    Compute a smoothness score for a path (0.0 = very jagged, 1.0 = perfectly smooth).

    Smoothness is defined as the fraction of consecutive triplets where the
    angular change is less than MAX_SMOOTH_ANGLE_DEG degrees.

    Args:
        path: Array of shape (N, 2).

    Returns:
        Smoothness score in [0, 1].
    """
    if len(path) < 3:
        return 1.0
    smooth_count = 0
    total = 0
    for i in range(1, len(path) - 1):
        v1 = path[i] - path[i - 1]
        v2 = path[i + 1] - path[i]
        angle = _angle_between_vectors(v1, v2)
        if angle < MAX_SMOOTH_ANGLE_DEG:
            smooth_count += 1
        total += 1
    return smooth_count / total if total > 0 else 1.0


def straight_line_distance_km(
    waypoints: List[Tuple[float, float]],
) -> float:
    """
    Compute the total straight-line (great-circle) distance through waypoints.

    Args:
        waypoints: List of (lat, lon) tuples.

    Returns:
        Total straight-line distance in kilometres.
    """
    pts = np.array(waypoints, dtype=float)
    return compute_path_length_km(pts)


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main() -> int:
    """Demonstrate Bezier path generation with sample logistics waypoints."""
    print("\n" + "=" * 70)
    print("  BEZIER PATH GENERATOR")
    print(f"  {BANNER}")
    print("=" * 70)

    rng = random.Random(42)
    num_routes = 5

    for route_idx in range(num_routes):
        # Generate synthetic waypoints (not real operational routes)
        n_wps = rng.randint(4, 8)
        base_lat = rng.uniform(35.0, 45.0)
        base_lon = rng.uniform(-95.0, -75.0)
        waypoints = []
        for _ in range(n_wps):
            base_lat += rng.uniform(0.1, 0.5)
            base_lon += rng.uniform(0.1, 0.5)
            waypoints.append((round(base_lat, 4), round(base_lon, 4)))

        t0 = time.perf_counter()
        path = generate_bezier_path(waypoints, samples_per_segment=50)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        straight_km = straight_line_distance_km(waypoints)
        bezier_km = compute_path_length_km(path)
        smoothness = compute_smoothness_score(path)

        print(f"\n  Route {route_idx + 1}: {n_wps} waypoints -> {len(path)} path points")
        print(f"  Straight-line distance : {straight_km:.2f} km")
        print(f"  Bezier path length     : {bezier_km:.2f} km  (ratio: {bezier_km/straight_km:.3f})")
        print(f"  Smoothness score       : {smoothness:.3f}  (target: >0.90)")
        print(f"  Generation time        : {elapsed_ms:.2f} ms")
        assert bezier_km >= straight_km * 0.99, "Path shorter than straight-line — check control points"
        assert smoothness >= 0.90, f"Smoothness {smoothness:.3f} below 0.90 threshold"

    print("\n" + "=" * 70)
    print("  All routes passed smoothness and length checks.")
    print(f"  {BANNER}")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
