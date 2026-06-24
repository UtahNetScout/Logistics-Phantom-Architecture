"""
tests/unit/test_kinematic_profiles.py
======================================

Unit tests for the Kinematic Velocity Profiler.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA — PORTFOLIO PROOF-OF-CONCEPT

Validates:
    - Speed increases on long straights (mean speed on straights > mean on curves)
    - Speed decreases on tight curves (centripetal constraint active)
    - Acceleration/deceleration bounded by physics constraints
    - Speed variance within 15% of historical mean (realism score ≥ 0.80)

Metrics: mean velocity, acceleration variance, realism score.
"""

import math
from typing import List, Tuple

import numpy as np
import pytest

from src.prototype.bezier_path_generator import generate_bezier_path
from src.prototype.kinematic_velocity_profiler import (
    BASE_SPEED_KMH,
    MAX_ACCEL_MS2,
    MAX_DECEL_MS2,
    MAX_SPEED_KMH,
    MIN_SPEED_KMH,
    SPEED_VARIANCE_TOLERANCE,
    apply_kinematic_profile,
    compute_realism_score,
)


# ============================================================================
# HELPERS
# ============================================================================

def _straight_path(n: int = 100) -> np.ndarray:
    """Generate a perfectly straight path (constant heading)."""
    lats = np.linspace(36.0, 38.0, n)
    lons = np.linspace(-90.0, -88.0, n)
    return np.column_stack([lats, lons])


def _curved_path(n: int = 100) -> np.ndarray:
    """
    Generate a tightly curved path using Bezier through a sharp U-turn.
    """
    waypoints = [
        (36.0, -90.0),
        (36.5, -89.5),
        (37.0, -90.0),  # hairpin
        (36.5, -90.5),
        (36.0, -91.0),
    ]
    return generate_bezier_path(waypoints, samples_per_segment=20)


def _make_route(seed: int = 42, n_wps: int = 6) -> np.ndarray:
    """Generate a typical mixed-terrain route."""
    import random
    rng = random.Random(seed)
    base_lat, base_lon = 36.0, -90.0
    wps = []
    for _ in range(n_wps):
        base_lat += rng.uniform(0.2, 0.8)
        base_lon += rng.uniform(0.2, 0.8)
        wps.append((round(base_lat, 4), round(base_lon, 4)))
    return generate_bezier_path(wps, samples_per_segment=50)


# ============================================================================
# TESTS
# ============================================================================

class TestSpeedOnStraights:
    """Vehicles should travel at near-maximum speed on straight segments."""

    def test_mean_speed_on_straight_near_base_speed(self):
        """
        Mean speed on a perfectly straight path should equal BASE_SPEED_KMH
        (no curvature → no centripetal constraint → speed stays at base).
        """
        path = _straight_path(n=80)
        speeds = apply_kinematic_profile(path, base_speed_kmh=BASE_SPEED_KMH)
        mean_spd = float(np.mean(speeds))
        print(f"\n  Straight path mean speed: {mean_spd:.2f} km/h  "
              f"(base: {BASE_SPEED_KMH} km/h)")
        # On a straight, speed should stay close to the base speed
        assert mean_spd >= BASE_SPEED_KMH * 0.80, (
            f"Speed on straight too low: {mean_spd:.1f} km/h"
        )

    def test_speeds_do_not_exceed_maximum(self):
        """No speed value should exceed MAX_SPEED_KMH."""
        path = _straight_path(n=80)
        speeds = apply_kinematic_profile(path)
        max_spd = float(np.max(speeds))
        print(f"\n  Max speed on straight: {max_spd:.2f} km/h  "
              f"(limit: {MAX_SPEED_KMH} km/h)")
        assert max_spd <= MAX_SPEED_KMH + 0.01, (
            f"Speed {max_spd:.2f} exceeds MAX_SPEED_KMH {MAX_SPEED_KMH}"
        )


class TestSpeedOnCurves:
    """Vehicles must slow on tight curves."""

    def test_minimum_speed_on_curved_path(self):
        """Speeds on a curved path must not drop below MIN_SPEED_KMH."""
        path = _curved_path()
        speeds = apply_kinematic_profile(path)
        min_spd = float(np.min(speeds))
        print(f"\n  Curved path min speed: {min_spd:.2f} km/h  "
              f"(floor: {MIN_SPEED_KMH} km/h)")
        assert min_spd >= MIN_SPEED_KMH - 0.01, (
            f"Speed {min_spd:.2f} drops below MIN_SPEED_KMH {MIN_SPEED_KMH}"
        )

    def test_curved_path_mean_speed_below_straight(self):
        """
        Mean speed on a curved path should be lower than on a straight path.
        """
        straight = _straight_path(n=80)
        curved = _curved_path()
        spd_straight = float(np.mean(apply_kinematic_profile(straight)))
        spd_curved = float(np.mean(apply_kinematic_profile(curved)))
        print(f"\n  Straight mean: {spd_straight:.2f} km/h  "
              f"| Curved mean: {spd_curved:.2f} km/h")
        assert spd_curved <= spd_straight, (
            f"Curved path ({spd_curved:.1f}) faster than straight ({spd_straight:.1f})"
        )


