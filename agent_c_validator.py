#!/usr/bin/env python3
"""
Agent C Validator - QA Gate for Logistics Phantom Architecture
===============================================================

This script simulates 'Agent C' (The QA Gate) for the Logistics Phantom Architecture.
It demonstrates the computational viability of preventing friendly-fire data contamination
by validating phantom convoy coordinates against real convoy ground truth.

Key Features:
    - Generates 1 Real Convoy (5 lat/lon coordinates)
    - Generates 1,000 Phantom Convoys (each with 5 lat/lon coordinates)
    - Intentionally contaminates 5 Phantom convoys with near-collision coordinates
    - Validates all Phantom convoys against Real convoy using distance calculations
    - Flags and rejects any Phantom convoy within 2.0 km collision threshold
    - Reports processing metrics in milliseconds (sub-second latency)

Usage:
    python3 agent_c_validator.py

Author: Logistics Phantom PoC
Date: 2026
"""

import json
import math
import random
import time
from typing import List, Tuple, Dict


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

REAL_CONVOY_SIZE = 5                    # Number of waypoints per convoy
PHANTOM_CONVOY_COUNT = 1000             # Total phantom convoys to generate
COLLISION_THRESHOLD_KM = 2.0            # Distance threshold for collision detection
CONTAMINATION_COUNT = 5                 # Number of phantom convoys to intentionally contaminate
EARTH_RADIUS_KM = 6371.0                # Earth's mean radius in kilometers
RANDOM_SEED = 42                        # Fixed seed for reproducible output


# ============================================================================
# CORE MATHEMATICAL FUNCTIONS
# ============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Uses the Haversine formula, which provides accurate distances for points
    on a sphere. Returns distance in kilometers.

    Args:
        lat1 (float): Latitude of point 1 in degrees
        lon1 (float): Longitude of point 1 in degrees
        lat2 (float): Latitude of point 2 in degrees
        lon2 (float): Longitude of point 2 in degrees

    Returns:
        float: Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2

    c = 2 * math.asin(math.sqrt(a))
    distance = EARTH_RADIUS_KM * c

    return distance


def convoy_min_distance(real_convoy: List[Tuple[float, float]],
                       phantom_convoy: List[Tuple[float, float]]) -> float:
    """
    Calculate the minimum distance between any two waypoints across convoys.

    Iterates through all waypoint pairs and returns the closest proximity.
    This ensures we catch contaminated Phantom coordinates at any position.

    Args:
        real_convoy (List[Tuple[float, float]]): Real convoy waypoints (lat, lon)
        phantom_convoy (List[Tuple[float, float]]): Phantom convoy waypoints (lat, lon)

    Returns:
        float: Minimum distance in kilometers
    """
    min_distance = float('inf')

    for real_lat, real_lon in real_convoy:
        for phantom_lat, phantom_lon in phantom_convoy:
            distance = haversine_distance(real_lat, real_lon, phantom_lat, phantom_lon)
            min_distance = min(min_distance, distance)

    return min_distance


# ============================================================================
# DATA GENERATION FUNCTIONS
# ============================================================================

def generate_real_convoy() -> List[Tuple[float, float]]:
    """
    Generate a single Real Convoy with 5 waypoints.

    Creates a realistic convoy path by generating a center point and then
    creating nearby waypoints. Uses a base location representing a friendly asset.

    Returns:
        List[Tuple[float, float]]: List of (latitude, longitude) tuples
    """
    # Base location (center of real convoy)
    base_lat = 40.7128 + random.uniform(-0.1, 0.1)   # New York area ±0.1 degrees
    base_lon = -74.0060 + random.uniform(-0.1, 0.1)

    convoy = []
    for i in range(REAL_CONVOY_SIZE):
        # Create nearby waypoints (within ~5 km of base)
        offset_lat = random.uniform(-0.05, 0.05)
        offset_lon = random.uniform(-0.05, 0.05)
        lat = base_lat + offset_lat
        lon = base_lon + offset_lon
        convoy.append((lat, lon))

    return convoy


