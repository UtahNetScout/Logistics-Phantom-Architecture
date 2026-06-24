#!/usr/bin/env python3
"""
Kinematic Velocity Profiler - Logistics Phantom Architecture
============================================================

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA
PORTFOLIO PROOF-OF-CONCEPT — NOT OPERATIONAL TELEMETRY
NOT DEPLOYMENT-READY DECEPTION TOOLING

Applies physics-inspired velocity profiles to smooth phantom convoy paths.
Vehicles slow on curves (centripetal acceleration limit) and accelerate on
straights, mimicking real logistics vehicle behavior. This increases phantom
realism compared to constant-speed or pure-noise approaches.

Key Features:
    - Speed reduction proportional to path curvature (radius of curvature)
    - Acceleration/deceleration bounded by realistic vehicle constraints
    - Speed variance within 15% of historical mean across a segment
    - Deterministic with fixed seeds
    - Printed metrics: mean velocity, acceleration variance, realism score

Usage:
    python3 kinematic_velocity_profiler.py

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

MIN_SPEED_KMH: float = 20.0            # Absolute minimum speed (km/h) on sharp turns
MAX_SPEED_KMH: float = 65.0            # Absolute maximum speed (km/h) on straights
BASE_SPEED_KMH: float = 45.0           # Historical mean logistics speed (km/h)
MAX_ACCEL_MS2: float = 1.5             # Maximum acceleration (m/s²)
MAX_DECEL_MS2: float = 2.5             # Maximum deceleration / braking (m/s²)
MAX_LATERAL_ACCEL_MS2: float = 3.0     # Centripetal acceleration limit (m/s²)
SPEED_VARIANCE_TOLERANCE: float = 0.15 # Speed variance must be within 15% of mean

# ============================================================================
# CURVATURE COMPUTATION
# ============================================================================


def _compute_curvature(path: np.ndarray) -> np.ndarray:
    """
    Estimate the signed curvature at each interior path point.

    Uses the standard three-point formula. End points are assigned zero
    curvature (treated as straight).

    Args:
        path: Array of shape (N, 2) with (lat, lon) in degrees.

    Returns:
        Array of shape (N,) with curvature values (1/m, approximately).
    """
    n = len(path)
    curvature = np.zeros(n)
    if n < 3:
        return curvature

    # Work in approximate Cartesian metres for local geometry
    # 1 degree latitude ≈ 111_000 m; longitude scaled by cos(lat)
    lat_mid = math.radians(path[:, 0].mean())
    scale_lat = 111_000.0
    scale_lon = 111_000.0 * math.cos(lat_mid)

    xy = np.column_stack([path[:, 1] * scale_lon, path[:, 0] * scale_lat])

    for i in range(1, n - 1):
        a = xy[i - 1]
        b = xy[i]
        c = xy[i + 1]
        ab = np.linalg.norm(b - a)
        bc = np.linalg.norm(c - b)
        ac = np.linalg.norm(c - a)
        # Area of triangle via cross product
        cross = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        denom = ab * bc * ac
        curvature[i] = (2 * cross / denom) if denom > 1e-6 else 0.0

    return curvature


# ============================================================================
# PUBLIC API
# ============================================================================


def apply_kinematic_profile(
    path: np.ndarray,
    base_speed_kmh: float = BASE_SPEED_KMH,
) -> np.ndarray:
    """
    Compute a physically-constrained speed profile along a path.

    Steps:
      1. Compute curvature at each point.
      2. Derive maximum safe speed from centripetal acceleration limit.
      3. Clip to [MIN_SPEED_KMH, MAX_SPEED_KMH].
      4. Apply forward/backward smoothing passes to respect accel/decel limits.

    Args:
        path: Array of shape (N, 2) with (lat, lon) in degrees.
        base_speed_kmh: Nominal cruising speed used as the starting speed.

    Returns:
        Array of shape (N,) with speed in km/h at each path point.
    """
    n = len(path)
    if n < 2:
        return np.full(n, base_speed_kmh)

    curvature = _compute_curvature(path)

    # Maximum speed from centripetal limit: v² ≤ a_max / κ  →  v ≤ sqrt(a/κ)
    speed = np.full(n, base_speed_kmh)
    for i in range(n):
        kappa = curvature[i]
        if kappa > 1e-6:
            v_max_ms = math.sqrt(MAX_LATERAL_ACCEL_MS2 / kappa)
            v_max_kmh = v_max_ms * 3.6
            speed[i] = min(speed[i], v_max_kmh)

    speed = np.clip(speed, MIN_SPEED_KMH, MAX_SPEED_KMH)

    # Compute approximate segment lengths in metres
    lat_mid = math.radians(path[:, 0].mean())
    scale_lat = 111_000.0
    scale_lon = 111_000.0 * math.cos(lat_mid)
    diffs = np.diff(path, axis=0)
    seg_m = np.sqrt((diffs[:, 1] * scale_lon) ** 2 + (diffs[:, 0] * scale_lat) ** 2)
    seg_m = np.maximum(seg_m, 1.0)  # avoid division by zero

    def _accel_limited(spd: np.ndarray, max_accel: float) -> np.ndarray:
        """Apply a single-pass acceleration limit (forward direction)."""
        out = spd.copy()
        for i in range(1, n):
            ds = seg_m[i - 1]
            # v² ≤ v_prev² + 2·a·ds  →  v ≤ sqrt(v_prev² + 2·a·ds)
            v_max = math.sqrt(out[i - 1] ** 2 + 2 * max_accel * ds / 3.6 ** 2) * 3.6
            if out[i] > v_max:
                out[i] = v_max
        return out

    # Forward pass: limit acceleration
    speed = _accel_limited(speed, MAX_ACCEL_MS2)
    # Backward pass: limit deceleration (reverse speed array, then reverse back)
    speed = _accel_limited(speed[::-1], MAX_DECEL_MS2)[::-1]

    return speed


def compute_realism_score(
    speed_profile: np.ndarray,
    historical_mean_kmh: float = BASE_SPEED_KMH,
) -> float:
    """
    Compute a realism score (0–1) for a speed profile.

    Score = 1.0 if speed variance is within SPEED_VARIANCE_TOLERANCE of the
    historical mean, linearly decaying to 0.0 at twice the tolerance.

    Args:
        speed_profile: Array of speed values in km/h.
        historical_mean_kmh: Expected mean speed.

    Returns:
        Realism score in [0, 1].
    """
    if len(speed_profile) == 0:
        return 0.0
    mean_spd = float(np.mean(speed_profile))
    deviation = abs(mean_spd - historical_mean_kmh) / historical_mean_kmh
    if deviation <= SPEED_VARIANCE_TOLERANCE:
        return 1.0
    elif deviation <= 2 * SPEED_VARIANCE_TOLERANCE:
        return 1.0 - (deviation - SPEED_VARIANCE_TOLERANCE) / SPEED_VARIANCE_TOLERANCE
    return 0.0


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main() -> int:
    """Run kinematic profiling on several synthetic phantom routes."""
    print("\n" + "=" * 70)
    print("  KINEMATIC VELOCITY PROFILER")
    print(f"  {BANNER}")
    print("=" * 70)

    try:
        from .bezier_path_generator import generate_bezier_path  # package/module context
    except ImportError:
        from bezier_path_generator import generate_bezier_path  # standalone script context

    rng = random.Random(42)
    num_routes = 5

    for route_idx in range(num_routes):
        n_wps = rng.randint(5, 10)
        base_lat = rng.uniform(35.0, 45.0)
        base_lon = rng.uniform(-95.0, -75.0)
        waypoints: List[Tuple[float, float]] = []
        for _ in range(n_wps):
            base_lat += rng.uniform(0.2, 0.8)
            base_lon += rng.uniform(0.2, 0.8)
            waypoints.append((round(base_lat, 4), round(base_lon, 4)))

        path = generate_bezier_path(waypoints, samples_per_segment=40)

        t0 = time.perf_counter()
        speed_profile = apply_kinematic_profile(path)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        mean_v = float(np.mean(speed_profile))
        std_v = float(np.std(speed_profile))
        accel_var = float(np.var(np.diff(speed_profile)))
        realism = compute_realism_score(speed_profile)

        print(f"\n  Route {route_idx + 1}: {len(path)} path points")
        print(f"  Mean velocity        : {mean_v:.2f} km/h")
        print(f"  Speed std-dev        : {std_v:.2f} km/h")
        print(f"  Acceleration variance: {accel_var:.4f}")
        print(f"  Realism score        : {realism:.3f}  (target: >0.80)")
        print(f"  Profiling time       : {elapsed_ms:.2f} ms")
        assert mean_v >= MIN_SPEED_KMH, f"Mean speed {mean_v:.1f} below minimum"
        assert mean_v <= MAX_SPEED_KMH, f"Mean speed {mean_v:.1f} above maximum"
        assert realism >= 0.80, f"Realism score {realism:.3f} below 0.80"

    print("\n" + "=" * 70)
    print("  All routes passed kinematic realism checks.")
    print(f"  {BANNER}")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
