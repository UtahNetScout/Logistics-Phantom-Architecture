#!/usr/bin/env python3
"""
UNCLASSIFIED SYNTHETIC PROTOTYPE - Portfolio Proof-of-Concept

unclassified synthetic prototype data
portfolio proof-of-concept
not operational telemetry
not deployment-ready deception tooling
prototype for research/portfolio purposes

Agent B Parallel Swarm Generator
================================
Generates synthetic phantom convoy telemetry in parallel from abstract seed
parameters. This module is a reproducible portfolio prototype only.
"""

from __future__ import annotations

import multiprocessing as mp
import random
import statistics
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

try:
    from .bezier_path_generator import generate_bezier_path
    from .kinematic_velocity_profiler import generate_velocity_profile
except ImportError:
    from bezier_path_generator import generate_bezier_path
    from kinematic_velocity_profiler import generate_velocity_profile


DEFAULT_SEED = 20260624


@dataclass(frozen=True)
class SwarmSeed:
    """Abstract seed parameters supplied by upstream routing logic."""

    distance_km: float
    duration_hours: float
    terrain_type: str
    asset_count: int


@dataclass(frozen=True)
class GenerationMetrics:
    """Performance summary for synthetic parallel swarm generation."""

    generation_time_s: float
    phantom_count: int
    latency_per_record_ms: float


def _build_waypoints(seed: SwarmSeed, rng: random.Random) -> List[Tuple[float, float]]:
    """Construct abstract synthetic waypoint anchors (not real coordinates)."""
    segment = seed.distance_km / 3.0
    return [
        (0.0, 0.0),
        (segment, rng.uniform(-0.4, 0.4) * segment),
        (2.0 * segment, rng.uniform(-0.4, 0.4) * segment),
        (seed.distance_km, rng.uniform(-0.2, 0.2) * segment),
    ]


def _single_convoy_task(args: Tuple[int, SwarmSeed, int]) -> Dict:
    """Generate one synthetic convoy record with path, speed, rest, and noise."""
    record_id, seed, worker_seed = args
    rng = random.Random(worker_seed)

    waypoints = _build_waypoints(seed, rng)
    path_points, _ = generate_bezier_path(
        waypoints=waypoints,
        duration_hours=seed.duration_hours,
        samples_per_segment=18,
        seed=worker_seed,
    )
    velocity_profile, _ = generate_velocity_profile(
        path_points=[(p["x_km"], p["y_km"]) for p in path_points],
        terrain_type=seed.terrain_type,
        seed=worker_seed + 97,
    )

    rest_stop_count = rng.randint(1, 3)
    rest_stops = sorted(rng.sample(range(1, max(2, len(path_points) - 1)), k=rest_stop_count))

    sensor_noise = {
        "position_noise_m": round(rng.uniform(1.5, 12.0), 3),
        "speed_noise_kmh": round(rng.uniform(0.2, 1.6), 3),
        "timestamp_jitter_s": round(rng.uniform(0.0, 2.5), 3),
    }

    return {
        "phantom_id": f"phantom-{record_id:05d}",
        "terrain_type": seed.terrain_type,
        "path": path_points,
        "velocity_profile": velocity_profile,
        "rest_stops": rest_stops,
        "sensor_noise": sensor_noise,
    }


def generate_parallel_phantom_swarm(seed: SwarmSeed, base_seed: int = DEFAULT_SEED) -> Tuple[List[Dict], GenerationMetrics]:
    """
    Generate 100-1000 synthetic phantom convoy records in parallel.

    The phantom count scales from abstract `asset_count` and is clamped to
    [100, 1000] for repeatable prototype runs.
    """
    start = time.perf_counter()

    phantom_count = max(100, min(1000, seed.asset_count * 120))
    args = [(idx, seed, base_seed + idx) for idx in range(phantom_count)]

    with mp.Pool(processes=min(8, mp.cpu_count())) as pool:
        convoys = pool.map(_single_convoy_task, args)

    duration = time.perf_counter() - start
    metrics = GenerationMetrics(
        generation_time_s=round(duration, 3),
        phantom_count=phantom_count,
        latency_per_record_ms=round((duration * 1000.0) / phantom_count, 3),
    )
    return convoys, metrics


def main() -> None:
    """Run a deterministic parallel generation demonstration."""
    seed = SwarmSeed(distance_km=180.0, duration_hours=6.0, terrain_type="desert", asset_count=5)
    convoys, metrics = generate_parallel_phantom_swarm(seed)

    speed_means = [statistics.mean(v["speed_kmh"] for v in c["velocity_profile"]) for c in convoys[:10]]
    print("UNCLASSIFIED SYNTHETIC PROTOTYPE - Portfolio Proof-of-Concept")
    print("Not operational telemetry | Not deployment-ready | Prototype for research/portfolio purposes")
    print(f"Phantom convoy count: {metrics.phantom_count}")
    print(f"Generation time (s): {metrics.generation_time_s}")
    print(f"Latency per record (ms): {metrics.latency_per_record_ms}")
    print(f"Sample mean speed over first 10 convoys (km/h): {round(statistics.mean(speed_means), 3)}")


if __name__ == "__main__":
    main()
