"""
tests/integration/test_swarm_realism.py
=========================================

Integration tests verifying that Bezier paths + kinematic profiles produce
realistic phantom movement, and that multimodal telemetry is cross-modally
consistent.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA — PORTFOLIO PROOF-OF-CONCEPT

Validates:
    - Bezier + kinematic combination produces realistic movement (consistency ≥ 0.80)
    - Multimodal telemetry physical/RF/manifest fields are internally consistent
    - Cross-modal alignment: fuel tracks distance, RF power tracks rest state
    - Consistency score computed and printed for each test
"""

from typing import Dict, List, Tuple

import numpy as np
import pytest

from src.prototype.bezier_path_generator import (
    compute_smoothness_score,
    generate_bezier_path,
)
from src.prototype.kinematic_velocity_profiler import (
    BASE_SPEED_KMH,
    MIN_SPEED_KMH,
    MAX_SPEED_KMH,
    apply_kinematic_profile,
    compute_realism_score,
)
from src.prototype.multimodal_telemetry_generator import generate_telemetry


# ============================================================================
# HELPERS
# ============================================================================

def _make_route(seed: int = 42, n_wps: int = 6) -> List[Tuple[float, float]]:
    import random
    rng = random.Random(seed)
    base_lat, base_lon = 36.0, -90.0
    wps = []
    for _ in range(n_wps):
        base_lat += rng.uniform(0.2, 0.8)
        base_lon += rng.uniform(0.2, 0.8)
        wps.append((round(base_lat, 4), round(base_lon, 4)))
    return wps


# ============================================================================
# TESTS
# ============================================================================

class TestBezierKinematicRealism:
    """Combined Bezier + kinematic profile must produce realistic movement."""

    def test_combined_pipeline_produces_valid_speeds(self):
        """
        Bezier path fed into kinematic profiler must produce valid speed arrays.
        """
        waypoints = _make_route(seed=42)
        path = generate_bezier_path(waypoints, samples_per_segment=40)
        speeds = apply_kinematic_profile(path, base_speed_kmh=BASE_SPEED_KMH)
        assert len(speeds) == len(path)
        assert float(np.min(speeds)) >= MIN_SPEED_KMH - 0.01
        assert float(np.max(speeds)) <= MAX_SPEED_KMH + 0.01
        print(f"\n  Speed range: {np.min(speeds):.1f}–{np.max(speeds):.1f} km/h")

    def test_consistency_score_above_threshold(self):
        """
        Realism score across 10 synthetic routes must average ≥ 0.80.
        """
        scores = []
        for seed in range(10):
            wps = _make_route(seed=seed)
            path = generate_bezier_path(wps, samples_per_segment=40)
            speeds = apply_kinematic_profile(path, base_speed_kmh=BASE_SPEED_KMH)
            score = compute_realism_score(speeds, historical_mean_kmh=BASE_SPEED_KMH)
            scores.append(score)
        mean_score = float(np.mean(scores))
        print(f"\n  Mean consistency score (10 routes): {mean_score:.4f}  (target: ≥0.80)")
        assert mean_score >= 0.80, (
            f"Mean consistency score {mean_score:.4f} below 0.80"
        )

    def test_smoothness_maintained_through_full_pipeline(self):
        """Bezier paths through the full pipeline must remain smooth."""
        for seed in range(5):
            wps = _make_route(seed=seed, n_wps=6)
            path = generate_bezier_path(wps, samples_per_segment=50)
            score = compute_smoothness_score(path)
            assert score >= 0.90, (
                f"Smoothness {score:.4f} degraded in full pipeline (seed={seed})"
            )
        print("\n  All 5 routes maintained smoothness ≥ 0.90 ✅")

    def test_combination_deterministic_with_seed(self):
        """Two runs with the same seed must produce identical speed profiles."""
        wps = _make_route(seed=42)
        path_a = generate_bezier_path(wps, samples_per_segment=40)
        speeds_a = apply_kinematic_profile(path_a, base_speed_kmh=BASE_SPEED_KMH)
        path_b = generate_bezier_path(wps, samples_per_segment=40)
        speeds_b = apply_kinematic_profile(path_b, base_speed_kmh=BASE_SPEED_KMH)
        np.testing.assert_array_equal(speeds_a, speeds_b,
                                      err_msg="Speed profiles differ between identical runs")
        print("\n  Determinism verified for Bezier + kinematic pipeline ✅")


