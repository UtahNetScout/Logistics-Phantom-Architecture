#!/usr/bin/env python3
"""
Kinematic Velocity Profiler
============================
Unclassified Synthetic Prototype - Portfolio PoC
Not operational telemetry. Not deployment-ready deception tooling.

This module generates physically plausible speed profiles for phantom convoy
routes. Naive phantom telemetry moves at constant speed regardless of road
geometry, which is a detectable artifact. Real vehicles slow on curves and
accelerate on straight segments; this profiler replicates that behavior.

Methodology:
    - Curvature at each waypoint is estimated from the angular change between
      consecutive waypoint vectors.
    - Speed is inversely proportional to local curvature (sharp curves → slow).
    - Speed is bounded by configurable min/max values representing convoy
      operational speed ranges.
    - Acceleration and deceleration between waypoints are applied smoothly.

Connections to Architecture:
    - Consumes waypoint lists produced by bezier_path_generator.py
    - Produces (lat, lon, speed_kmh, timestamp_s) tuples for downstream use
    - More realistic speed profiles increase adversary detection cost

Usage:
    python src/prototype/kinematic_velocity_profiler.py
"""

import math
import random
from typing import List, Tuple

# ============================================================================
# BANNER
# ============================================================================

BANNER = """
================================================================================
  KINEMATIC VELOCITY PROFILER
  Unclassified Synthetic Prototype - Portfolio PoC
  Not operational telemetry. Not deployment-ready deception tooling.
================================================================================
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

RANDOM_SEED = 42
MIN_SPEED_KMH = 15.0        # Minimum speed at sharp curves (km/h)
MAX_SPEED_KMH = 80.0        # Maximum speed on straight segments (km/h)
MAX_ACCEL_KMHS = 10.0       # Max speed change per waypoint step (km/h)
CURVATURE_SCALE = 5.0       # Tuning constant for curvature-to-speed mapping


# ============================================================================
# GEOMETRY HELPERS
# ============================================================================

Point2D = Tuple[float, float]       # (latitude, longitude)
TelemetryPoint = Tuple[float, float, float, float]   # (lat, lon, speed, time)


def euclidean_distance(p1: Point2D, p2: Point2D) -> float:
    """
    Calculate approximate planar distance between two lat/lon points.

    Uses a flat-Earth approximation adequate for short route segments
    (< 100 km). Not suitable for large-scale geodesic calculations.

    Args:
        p1: First (lat, lon) point.
        p2: Second (lat, lon) point.

    Returns:
        Approximate distance in degrees (proxy for short-range comparison).
    """
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def turning_angle_rad(prev_pt: Point2D, curr_pt: Point2D,
                      next_pt: Point2D) -> float:
    """
    Estimate the turning angle at curr_pt given the adjacent waypoints.

    Computes the angle between vectors (prev→curr) and (curr→next).
    A larger turning angle indicates a sharper curve.

    Args:
        prev_pt: Previous waypoint (lat, lon).
        curr_pt: Current waypoint (lat, lon).
        next_pt: Next waypoint (lat, lon).

    Returns:
        Turning angle in radians [0, π].
    """
    v1 = (curr_pt[0] - prev_pt[0], curr_pt[1] - prev_pt[1])
    v2 = (next_pt[0] - curr_pt[0], next_pt[1] - curr_pt[1])

    mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

    if mag1 < 1e-9 or mag2 < 1e-9:
        return 0.0

    dot = v1[0] * v2[0] + v1[1] * v2[1]
    cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.acos(cos_angle)


# ============================================================================
# SPEED PROFILING
# ============================================================================

def compute_curvature_speeds(waypoints: List[Point2D]) -> List[float]:
    """
    Compute a target speed for each waypoint based on local curvature.

    Interior waypoints receive a curvature-derived speed; endpoints inherit
    their nearest interior value. Speed decreases with sharper curvature.

    Args:
        waypoints: Ordered list of (lat, lon) route waypoints.

    Returns:
        List of target speeds (km/h) aligned to each waypoint.
    """
    n = len(waypoints)
    speeds = [MAX_SPEED_KMH] * n

    for i in range(1, n - 1):
        angle = turning_angle_rad(waypoints[i - 1], waypoints[i], waypoints[i + 1])
        # Normalize angle to [0, 1] relative to π; scale speed inversely
        curvature_factor = angle / math.pi   # 0 = straight, 1 = U-turn
        speed = MAX_SPEED_KMH - curvature_factor * CURVATURE_SCALE * (
            MAX_SPEED_KMH - MIN_SPEED_KMH
        )
        speeds[i] = max(MIN_SPEED_KMH, min(MAX_SPEED_KMH, speed))

    # Endpoints match adjacent interior points
    if n >= 2:
        speeds[0] = speeds[1]
        speeds[-1] = speeds[-2]

    return speeds


def smooth_speed_profile(raw_speeds: List[float],
                         max_accel: float = MAX_ACCEL_KMHS) -> List[float]:
    """
    Apply acceleration/deceleration smoothing to the raw speed profile.

    Ensures that the speed change between consecutive waypoints never
    exceeds max_accel, producing a physically plausible profile.

    Args:
        raw_speeds: List of curvature-derived target speeds.
        max_accel: Maximum allowed speed change per step (km/h).

    Returns:
        Smoothed speed list respecting acceleration constraints.
    """
    smoothed = list(raw_speeds)
    n = len(smoothed)

    # Forward pass (acceleration limit)
    for i in range(1, n):
        smoothed[i] = min(smoothed[i], smoothed[i - 1] + max_accel)

    # Backward pass (deceleration limit)
    for i in range(n - 2, -1, -1):
        smoothed[i] = min(smoothed[i], smoothed[i + 1] + max_accel)

    return smoothed


def assign_timestamps(waypoints: List[Point2D],
                      speeds: List[float],
                      start_time_s: float = 0.0) -> List[TelemetryPoint]:
    """
    Assign cumulative timestamps to each waypoint based on speed.

    Converts speed (km/h) and inter-waypoint distance to elapsed time.
    Uses a flat-Earth degree-to-km approximation (1° ≈ 111 km).

    Args:
        waypoints: Ordered (lat, lon) waypoint list.
        speeds: Speed (km/h) at each waypoint.
        start_time_s: Absolute start time in seconds.

    Returns:
        List of (lat, lon, speed_kmh, timestamp_s) tuples.
    """
    DEG_TO_KM = 111.0   # Rough approximation for short distances

    telemetry: List[TelemetryPoint] = []
    elapsed = start_time_s

    for i, (wp, spd) in enumerate(zip(waypoints, speeds)):
        telemetry.append((wp[0], wp[1], round(spd, 2), round(elapsed, 3)))

        if i < len(waypoints) - 1:
            dist_deg = euclidean_distance(wp, waypoints[i + 1])
            dist_km = dist_deg * DEG_TO_KM
            avg_speed = (spd + speeds[i + 1]) / 2.0
            if avg_speed > 0:
                elapsed += (dist_km / avg_speed) * 3600.0   # hours → seconds

    return telemetry


def profile_route(waypoints: List[Point2D],
                  start_time_s: float = 0.0) -> List[TelemetryPoint]:
    """
    Full pipeline: waypoints → kinematic telemetry with speed timestamps.

    Args:
        waypoints: Ordered (lat, lon) route waypoints.
        start_time_s: Route start time offset in seconds.

    Returns:
        List of (lat, lon, speed_kmh, timestamp_s) telemetry records.
    """
    raw_speeds = compute_curvature_speeds(waypoints)
    smooth_speeds = smooth_speed_profile(raw_speeds)
    return assign_timestamps(waypoints, smooth_speeds, start_time_s)


# ============================================================================
# REPORTING
# ============================================================================

def print_profile_stats(telemetry: List[TelemetryPoint]) -> None:
    """
    Print speed profile statistics to console.

    Args:
        telemetry: Output of profile_route().
    """
    speeds = [pt[2] for pt in telemetry]
    min_spd = min(speeds)
    max_spd = max(speeds)
    avg_spd = sum(speeds) / len(speeds)
    total_time_s = telemetry[-1][3] - telemetry[0][3] if len(telemetry) > 1 else 0.0

    print("\n" + "─" * 80)
    print("  KINEMATIC PROFILE STATS")
    print("─" * 80)
    print(f"  Waypoints processed:  {len(telemetry)}")
    print(f"  Min speed:            {min_spd:.1f} km/h  (sharp curves)")
    print(f"  Max speed:            {max_spd:.1f} km/h  (straight segments)")
    print(f"  Avg speed:            {avg_spd:.1f} km/h")
    print(f"  Route duration:       {total_time_s:.1f} seconds")
    print()
    print("  First 5 telemetry points:")
    print(f"  {'Lat':>12} {'Lon':>12} {'Speed(km/h)':>12} {'Time(s)':>10}")
    print("  " + "─" * 50)
    for pt in telemetry[:5]:
        print(f"  {pt[0]:12.6f} {pt[1]:12.6f} {pt[2]:12.1f} {pt[3]:10.1f}")
    print("─" * 80)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(BANNER)

    # Import bezier_path_generator sibling module for realistic waypoints
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from bezier_path_generator import batch_generate_routes

    print("  Generating 10 Bezier routes and applying kinematic velocity profiling...")
    routes = batch_generate_routes(count=10, seed=RANDOM_SEED)

    for idx, route in enumerate(routes):
        telemetry = profile_route(route)
        if idx == 0:
            print_profile_stats(telemetry)

    print(f"\n  Profiled {len(routes)} synthetic phantom routes.")
    print("  Prototype run complete. All data is unclassified synthetic output.\n")
