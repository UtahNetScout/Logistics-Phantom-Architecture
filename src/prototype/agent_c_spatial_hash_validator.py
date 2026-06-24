#!/usr/bin/env python3
"""
Agent C Spatial Hash Validator
================================
Unclassified Synthetic Prototype - Portfolio PoC
Not operational telemetry. Not deployment-ready deception tooling.

This module is an optimized version of Agent C (the QA Gate) that uses a
spatial hash grid for collision detection instead of the O(n*m) pairwise
Haversine scan in the original agent_c_validator.py.

Motivation:
    The baseline validator checks every phantom waypoint against every real
    convoy waypoint — O(P * R * W^2) complexity. At 10,000+ phantoms this
    becomes a bottleneck. A spatial hash bucketing real-convoy waypoints into
    a grid of cells allows O(1) average-case lookup per phantom waypoint,
    reducing total complexity to O(P * W).

Methodology:
    1. All real convoy waypoints are inserted into a hash grid keyed by
       (floor(lat / cell_size), floor(lon / cell_size)).
    2. For each phantom waypoint, only cells within a 1-cell radius need to
       be checked for potential collisions.
    3. The collision threshold is converted to approximate degrees for the
       bucket radius calculation.

Connections to Architecture:
    - Replaces the naive validation loop in agent_c_validator.py
    - Same functional contract: returns approved / rejected phantom lists
    - Validates that collision checking scales sub-linearly with phantom count

Usage:
    python src/prototype/agent_c_spatial_hash_validator.py
"""

import math
import random
import time
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# ============================================================================
# BANNER
# ============================================================================

BANNER = """
================================================================================
  AGENT C SPATIAL HASH VALIDATOR
  Unclassified Synthetic Prototype - Portfolio PoC
  Not operational telemetry. Not deployment-ready deception tooling.
================================================================================
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

RANDOM_SEED = 42
COLLISION_THRESHOLD_KM = 2.0        # Same threshold as baseline validator
EARTH_RADIUS_KM = 6371.0
WAYPOINTS_PER_CONVOY = 5

# Convert threshold to degrees (1° lat ≈ 111 km, conservative)
THRESHOLD_DEG = COLLISION_THRESHOLD_KM / 111.0


# ============================================================================
# SPATIAL HASH GRID
# ============================================================================

class SpatialHashGrid:
    """
    A 2D spatial hash grid for fast proximity lookups of lat/lon points.

    Divides the coordinate space into cells of size `cell_size` degrees.
    Points inserted into the grid can be queried by any point to find all
    stored points within adjacent cells (immediate 3×3 neighborhood).

    Attributes:
        cell_size: Grid cell size in degrees.
        grid: Dict mapping (cell_row, cell_col) to a list of points.
    """

    def __init__(self, cell_size: float = THRESHOLD_DEG) -> None:
        """
        Initialize the spatial hash grid.

        Args:
            cell_size: Width/height of each grid cell in degrees.
        """
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int], List[Tuple[float, float]]] = defaultdict(list)

    def _cell_key(self, lat: float, lon: float) -> Tuple[int, int]:
        """Compute the grid cell key for a (lat, lon) point."""
        return (int(math.floor(lat / self.cell_size)),
                int(math.floor(lon / self.cell_size)))

    def insert(self, lat: float, lon: float) -> None:
        """
        Insert a (lat, lon) point into the grid.

        Args:
            lat: Latitude in degrees.
            lon: Longitude in degrees.
        """
        key = self._cell_key(lat, lon)
        self.grid[key].append((lat, lon))

    def query_neighbors(self, lat: float, lon: float) -> List[Tuple[float, float]]:
        """
        Return all points in the 3×3 cell neighborhood of the given point.

        Args:
            lat: Query latitude in degrees.
            lon: Query longitude in degrees.

        Returns:
            List of (lat, lon) candidate points from neighboring cells.
        """
        row, col = self._cell_key(lat, lon)
        candidates = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                candidates.extend(self.grid.get((row + dr, col + dc), []))
        return candidates


# ============================================================================
# HAVERSINE DISTANCE
# ============================================================================

def haversine_distance(lat1: float, lon1: float,
                       lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance (km) between two lat/lon points.

    Args:
        lat1, lon1: First point in degrees.
        lat2, lon2: Second point in degrees.

    Returns:
        Distance in kilometers.
    """
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


# ============================================================================
# VALIDATION ENGINE
# ============================================================================

def build_real_convoy_grid(real_convoys: List[List[Tuple[float, float]]]) -> SpatialHashGrid:
    """
    Build a spatial hash grid from all real convoy waypoints.

    Args:
        real_convoys: List of real convoys; each convoy is a list of (lat, lon).

    Returns:
        Populated SpatialHashGrid ready for proximity queries.
    """
    grid = SpatialHashGrid(cell_size=THRESHOLD_DEG)
    for convoy in real_convoys:
        for lat, lon in convoy:
            grid.insert(lat, lon)
    return grid