def generate_phantom_convoys(contamination_indices: List[int]) -> List[List[Tuple[float, float]]]:
    """
    Generate 1,000 Phantom Convoys, with intentional contamination.

    Most convoys are generated randomly across the globe. 5 specific convoys
    are intentionally contaminated with coordinates dangerously close to the
    Real Convoy to test the collision detection system.

    Args:
        contamination_indices (List[int]): Indices of convoys to intentionally contaminate

    Returns:
        List[List[Tuple[float, float]]]: List of phantom convoys
    """
    phantom_convoys = []

    for convoy_idx in range(PHANTOM_CONVOY_COUNT):
        convoy = []

        if convoy_idx in contamination_indices:
            # INTENTIONAL CONTAMINATION: Create waypoints very close to real convoy
            # We'll generate this relative to real_convoy after it's created
            # For now, mark this as a placeholder
            convoy = None  # Will be filled in by caller with real_convoy reference
        else:
            # NORMAL GENERATION: Random waypoints across the globe
            base_lat = random.uniform(-80, 80)
            base_lon = random.uniform(-180, 180)

            for _ in range(REAL_CONVOY_SIZE):
                offset_lat = random.uniform(-1, 1)
                offset_lon = random.uniform(-1, 1)
                lat = base_lat + offset_lat
                lon = base_lon + offset_lon
                convoy.append((lat, lon))

        phantom_convoys.append(convoy)

    return phantom_convoys


def inject_contamination(phantom_convoys: List[List[Tuple[float, float]]],
                        real_convoy: List[Tuple[float, float]],
                        contamination_indices: List[int]) -> None:
    """
    Inject intentional contamination into specific phantom convoys.

    Takes phantom convoys and modifies those at contamination_indices to have
    waypoints extremely close to (within 0.5-1.5 km of) the Real Convoy.

    Args:
        phantom_convoys (List[List[Tuple[float, float]]]): List of phantom convoys (modified in place)
        real_convoy (List[Tuple[float, float]]): Real convoy coordinates
        contamination_indices (List[int]): Indices of convoys to contaminate
    """
    for contamination_idx in contamination_indices:
        contaminated_convoy = []

        # For each waypoint in real convoy, create a nearby phantom waypoint
        for real_lat, real_lon in real_convoy:
            # Add a tiny offset to real coordinates (0.5-1.5 km away)
            # Approximately 1 degree lat = 111 km, so 0.005 degrees ≈ 0.5 km
            offset_lat = random.uniform(0.005, 0.015)
            offset_lon = random.uniform(0.005, 0.015)
            if random.choice([True, False]):
                offset_lat *= -1
            if random.choice([True, False]):
                offset_lon *= -1

            phantom_lat = real_lat + offset_lat
            phantom_lon = real_lon + offset_lon
            contaminated_convoy.append((phantom_lat, phantom_lon))

        phantom_convoys[contamination_idx] = contaminated_convoy


# ============================================================================
# VALIDATION ENGINE
# ============================================================================

def validate_phantom_convoys(real_convoy: List[Tuple[float, float]],
                            phantom_convoys: List[List[Tuple[float, float]]]) -> Dict:
    """
    Validate all phantom convoys against the real convoy.

    This is the core Agent C QA Gate logic. Iterates through all phantom convoys,
    calculates minimum distance to real convoy, and flags any that come within
    the collision threshold (2.0 km).

    Args:
        real_convoy (List[Tuple[float, float]]): Real convoy coordinates
        phantom_convoys (List[List[Tuple[float, float]]]): All phantom convoys

    Returns:
        Dict: Validation results including approved/rejected counts and collision details
    """
    approved_phantoms = []
    rejected_phantoms = []
    collision_details = []

    for phantom_idx, phantom_convoy in enumerate(phantom_convoys):
        min_distance = convoy_min_distance(real_convoy, phantom_convoy)

        if min_distance < COLLISION_THRESHOLD_KM:
            # COLLISION DETECTED: Reject this phantom
            rejected_phantoms.append(phantom_idx)
            collision_details.append({
                'phantom_id': phantom_idx,
                'min_distance_km': round(min_distance, 4),
                'status': 'REJECTED - Friendly-Fire Risk'
            })
        else:
            # SAFE: Approve for broadcast
            approved_phantoms.append(phantom_idx)

    return {
        'approved_count': len(approved_phantoms),
        'rejected_count': len(rejected_phantoms),
        'approved_indices': approved_phantoms,
        'rejected_indices': rejected_phantoms,
        'collision_details': collision_details
    }