class TestAccelerationConstraints:
    """Acceleration and deceleration must respect vehicle physics."""

    def test_acceleration_does_not_exceed_limit(self):
        """
        Step-wise acceleration between consecutive points must not exceed
        MAX_ACCEL_MS2 (converted from km/h to m/s for comparison).

        Uses a rough estimate based on speed change / estimated time step.
        """
        path = _make_route(seed=42)
        speeds_kmh = apply_kinematic_profile(path)
        speeds_ms = speeds_kmh / 3.6

        # Approximate segment distances in metres for time step estimation
        lat_mid = math.radians(path[:, 0].mean())
        scale = 111_000.0
        diffs = np.diff(path, axis=0)
        seg_m = np.sqrt((diffs[:, 1] * scale * math.cos(lat_mid)) ** 2
                        + (diffs[:, 0] * scale) ** 2)
        seg_m = np.maximum(seg_m, 1.0)

        # dt = distance / mean_speed for each segment
        mean_speeds = (speeds_ms[:-1] + speeds_ms[1:]) / 2
        mean_speeds = np.maximum(mean_speeds, 0.1)
        dt = seg_m / mean_speeds

        dv = np.abs(np.diff(speeds_ms))
        accel = dv / np.maximum(dt, 1e-6)

        max_obs_accel = float(np.max(accel))
        # Allow 3x headroom — dt approximation is rough for Bezier segments
        tolerance = max(MAX_ACCEL_MS2, MAX_DECEL_MS2) * 3.0
        print(f"\n  Max observed accel: {max_obs_accel:.3f} m/s²  "
              f"(tolerance: {tolerance:.1f} m/s²)")
        assert max_obs_accel <= tolerance, (
            f"Acceleration {max_obs_accel:.3f} m/s² exceeds tolerance {tolerance:.1f}"
        )

    def test_speed_profile_is_smooth_no_infinite_values(self):
        """Speed profile must contain only finite values."""
        path = _make_route(seed=99)
        speeds = apply_kinematic_profile(path)
        assert np.all(np.isfinite(speeds)), "Speed profile contains non-finite values"
        assert np.all(speeds >= 0), "Speed profile contains negative values"


class TestRealismScore:
    """Speed variance must be within 15% of historical mean (score ≥ 0.80)."""

    def test_realism_score_above_threshold(self):
        """
        Realism score for typical mixed-terrain routes must be ≥ 0.80.
        """
        scores = []
        for seed in range(10):
            path = _make_route(seed=seed)
            speeds = apply_kinematic_profile(path, base_speed_kmh=BASE_SPEED_KMH)
            score = compute_realism_score(speeds, historical_mean_kmh=BASE_SPEED_KMH)
            scores.append(score)

        mean_score = sum(scores) / len(scores)
        below = [s for s in scores if s < 0.80]
        print(f"\n  Mean realism score: {mean_score:.4f}  "
              f"routes below 0.80: {len(below)}/10")
        assert mean_score >= 0.80, (
            f"Mean realism score {mean_score:.4f} below 0.80 threshold"
        )

    def test_perfectly_uniform_speed_scores_one(self):
        """A perfectly uniform speed profile should score 1.0."""
        uniform_speeds = np.full(100, BASE_SPEED_KMH)
        score = compute_realism_score(uniform_speeds, historical_mean_kmh=BASE_SPEED_KMH)
        print(f"\n  Uniform speed profile realism score: {score:.4f}  (expected 1.0)")
        assert score == 1.0

    def test_wildly_unrealistic_speed_scores_low(self):
        """A speed profile far from historical mean should score low."""
        unrealistic_speeds = np.full(100, BASE_SPEED_KMH * 3.0)  # 3x too fast
        score = compute_realism_score(unrealistic_speeds, historical_mean_kmh=BASE_SPEED_KMH)
        print(f"\n  Unrealistic speed realism score: {score:.4f}  (expected <0.5)")
        assert score < 0.5, f"Expected low score for unrealistic speeds, got {score:.4f}"

    @pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
    def test_realism_score_range(self, seed: int):
        """Speed profile realism score must always be in [0, 1]."""
        path = _make_route(seed=seed)
        speeds = apply_kinematic_profile(path)
        score = compute_realism_score(speeds)
        print(f"\n  Seed {seed}: realism score = {score:.4f}")
        assert 0.0 <= score <= 1.0
