#!/usr/bin/env python3
"""
Agent B Parallel Swarm Generator - Logistics Phantom Architecture
=================================================================

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA
PORTFOLIO PROOF-OF-CONCEPT — NOT OPERATIONAL TELEMETRY
NOT DEPLOYMENT-READY DECEPTION TOOLING

Simulates Agent B's role in the Logistics Phantom Architecture: generating
large batches of synthetic phantom convoy records in parallel. Uses Python
multiprocessing to achieve near-linear speedup across CPU cores.

Key Features:
    - Configurable phantom multiplier (100x, 250x, 1000x)
    - Speed profiles constrained to realistic logistics range (35–55 km/h)
    - Rest stops at realistic intervals (fuel/crew rotation, 150–300 km)
    - Temporal jitter of ±30 minutes per waypoint
    - Deterministic with fixed random seeds for reproducibility
    - Printed metrics: generation time, phantom count, per-phantom latency

Usage:
    python3 agent_b_parallel_swarm_generator.py

Author: Logistics Phantom Prototype
Date: 2026
"""

import math
import random
import time
from multiprocessing import Pool, cpu_count
from typing import Dict, List, Optional, Tuple

# ============================================================================
# BANNER
# ============================================================================

BANNER = (
    "UNCLASSIFIED SYNTHETIC PROTOTYPE DATA | "
    "PORTFOLIO PROOF-OF-CONCEPT | "
    "NOT OPERATIONAL TELEMETRY"
)

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

WAYPOINTS_PER_PHANTOM: int = 8          # Waypoints per phantom convoy route
MIN_SPEED_KMH: float = 35.0             # Minimum logistics vehicle speed (km/h)
MAX_SPEED_KMH: float = 55.0             # Maximum logistics vehicle speed (km/h)
REST_INTERVAL_KM_MIN: float = 150.0     # Minimum distance between rest stops (km)
REST_INTERVAL_KM_MAX: float = 300.0     # Maximum distance between rest stops (km)
TEMPORAL_JITTER_MIN_MIN: float = -30.0  # Minimum temporal jitter (minutes)
TEMPORAL_JITTER_MAX_MIN: float = 30.0   # Maximum temporal jitter (minutes)
GEO_LAT_MIN: float = 30.0              # Geographic bounding box — min latitude
GEO_LAT_MAX: float = 50.0              # Geographic bounding box — max latitude
GEO_LON_MIN: float = -100.0            # Geographic bounding box — min longitude
GEO_LON_MAX: float = -70.0             # Geographic bounding box — max longitude
EARTH_RADIUS_KM: float = 6371.0