# ============================================================================
# REPORTING FUNCTIONS
# ============================================================================

def print_banner():
    """Print the Agent C Validator banner."""
    print("\n" + "=" * 80)
    print("  AGENT C VALIDATOR - QA GATE FOR LOGISTICS PHANTOM ARCHITECTURE")
    print("=" * 80)
    print()


def print_summary_report(total_generated: int, results: Dict, processing_time_ms: float):
    """
    Print a clean, terminal-based summary report.

    Displays key metrics in a readable format, including latency measurements
    to prove sub-second processing capability.

    Args:
        total_generated (int): Total phantom convoys generated
        results (Dict): Validation results from validate_phantom_convoys()
        processing_time_ms (float): Total processing time in milliseconds
    """
    approved = results['approved_count']
    rejected = results['rejected_count']
    rejection_rate = (rejected / total_generated) * 100 if total_generated > 0 else 0

    print("\n" + "─" * 80)
    print("  VALIDATION SUMMARY REPORT")
    print("─" * 80)
    print()
    print(f"  Total Phantom Convoys Generated:        {total_generated:,}")
    print(f"  Phantoms Approved for Broadcast:        {approved:,} ({100-rejection_rate:.2f}%)")
    print(f"  Phantoms Rejected (Friendly-Fire Risk): {rejected:,} ({rejection_rate:.2f}%)")
    print()
    print(f"  Collision Threshold:                    {COLLISION_THRESHOLD_KM} kilometers")
    print()
    print(f"  Total Processing Time:                  {processing_time_ms:.2f} milliseconds")
    if processing_time_ms < 1000:
        print(f"  Status:                                 ✓ SUB-SECOND LATENCY ACHIEVED")
    print()
    print("─" * 80)

    # Detailed collision report
    if results['collision_details']:
        print("\n  COLLISION ANOMALIES DETECTED (Dangerously Close Phantoms):\n")
        print(f"  {'Phantom ID':<15} {'Min Distance (km)':<20} {'Status':<30}")
        print("  " + "─" * 65)
        for detail in results['collision_details']:
            phantom_id = detail['phantom_id']
            distance = detail['min_distance_km']
            status = detail['status']
            print(f"  {phantom_id:<15} {distance:<20} {status:<30}")
        print()


def print_footer():
    """Print footer with execution timestamp and prototype banner."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  Validation Executed: {timestamp}")
    print(f"  {BANNER}")
    print("=" * 80 + "\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution function for Agent C Validator.

    Orchestrates data generation, contamination injection, validation,
    and reporting.
    """
    # Fix random seed for reproducible output
    random.seed(RANDOM_SEED)

    # Start timing
    start_time = time.time()

    # Print banner
    print_banner()

    # Step 1: Generate Real Convoy
    print("  [1/5] Generating Real Convoy...")
    real_convoy = generate_real_convoy()

    # Step 2: Prepare contamination indices
    print("  [2/5] Preparing contamination indices...")
    contamination_indices = random.sample(range(PHANTOM_CONVOY_COUNT),
                                         CONTAMINATION_COUNT)

    # Step 3: Generate Phantom Convoys (with placeholders for contaminated ones)
    print("  [3/5] Generating 1,000 Phantom Convoys...")
    phantom_convoys = generate_phantom_convoys(contamination_indices)

    # Step 4: Inject contamination
    print("  [4/5] Injecting intentional contamination into 5 phantoms...")
    inject_contamination(phantom_convoys, real_convoy, contamination_indices)

    # Step 5: Validate all phantom convoys
    print("  [5/5] Executing Agent C validation engine...")
    results = validate_phantom_convoys(real_convoy, phantom_convoys)

    # Calculate processing time
    end_time = time.time()
    processing_time_ms = (end_time - start_time) * 1000

    # Print summary report
    print_summary_report(PHANTOM_CONVOY_COUNT, results, processing_time_ms)

    # Print footer
    print_footer()

    # Exit with appropriate code
    return 0


if __name__ == "__main__":
    exit(main())