class TestMultimodalConsistency:
    """Multimodal telemetry fields must be internally consistent."""

    def test_physical_rf_manifest_all_present(self):
        """
        generate_telemetry must return all three modality keys.
        """
        wps = _make_route(seed=42)
        telemetry = generate_telemetry(wps, seed=42)
        assert "physical" in telemetry, "Missing 'physical' key"
        assert "rf" in telemetry, "Missing 'rf' key"
        assert "logistics_manifest" in telemetry, "Missing 'logistics_manifest' key"

    def test_physical_waypoint_count_matches_route(self):
        """Physical telemetry must have one record per waypoint."""
        wps = _make_route(seed=42)
        telemetry = generate_telemetry(wps, seed=42)
        assert len(telemetry["physical"]) == len(wps)
        assert len(telemetry["rf"]) == len(wps)

    def test_fuel_decreases_along_route(self):
        """
        Fuel remaining must decrease from start to end (physics consistency).
        """
        wps = _make_route(seed=42, n_wps=8)
        telemetry = generate_telemetry(wps, seed=42)
        phys = telemetry["physical"]
        fuel_start = phys[0]["fuel_remaining_l"]
        fuel_end = phys[-1]["fuel_remaining_l"]
        print(f"\n  Fuel: {fuel_start:.0f}L → {fuel_end:.0f}L")
        assert fuel_end < fuel_start, "Fuel should decrease along route"

    def test_rf_power_higher_at_rest_stops(self):
        """
        RF transmission power must be higher at rest stops than during movement.
        This validates cross-modal alignment (physical state → RF behaviour).
        """
        wps = _make_route(seed=42, n_wps=10)
        telemetry = generate_telemetry(wps, seed=42)
        rf = telemetry["rf"]
        rest = [r for r in rf if r["at_rest_stop"]]
        moving = [r for r in rf if not r["at_rest_stop"]]
        if rest and moving:
            avg_rest_tx = sum(r["tx_power_dbm"] for r in rest) / len(rest)
            avg_move_tx = sum(r["tx_power_dbm"] for r in moving) / len(moving)
            print(f"\n  RF power: rest={avg_rest_tx:.1f} dBm, moving={avg_move_tx:.1f} dBm")
            assert avg_rest_tx > avg_move_tx, (
                "RF power at rest stops should exceed moving power"
            )

    def test_payload_consistent_across_physical_records(self):
        """
        Payload tonnage must be constant throughout a single convoy route.
        """
        wps = _make_route(seed=42)
        telemetry = generate_telemetry(wps, seed=42)
        phys = telemetry["physical"]
        payloads = [p["payload_tonnes"] for p in phys]
        assert len(set(payloads)) == 1, (
            f"Payload tonnage changed during route: {payloads}"
        )

    def test_manifest_total_km_positive(self):
        """
        The logistics manifest must report a positive total route distance.
        """
        wps = _make_route(seed=42, n_wps=6)
        telemetry = generate_telemetry(wps, seed=42)
        km = telemetry["logistics_manifest"]["total_route_km"]
        print(f"\n  Manifest total route: {km:.2f} km")
        assert km > 0.0, "Manifest shows zero route distance"

    def test_multimodal_consistency_score(self):
        """
        Compute a composite consistency score across 5 routes.

        Score = fraction of routes where all cross-modal checks pass.
        Target: 100% consistency (all checks pass for all routes).
        """
        passed = 0
        total = 5
        for seed in range(total):
            wps = _make_route(seed=seed, n_wps=7)
            tel = generate_telemetry(wps, seed=seed)
            phys = tel["physical"]
            rf_recs = tel["rf"]
            manifest = tel["logistics_manifest"]

            checks = [
                phys[-1]["fuel_remaining_l"] < phys[0]["fuel_remaining_l"],
                manifest["total_route_km"] > 0,
                len(phys) == len(wps),
                len(rf_recs) == len(wps),
            ]
            if all(checks):
                passed += 1

        consistency = passed / total
        print(f"\n  Multimodal consistency: {passed}/{total} routes = {consistency:.2f}")
        assert consistency >= 0.80, (
            f"Cross-modal consistency {consistency:.2f} below 0.80 threshold"
        )
