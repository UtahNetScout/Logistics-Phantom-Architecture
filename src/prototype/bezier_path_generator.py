#!/usr/bin/env python3
"""
Bezier Path Generator
======================
Unclassified Synthetic Prototype - Portfolio PoC
Not operational telemetry. Not deployment-ready deception tooling.

This module generates realistic phantom convoy routes using cubic Bezier curves.
Straight-line waypoint noise produces spatially implausible paths; Bezier curves
produce smooth, road-like trajectories that are harder for adversarial anomaly
detectors to distinguish from genuine logistics movements.

Methodology:
    - A cubic Bezier curve is defined by four control points: P0 (start),
      P1 and P2 (interior handles), and P3 (end).
    - Control points are jittered randomly from a base anchor to simulate
      organic route variation.
    - The curve is sampled at N evenly-spaced t values to produce waypoints.
    - Multiple independent curves can be chained to simulate multi-leg routes.

Mathematical Background:
    B(t) = (1-t)^3*P0 + 3*(1-t)^2*t*P1 + 3*(1-t)*t^2*P2 + t^3*P3
    where t ∈ [0, 1]

Connections to Architecture:
    - Feeds into Agent B (Phantom Swarm Generator) to produce realistic paths
    - More plausible movement patterns increase the cost of adversary filtering
    - Kinematic velocity profiler consumes these waypoints downstream

Usage:
    python src/prototype/bezier_path_generator.py
"""

import random
from typing import List, Tuple

# ============================================================================
# BANNER
# ============================================================================