# ============================================================================
# PURE FUNCTIONS (picklable for multiprocessing)
# ============================================================================


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two lat/lon points."""
    r = EARTH_RADIUS_KM
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _generate_single_phantom(args: Tuple[int, int]) -> Dict:
    """
    Generate one phantom convoy record.

    Designed as a module-level function so it can be pickled by multiprocessing.

    Args:
        args: Tuple of (phantom_index, base_seed)

    Returns:
        Dict containing phantom_id, waypoints, speed_profile_kmh,
        rest_stops, and timestamp_offsets_min.
    """
    phantom_idx, base_seed = args
    rng = random.Random(base_seed + phantom_idx)

    # Generate route waypoints within geographic bounds
    base_lat = rng.uniform(GEO_LAT_MIN, GEO_LAT_MAX)
    base_lon = rng.uniform(GEO_LON_MIN, GEO_LON_MAX)
    waypoints: List[Tuple[float, float]] = []
    for _ in range(WAYPOINTS_PER_PHANTOM):
        lat = base_lat + rng.uniform(-2.0, 2.0)
        lon = base_lon + rng.uniform(-2.0, 2.0)
        lat = max(GEO_LAT_MIN - 5, min(GEO_LAT_MAX + 5, lat))
        lon = max(GEO_LON_MIN - 5, min(GEO_LON_MAX + 5, lon))
        waypoints.append((round(lat, 6), round(lon, 6)))
        base_lat = lat
        base_lon = lon

    # Build speed profile — one speed per leg
    speed_profile: List[float] = []
    for _ in range(len(waypoints) - 1):
        speed = rng.uniform(MIN_SPEED_KMH, MAX_SPEED_KMH)
        speed_profile.append(round(speed, 2))

    # Compute cumulative distances and schedule rest stops
    rest_stops: List[int] = []
    cumulative_km = 0.0
    next_rest_km = rng.uniform(REST_INTERVAL_KM_MIN, REST_INTERVAL_KM_MAX)
    for i in range(len(waypoints) - 1):
        seg_km = _haversine_km(*waypoints[i], *waypoints[i + 1])
        cumulative_km += seg_km
        if cumulative_km >= next_rest_km:
            rest_stops.append(i + 1)
            cumulative_km = 0.0
            next_rest_km = rng.uniform(REST_INTERVAL_KM_MIN, REST_INTERVAL_KM_MAX)

    # Apply temporal jitter to each waypoint timestamp
    timestamp_offsets_min: List[float] = [
        round(rng.uniform(TEMPORAL_JITTER_MIN_MIN, TEMPORAL_JITTER_MAX_MIN), 2)
        for _ in waypoints
    ]

    return {
        "phantom_id": phantom_idx,
        "waypoints": waypoints,
        "speed_profile_kmh": speed_profile,
        "rest_stops": rest_stops,
        "timestamp_offsets_min": timestamp_offsets_min,
    }


# ============================================================================
# PUBLIC API
# ============================================================================


def generate_phantom_swarm(
    num_phantoms: int,
    seed: int = 42,
    n_workers: Optional[int] = None,
) -> List[Dict]:
    """
    Generate a swarm of synthetic phantom convoy records in parallel.

    Uses Python multiprocessing.Pool to distribute work across CPU cores,
    achieving near-linear speedup for large phantom counts.

    Args:
        num_phantoms: Total number of phantom convoys to generate.
        seed: Base random seed for deterministic output.
        n_workers: Worker processes (defaults to cpu_count()).

    Returns:
        List of phantom dicts, each containing waypoints, speed profile,
        rest stops, and temporal jitter offsets.
    """
    if n_workers is None:
        n_workers = max(1, cpu_count())

    args = [(i, seed) for i in range(num_phantoms)]

    if n_workers == 1:
        # Serial fallback (also used in test environments without fork support)
        return [_generate_single_phantom(a) for a in args]

    with Pool(processes=n_workers) as pool:
        results = pool.map(_generate_single_phantom, args)

    return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main() -> int:
    """Run Agent B swarm generation at 100x, 250x, and 1000x multipliers."""
    print("\n" + "=" * 70)
    print("  AGENT B PARALLEL SWARM GENERATOR")
    print(f"  {BANNER}")
    print("=" * 70)

    multipliers = [100, 250, 1000]
    for multiplier in multipliers:
        t0 = time.perf_counter()
        phantoms = generate_phantom_swarm(num_phantoms=multiplier, seed=42)
        elapsed = time.perf_counter() - t0

        latency_ms = elapsed * 1000
        per_phantom_us = (elapsed / multiplier) * 1_000_000

        print(f"\n  Multiplier : {multiplier}x")
        print(f"  Generated  : {len(phantoms):,} phantom convoys")
        print(f"  Total time : {latency_ms:.1f} ms")
        print(f"  Per phantom: {per_phantom_us:.1f} µs")
        sample = phantoms[0]
        print(f"  Sample ID  : {sample['phantom_id']}")
        print(f"  Waypoints  : {len(sample['waypoints'])}")
        print(f"  Rest stops : {sample['rest_stops']}")
        speeds = sample["speed_profile_kmh"]
        print(f"  Speed range: {min(speeds):.1f}–{max(speeds):.1f} km/h")

    print("\n" + "=" * 70)
    print("  Prototype complete. All data synthetic.")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
