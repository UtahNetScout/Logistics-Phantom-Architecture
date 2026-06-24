#!/usr/bin/env python3
"""
UNCLASSIFIED SYNTHETIC PROTOTYPE - Portfolio Proof-of-Concept

unclassified synthetic prototype data
portfolio proof-of-concept
not operational telemetry
not deployment-ready deception tooling
prototype for research/portfolio purposes

Bezier Path Generator
=====================
Builds smooth synthetic convoy paths from abstract waypoints using cubic Bezier
interpolation and reports prototype path-quality metrics.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


DEFAULT_SEED = 20260624
Point = Tuple[float, float]


@dataclass(frozen=True)
class PathMetrics:
    """Aggregate metrics for generated Bezier path prototypes."""

    path_smoothness_score: float
    waypoint_accuracy_km: float
    generation_latency_ms: float


def cubic_bezier(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    """Evaluate a cubic Bezier curve at interpolation factor ``t`` in [0, 1]."""
    mt = 1.0 - t
    x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
    y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
    return x, y


def _distance(a: Point, b: Point) -> float:
    """Return Euclidean distance in synthetic kilometer space."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _control_points(waypoints: Sequence[Point], rng: random.Random) -> List[Tuple[Point, Point, Point, Point]]:
    """Construct Bezier segment controls from adjacent waypoints."""
    segments: List[Tuple[Point, Point, Point, Point]] = []
    for i in range(len(waypoints) - 1):
        p0 = waypoints[i]
        p3 = waypoints[i + 1]
        dx, dy = p3[0] - p0[0], p3[1] - p0[1]
        jitter_x = rng.uniform(-0.12, 0.12)
        jitter_y = rng.uniform(-0.12, 0.12)
        p1 = (p0[0] + dx / 3.0 + jitter_x, p0[1] + dy / 3.0 + jitter_y)
        p2 = (p0[0] + 2.0 * dx / 3.0 - jitter_x, p0[1] + 2.0 * dy / 3.0 - jitter_y)
        segments.append((p0, p1, p2, p3))
    return segments


def generate_bezier_path(
    waypoints: Sequence[Point],
    duration_hours: float,
    samples_per_segment: int = 25,
    seed: int = DEFAULT_SEED,
) -> Tuple[List[dict], PathMetrics]:
    """
    Generate smooth synthetic route points and per-point temporal distribution.

    Args:
        waypoints: Abstract synthetic waypoints in kilometer coordinate space.
        duration_hours: Total route duration for timestamp allocation.
        samples_per_segment: Number of sampled points per Bezier segment.
        seed: Deterministic random seed for repeatable control-point jitter.

    Returns:
        Tuple of point dictionaries and aggregate metrics.
    """
    if len(waypoints) < 2:
        raise ValueError("At least two waypoints are required")
    if duration_hours <= 0:
        raise ValueError("duration_hours must be positive")

    start = time.perf_counter()
    rng = random.Random(seed)
    segments = _control_points(waypoints, rng)

    segment_lengths = [_distance(p0, p3) for p0, _, _, p3 in segments]
    total_length = max(sum(segment_lengths), 1e-9)

    path_points: List[dict] = []
    elapsed_seconds = 0.0

    for seg_idx, (p0, p1, p2, p3) in enumerate(segments):
        segment_seconds = duration_hours * 3600.0 * (segment_lengths[seg_idx] / total_length)
        for i in range(samples_per_segment):
            t = i / max(samples_per_segment - 1, 1)
            x, y = cubic_bezier(p0, p1, p2, p3, t)
            timestamp = elapsed_seconds + t * segment_seconds
            path_points.append(
                {
                    "segment": seg_idx,
                    "t": round(t, 4),
                    "x_km": round(x, 4),
                    "y_km": round(y, 4),
                    "time_s": round(timestamp, 2),
                }
            )
        elapsed_seconds += segment_seconds

    heading_changes: List[float] = []
    for i in range(1, len(path_points) - 1):
        a = (path_points[i]["x_km"] - path_points[i - 1]["x_km"], path_points[i]["y_km"] - path_points[i - 1]["y_km"])
        b = (path_points[i + 1]["x_km"] - path_points[i]["x_km"], path_points[i + 1]["y_km"] - path_points[i]["y_km"])
        mag = math.hypot(*a) * math.hypot(*b)
        if mag <= 1e-9:
            continue
        cosine = max(-1.0, min(1.0, (a[0] * b[0] + a[1] * b[1]) / mag))
        heading_changes.append(abs(math.acos(cosine)))

    avg_turn_radians = sum(heading_changes) / max(len(heading_changes), 1)
    smoothness_score = max(0.0, 1.0 - avg_turn_radians / math.pi)

    waypoint_errors = []
    sampled_xy = [(p["x_km"], p["y_km"]) for p in path_points]
    for wp in waypoints:
        waypoint_errors.append(min(_distance(wp, pt) for pt in sampled_xy))
    waypoint_accuracy = sum(waypoint_errors) / max(len(waypoint_errors), 1)

    metrics = PathMetrics(
        path_smoothness_score=round(smoothness_score, 4),
        waypoint_accuracy_km=round(waypoint_accuracy, 4),
        generation_latency_ms=round((time.perf_counter() - start) * 1000.0, 3),
    )
    return path_points, metrics


def _example_waypoints() -> List[Point]:
    """Return deterministic synthetic waypoints from abstract seed parameters."""
    return [(0.0, 0.0), (8.0, 5.0), (16.0, 4.0), (24.0, 11.0)]


def main() -> None:
    """Run a reproducible prototype Bezier generation example."""
    waypoints = _example_waypoints()
    path, metrics = generate_bezier_path(waypoints=waypoints, duration_hours=5.5, samples_per_segment=20)

    print("UNCLASSIFIED SYNTHETIC PROTOTYPE - Portfolio Proof-of-Concept")
    print("Not operational telemetry | Not deployment-ready | Prototype for research/portfolio purposes")
    print(f"Generated points: {len(path)}")
    print(f"Path smoothness score: {metrics.path_smoothness_score}")
    print(f"Waypoint accuracy (km): {metrics.waypoint_accuracy_km}")
    print(f"Latency (ms): {metrics.generation_latency_ms}")


if __name__ == "__main__":
    main()