BANNER = """
================================================================================
  BEZIER PATH GENERATOR
  Unclassified Synthetic Prototype - Portfolio PoC
  Not operational telemetry. Not deployment-ready deception tooling.
================================================================================
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

RANDOM_SEED = 42
WAYPOINTS_PER_ROUTE = 20        # Sampled points along each Bezier curve
CONTROL_JITTER_DEG = 0.5        # Max lat/lon jitter for control points (degrees)
ROUTE_SPAN_DEG = 2.0            # Approximate route length (degrees)


# ============================================================================
# BEZIER MATH
# ============================================================================

Point2D = Tuple[float, float]   # (latitude, longitude)


def cubic_bezier_point(t: float,
                       p0: Point2D, p1: Point2D,
                       p2: Point2D, p3: Point2D) -> Point2D:
    """
    Evaluate a cubic Bezier curve at parameter t.

    B(t) = (1-t)^3*P0 + 3*(1-t)^2*t*P1 + 3*(1-t)*t^2*P2 + t^3*P3

    Args:
        t:  Curve parameter in [0, 1]. t=0 returns P0, t=1 returns P3.
        p0: Start control point (lat, lon).
        p1: First interior handle (lat, lon).
        p2: Second interior handle (lat, lon).
        p3: End control point (lat, lon).

    Returns:
        Interpolated (lat, lon) point on the curve.
    """
    mt = 1.0 - t
    lat = (mt ** 3 * p0[0]
           + 3 * mt ** 2 * t * p1[0]
           + 3 * mt * t ** 2 * p2[0]
           + t ** 3 * p3[0])
    lon = (mt ** 3 * p0[1]
           + 3 * mt ** 2 * t * p1[1]
           + 3 * mt * t ** 2 * p2[1]
           + t ** 3 * p3[1])
    return (round(lat, 6), round(lon, 6))


def sample_cubic_bezier(p0: Point2D, p1: Point2D,
                        p2: Point2D, p3: Point2D,
                        num_points: int = WAYPOINTS_PER_ROUTE) -> List[Point2D]:
    """
    Sample a cubic Bezier curve at evenly-spaced t values.

    Args:
        p0: Start control point.
        p1: First interior handle.
        p2: Second interior handle.
        p3: End control point.
        num_points: Number of waypoints to sample along the curve.

    Returns:
        List of (lat, lon) tuples sampled from t=0 to t=1.
    """
    return [
        cubic_bezier_point(i / (num_points - 1), p0, p1, p2, p3)
        for i in range(num_points)
    ]


# ============================================================================
# ROUTE GENERATION
# ============================================================================

def generate_control_points(anchor_lat: float, anchor_lon: float,
                             rng: random.Random) -> Tuple[Point2D, Point2D, Point2D, Point2D]:
    """
    Generate four control points for a cubic Bezier route.

    Starts at the anchor, ends roughly ROUTE_SPAN_DEG away, with two
    interior handles jittered to create organic curvature.

    Args:
        anchor_lat: Latitude of the route start.
        anchor_lon: Longitude of the route start.
        rng: Random number generator for reproducibility.

    Returns:
        Tuple of (P0, P1, P2, P3) control points.
    """
    span = ROUTE_SPAN_DEG
    jitter = CONTROL_JITTER_DEG

    p0 = (anchor_lat, anchor_lon)
    p3 = (anchor_lat + rng.uniform(span * 0.5, span),
          anchor_lon + rng.uniform(-span * 0.5, span * 0.5))

    # Interior handles create the curve shape
    p1 = (anchor_lat + rng.uniform(-jitter, jitter) + span * 0.25,
          anchor_lon + rng.uniform(-jitter, jitter))
    p2 = (anchor_lat + rng.uniform(-jitter, jitter) + span * 0.75,
          anchor_lon + rng.uniform(-jitter, jitter))

    return p0, p1, p2, p3


def generate_bezier_route(anchor_lat: float, anchor_lon: float,
                          rng: random.Random,
                          num_points: int = WAYPOINTS_PER_ROUTE) -> List[Point2D]:
    """
    Generate a full Bezier-curve phantom route from a given start point.

    Args:
        anchor_lat: Starting latitude for the route.
        anchor_lon: Starting longitude for the route.
        rng: Seeded random generator for determinism.
        num_points: Number of waypoints to sample along the curve.

    Returns:
        Ordered list of (lat, lon) waypoints forming a smooth route.
    """
    p0, p1, p2, p3 = generate_control_points(anchor_lat, anchor_lon, rng)
    return sample_cubic_bezier(p0, p1, p2, p3, num_points)


def batch_generate_routes(count: int,
                          seed: int = RANDOM_SEED) -> List[List[Point2D]]:
    """
    Generate a batch of independent Bezier phantom routes.

    Args:
        count: Number of routes to generate.
        seed: Random seed for reproducibility.

    Returns:
        List of routes, each a list of (lat, lon) waypoints.
    """
    rng = random.Random(seed)
    routes = []
    for _ in range(count):
        anchor_lat = rng.uniform(-55.0, 55.0)
        anchor_lon = rng.uniform(-160.0, 160.0)
        routes.append(generate_bezier_route(anchor_lat, anchor_lon, rng))
    return routes


# ============================================================================
# REPORTING
# ============================================================================

def print_route_stats(routes: List[List[Point2D]]) -> None:
    """
    Print summary statistics about the generated routes.

    Args:
        routes: List of generated Bezier routes.
    """
    total_waypoints = sum(len(r) for r in routes)
    print("\n" + "─" * 80)
    print("  BEZIER ROUTE GENERATION STATS")
    print("─" * 80)
    print(f"  Routes generated:     {len(routes):,}")
    print(f"  Waypoints per route:  {WAYPOINTS_PER_ROUTE}")
    print(f"  Total waypoints:      {total_waypoints:,}")
    print(f"  Random seed:          {RANDOM_SEED}")
    if routes:
        sample_route = routes[0]
        print()
        print("  Sample route (first 3 waypoints of route 0):")
        for wp in sample_route[:3]:
            print(f"    lat={wp[0]:.6f}, lon={wp[1]:.6f}")
        print("    ...")
    print("─" * 80)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(BANNER)

    print("  Generating 500 synthetic Bezier phantom routes...")
    routes = batch_generate_routes(count=500, seed=RANDOM_SEED)
    print_route_stats(routes)

    print("\n  Prototype run complete. All coordinates are synthetic and non-operational.\n")
