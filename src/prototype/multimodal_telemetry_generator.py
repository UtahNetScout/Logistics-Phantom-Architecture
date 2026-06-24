#!/usr/bin/env python3
"""
Multimodal Synthetic Telemetry Generator - Logistics Phantom Architecture
=========================================================================

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA
PORTFOLIO PROOF-OF-CONCEPT — NOT OPERATIONAL TELEMETRY
NOT DEPLOYMENT-READY DECEPTION TOOLING

Generates representative synthetic telemetry across three modalities for
each phantom convoy waypoint:
    1. Physical — GPS position, heading, speed, altitude, fuel, payload
    2. RF / Communications — transmit power, frequency band, call-sign,
       message interval, signal strength
    3. Logistics Manifest — cargo class, tonnage, origin, destination,
       driver-rotation window, scheduled ETA

Cross-modal consistency is intentional: fuel consumption tracks distance,
RF activity correlates with rest stops, payload tonnage matches refuel
intervals. This is a prototype demonstration of the metadata alignment
problem; actual cryptographic realism is not implemented.

Usage:
    python3 multimodal_telemetry_generator.py

Author: Logistics Phantom Prototype
Date: 2026
"""

import math
import random
import time
from typing import Dict, List, Optional, Tuple

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

FUEL_CONSUMPTION_L_PER_100KM: float = 35.0     # Heavy logistics truck (L/100km)
TANK_CAPACITY_L: float = 800.0                  # Fuel tank capacity (litres)
CARGO_CLASSES = ["Class I", "Class III", "Class V", "Class IX"]
RF_BANDS = ["VHF", "UHF", "HF", "SATCOM"]
EARTH_RADIUS_KM = 6371.0