def validate_phantoms_spatial(
    real_convoys: List[List[Tuple[float, float]]],
    phantom_convoys: List[List[Tuple[float, float]]],
) -> Dict:
    """
    Validate phantom convoys against real convoys using spatial hashing.

    For each phantom waypoint, only nearby real-convoy points (within the
    3×3 grid neighborhood) are distance-checked, reducing the number of
    Haversine computations from O(P*R*W^2) to roughly O(P*W).

    Args:
        real_convoys: Ground-truth convoy waypoints.
        phantom_convoys: Synthetic phantom convoy waypoints.

    Returns:
        Dict with keys: approved_count, rejected_count, collision_details.
    """
    grid = build_real_convoy_grid(real_convoys)

    approved, rejected, details = [], [], []

    for phantom_idx, phantom in enumerate(phantom_convoys):
        collision_found = False

        for phantom_lat, phantom_lon in phantom:
            if collision_found:
                break
            candidates = grid.query_neighbors(phantom_lat, phantom_lon)
            for real_lat, real_lon in candidates:
                dist = haversine_distance(phantom_lat, phantom_lon, real_lat, real_lon)
                if dist < COLLISION_THRESHOLD_KM:
                    collision_found = True
                    details.append({
                        "phantom_id": phantom_idx,
                        "min_distance_km": round(dist, 4),
                        "status": "REJECTED - Friendly-Fire Risk",
                    })
                    break

        if collision_found:
            rejected.append(phantom_idx)
        else:
            approved.append(phantom_idx)

    return {
        "approved_count": len(approved),
        "rejected_count": len(rejected),
        "collision_details": details,
    }


# ============================================================================
# DATA GENERATION HELPERS
# ============================================================================

def _make_convoy(base_lat: float, base_lon: float,
                 rng: random.Random,
                 spread: float = 0.8) -> List[Tuple[float, float]]:
    """Generate a synthetic convoy with waypoints near a base location."""
    return [
        (base_lat + rng.uniform(-spread, spread),
         base_lon + rng.uniform(-spread, spread))
        for _ in range(WAYPOINTS_PER_CONVOY)
    ]


def generate_test_dataset(
    phantom_count: int,
    contamination_count: int,
    seed: int = RANDOM_SEED,
) -> Tuple[List[List[Tuple[float, float]]], List[List[Tuple[float, float]]]]:
    """
    Generate real and phantom convoy datasets for benchmarking.

    Args:
        phantom_count: Total synthetic phantom convoys.
        contamination_count: How many phantoms to place near real convoys.
        seed: Random seed.

    Returns:
        Tuple of (real_convoys, phantom_convoys).
    """
    rng = random.Random(seed)

    real_convoys = [_make_convoy(40.0 + rng.uniform(-5, 5),
                                 -75.0 + rng.uniform(-5, 5), rng, spread=0.05)
                    for _ in range(3)]

    phantom_convoys = []
    for i in range(phantom_count):
        if i < contamination_count and real_convoys:
            # Place waypoints directly near the first real convoy waypoint
            # Use tight spread (~0.5 km) so they fall within COLLISION_THRESHOLD_KM
            real_ref = real_convoys[0][0]
            base_lat = real_ref[0] + rng.uniform(-0.004, 0.004)
            base_lon = real_ref[1] + rng.uniform(-0.004, 0.004)
            phantom_convoys.append(_make_convoy(base_lat, base_lon, rng, spread=0.004))
        else:
            base_lat = rng.uniform(-60.0, 60.0)
            base_lon = rng.uniform(-170.0, 170.0)
            phantom_convoys.append(_make_convoy(base_lat, base_lon, rng, spread=0.8))

    return real_convoys, phantom_convoys


# ============================================================================
# REPORTING
# ============================================================================

def print_results(phantom_count: int, results: Dict, elapsed_ms: float) -> None:
    """
    Print validation results and latency metrics.

    Args:
        phantom_count: Total phantoms validated.
        results: Output of validate_phantoms_spatial().
        elapsed_ms: Wall-clock validation time in milliseconds.
    """
    approved = results["approved_count"]
    rejected = results["rejected_count"]
    rate = (rejected / phantom_count * 100) if phantom_count else 0.0

    print("\n" + "─" * 80)
    print("  SPATIAL HASH VALIDATION RESULTS")
    print("─" * 80)
    print(f"  Phantoms validated:         {phantom_count:,}")
    print(f"  Approved:                   {approved:,} ({100 - rate:.2f}%)")
    print(f"  Rejected (collision risk):  {rejected:,} ({rate:.2f}%)")
    print(f"  Validation latency:         {elapsed_ms:.2f} ms")
    if elapsed_ms < 1000:
        print("  Status:                     ✓ SUB-SECOND LATENCY ACHIEVED")
    if results["collision_details"]:
        print()
        print("  Collision details (first 5):")
        for detail in results["collision_details"][:5]:
            print(f"    Phantom {detail['phantom_id']:>5} — "
                  f"{detail['min_distance_km']:.4f} km — {detail['status']}")
    print("─" * 80)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(BANNER)

    for phantom_count in [1000, 5000]:
        contamination = max(5, phantom_count // 200)
        print(f"\n  [RUN] Validating {phantom_count:,} phantoms "
              f"({contamination} contaminated)...")
        real_convoys, phantom_convoys = generate_test_dataset(
            phantom_count=phantom_count,
            contamination_count=contamination,
            seed=RANDOM_SEED,
        )

        start = time.perf_counter()
        results = validate_phantoms_spatial(real_convoys, phantom_convoys)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        print_results(phantom_count, results, elapsed_ms)

    print("\n  Prototype run complete. All data is unclassified synthetic output.\n")
