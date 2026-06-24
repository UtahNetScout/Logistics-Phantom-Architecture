#!/usr/bin/env python3
"""
UNCLASSIFIED SYNTHETIC PROTOTYPE - Portfolio Proof-of-Concept

unclassified synthetic prototype data
portfolio proof-of-concept
not operational telemetry
not deployment-ready deception tooling
Not operational telemetry
Not deployment-ready
Prototype for research/portfolio purposes

Kinematic Velocity Profiler
===========================
Builds synthetic speed/acceleration traces that decelerate through curves and
accelerate on straights while respecting terrain constraints.
"""

from __future__ import annotations

import math
import random
import statistics
import time
from dataclasses import dataclass
from typing import List, Sequence, Tuple


DEFAULT_SEED = 20260624
Point = Tuple[float, float]


@dataclass(frozen=True)
class VelocityMetrics:
    """Summary metrics for prototype velocity profile realism."""

    mean_velocity_kmh: float
    acceleration_variance: float
    realism_score: float
    generation_latency_ms: float


TERRAIN_SPEED_LIMITS = {
    "desert": 75.0,
    "urban": 45.0,
    "mountain": 35.0,
    "plains": 65.0,
}


def _curvature(path: Sequence[Point], idx: int) -> float:
    """Estimate local turning angle in radians."""
    a = (path[idx][0] - path[idx - 1][0], path[idx][1] - path[idx - 1][1])
    b = (path[idx + 1][0] - path[idx][0], path[idx + 1][1] - path[idx][1])
    mag = math.hypot(*a) * math.hypot(*b)
    if mag <= 1e-9:
        return 0.0
    cosine = max(-1.0, min(1.0, (a[0] * b[0] + a[1] * b[1]) / mag))
    return math.acos(cosine)


def generate_velocity_profile(
    path_points: Sequence[Point],
    terrain_type: str,
    seed: int = DEFAULT_SEED,
    time_step_s: float = 10.0,
) -> Tuple[List[dict], VelocityMetrics]:
    """
    Generate synthetic kinematic telemetry for a path.

    Args:
        path_points: Ordered synthetic route points in kilometer space.
        terrain_type: Terrain category controlling speed limits.
        seed: Deterministic random seed.
        time_step_s: Time delta between points.

    Returns:
        Per-point velocity/acceleration records and aggregate metrics.
    """
    if len(path_points) < 3:
        raise ValueError("At least three path points are required")

    start = time.perf_counter()
    rng = random.Random(seed)
    speed_limit = TERRAIN_SPEED_LIMITS.get(terrain_type, 50.0)

    records: List[dict] = []
    prev_speed = speed_limit * 0.6

    for idx in range(1, len(path_points) - 1):
        curve = _curvature(path_points, idx)
        curve_penalty = min(0.55, curve / math.pi)

        target_speed = speed_limit * (1.0 - curve_penalty)
        if curve < 0.20:
            target_speed = min(speed_limit, target_speed + 6.0)

        delta = target_speed - prev_speed
        accel_limit = 2.2
        acceleration = max(-accel_limit, min(accel_limit, delta / (time_step_s / 3.6)))

        speed = max(5.0, prev_speed + acceleration * (time_step_s / 3.6))
        speed += rng.uniform(-1.8, 1.8)
        speed = max(5.0, min(speed, speed_limit))

        records.append(
            {
                "index": idx,
                "speed_kmh": round(speed, 3),
                "accel_mps2": round(acceleration, 4),
                "curve_radians": round(curve, 4),
            }
        )
        prev_speed = speed

    speeds = [r["speed_kmh"] for r in records]
    accelerations = [r["accel_mps2"] for r in records]

    straight_speed = statistics.mean(r["speed_kmh"] for r in records if r["curve_radians"] < 0.2) if any(
        r["curve_radians"] < 0.2 for r in records
    ) else statistics.mean(speeds)
    curve_speed = statistics.mean(r["speed_kmh"] for r in records if r["curve_radians"] >= 0.2) if any(
        r["curve_radians"] >= 0.2 for r in records
    ) else straight_speed
    curve_compliance = 1.0 if straight_speed <= 0 else max(0.0, min(1.0, (straight_speed - curve_speed) / straight_speed))

    accel_var = statistics.pvariance(accelerations) if len(accelerations) > 1 else 0.0
    smooth_accel = max(0.0, 1.0 - min(accel_var / 2.5, 1.0))
    realism = 0.6 * curve_compliance + 0.4 * smooth_accel

    metrics = VelocityMetrics(
        mean_velocity_kmh=round(statistics.mean(speeds), 3),
        acceleration_variance=round(accel_var, 5),
        realism_score=round(realism, 4),
        generation_latency_ms=round((time.perf_counter() - start) * 1000.0, 3),
    )
    return records, metrics


def _example_path() -> List[Point]:
    """Return deterministic synthetic path points for demonstration."""
    return [(0.0, 0.0), (3.0, 1.0), (7.0, 4.0), (12.0, 3.0), (16.0, 7.0), (21.0, 9.0)]


def main() -> None:
    """Run a standalone profiler demonstration."""
    profile, metrics = generate_velocity_profile(_example_path(), terrain_type="desert")

    print("UNCLASSIFIED SYNTHETIC PROTOTYPE - Portfolio Proof-of-Concept")
    print("Not operational telemetry | Not deployment-ready | Prototype for research/portfolio purposes")
    print(f"Profile points: {len(profile)}")
    print(f"Mean velocity (km/h): {metrics.mean_velocity_kmh}")
    print(f"Acceleration variance: {metrics.acceleration_variance}")
    print(f"Realism score: {metrics.realism_score}")
    print(f"Latency (ms): {metrics.generation_latency_ms}")


if __name__ == "__main__":
    main()