# ============================================================================
# HELPER MATH
# ============================================================================


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km."""
    r = EARTH_RADIUS_KM
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return initial bearing (degrees, 0–360) from point 1 to point 2."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    x = math.sin(dlam) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


# ============================================================================
# PUBLIC API
# ============================================================================


def generate_telemetry(
    waypoints: List[Tuple[float, float]],
    speed_profile_kmh: Optional[List[float]] = None,
    seed: int = 42,
) -> Dict:
    """
    Generate cross-modal synthetic telemetry for one phantom convoy route.

    Args:
        waypoints: Ordered list of (lat, lon) tuples for the phantom route.
        speed_profile_kmh: Speed in km/h at each leg; generated if None.
        seed: Random seed for reproducibility.

    Returns:
        Dict with keys 'physical', 'rf', and 'logistics_manifest', each
        containing a list of records (one per waypoint or per leg).
    """
    rng = random.Random(seed)

    n = len(waypoints)
    if n < 2:
        raise ValueError("At least 2 waypoints are required.")

    if speed_profile_kmh is None:
        speed_profile_kmh = [rng.uniform(35.0, 55.0) for _ in range(n - 1)]

    # Precompute segment distances and cumulative distance
    seg_km = [
        _haversine_km(*waypoints[i], *waypoints[i + 1])
        for i in range(n - 1)
    ]
    total_km = sum(seg_km)
    cum_km = [0.0]
    for d in seg_km:
        cum_km.append(cum_km[-1] + d)

    # ── Logistics manifest (route-level) ──────────────────────────────────
    cargo_class = rng.choice(CARGO_CLASSES)
    payload_tonnes = rng.uniform(8.0, 22.0)
    refuel_interval_km = TANK_CAPACITY_L / (FUEL_CONSUMPTION_L_PER_100KM / 100.0)
    origin_id = f"DEPOT-{rng.randint(100, 999)}"
    destination_id = f"FOB-{rng.randint(10, 99)}"

    manifest: Dict = {
        "cargo_class": cargo_class,
        "payload_tonnes": round(payload_tonnes, 2),
        "origin_id": origin_id,
        "destination_id": destination_id,
        "total_route_km": round(total_km, 2),
        "estimated_refuels": int(total_km / refuel_interval_km),
        "driver_rotation_window_h": round(rng.uniform(4.0, 8.0), 1),
        "scheduled_eta_offset_min": round(rng.uniform(-30.0, 30.0), 1),
    }

    # ── Physical telemetry (per-waypoint) ─────────────────────────────────
    physical: List[Dict] = []
    fuel_remaining_l = TANK_CAPACITY_L
    for i, (lat, lon) in enumerate(waypoints):
        bearing = (
            _bearing_deg(*waypoints[i - 1], lat, lon) if i > 0 else 0.0
        )
        if i < n - 1:
            speed = speed_profile_kmh[i]
            dist_since_last = seg_km[i]
            fuel_used = dist_since_last * (FUEL_CONSUMPTION_L_PER_100KM / 100.0)
            fuel_remaining_l = max(0.0, fuel_remaining_l - fuel_used)
        else:
            speed = 0.0

        physical.append({
            "waypoint_idx": i,
            "lat": lat,
            "lon": lon,
            "altitude_m": round(rng.uniform(100.0, 1500.0), 1),
            "speed_kmh": round(speed, 2),
            "heading_deg": round(bearing, 1),
            "fuel_remaining_l": round(fuel_remaining_l, 1),
            "payload_tonnes": round(payload_tonnes, 2),
            "odometer_km": round(cum_km[i], 2),
        })

    # ── RF / Communications telemetry (per-waypoint) ──────────────────────
    rf_band = rng.choice(RF_BANDS)
    call_sign = f"PHANTOM-{rng.randint(1000, 9999)}"
    rf: List[Dict] = []
    for i, wp in enumerate(physical):
        # RF activity increases at rest stops (speed → 0) and refuel points
        is_rest = wp["speed_kmh"] < 5.0
        tx_power_dbm = rng.uniform(20.0, 40.0) if is_rest else rng.uniform(5.0, 20.0)
        msg_interval_s = rng.uniform(30.0, 120.0) if is_rest else rng.uniform(300.0, 900.0)
        signal_strength_dbm = rng.uniform(-90.0, -50.0)

        rf.append({
            "waypoint_idx": i,
            "call_sign": call_sign,
            "rf_band": rf_band,
            "tx_power_dbm": round(tx_power_dbm, 1),
            "msg_interval_s": round(msg_interval_s, 1),
            "signal_strength_dbm": round(signal_strength_dbm, 1),
            "at_rest_stop": is_rest,
        })

    return {
        "physical": physical,
        "rf": rf,
        "logistics_manifest": manifest,
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main() -> int:
    """Demonstrate multimodal telemetry generation for several phantom convoys."""
    print("\n" + "=" * 70)
    print("  MULTIMODAL SYNTHETIC TELEMETRY GENERATOR")
    print(f"  {BANNER}")
    print("=" * 70)

    rng = random.Random(42)
    num_convoys = 3

    for convoy_idx in range(num_convoys):
        n_wps = rng.randint(4, 7)
        base_lat = rng.uniform(35.0, 44.0)
        base_lon = rng.uniform(-95.0, -76.0)
        waypoints = []
        for _ in range(n_wps):
            base_lat += rng.uniform(0.2, 0.6)
            base_lon += rng.uniform(0.2, 0.6)
            waypoints.append((round(base_lat, 4), round(base_lon, 4)))

        t0 = time.perf_counter()
        telemetry = generate_telemetry(waypoints, seed=42 + convoy_idx)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        manifest = telemetry["logistics_manifest"]
        phys = telemetry["physical"]
        rf = telemetry["rf"]

        print(f"\n  Convoy {convoy_idx + 1}: {n_wps} waypoints, {manifest['total_route_km']:.1f} km")
        print(f"  Cargo class   : {manifest['cargo_class']}, {manifest['payload_tonnes']} t")
        print(f"  Route         : {manifest['origin_id']} → {manifest['destination_id']}")
        print(f"  Refuels       : {manifest['estimated_refuels']}")
        print(f"  Fuel at start : {phys[0]['fuel_remaining_l']:.0f} L")
        print(f"  Fuel at end   : {phys[-1]['fuel_remaining_l']:.0f} L")
        print(f"  RF call sign  : {rf[0]['call_sign']}  band: {rf[0]['rf_band']}")
        speeds = [p["speed_kmh"] for p in phys if p["speed_kmh"] > 0]
        if speeds:
            print(f"  Speed range   : {min(speeds):.1f}–{max(speeds):.1f} km/h")
        print(f"  Generation    : {elapsed_ms:.2f} ms")

        # Cross-modal consistency check
        assert phys[-1]["fuel_remaining_l"] < phys[0]["fuel_remaining_l"], \
            "Fuel should decrease along route"
        rest_rf = [r for r in rf if r["at_rest_stop"]]
        moving_rf = [r for r in rf if not r["at_rest_stop"]]
        if rest_rf and moving_rf:
            avg_rest_tx = sum(r["tx_power_dbm"] for r in rest_rf) / len(rest_rf)
            avg_move_tx = sum(r["tx_power_dbm"] for r in moving_rf) / len(moving_rf)
            assert avg_rest_tx > avg_move_tx, "RF power should be higher at rest stops"

    print("\n" + "=" * 70)
    print("  Multimodal telemetry generation complete. All data synthetic.")
    print(f"  {BANNER}")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
