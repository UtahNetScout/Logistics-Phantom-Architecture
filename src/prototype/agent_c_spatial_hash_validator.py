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

Agent C Spatial Hash Validator
==============================
Prototype spatial-hash collision gate for screening synthetic phantom records
against synthetic friendly ground truth at high throughput.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple


DEFAULT_SEED = 20260624
Point = Tuple[float, float]


@dataclass(frozen=True)
class ValidationMetrics:
    """Summary of spatial hash validation throughput and quality."""

    validation_time_ms: float
    rejection_count: int
    throughput_rps: float
    false_positive_rate: float


def _distance(a: Point, b: Point) -> float:
    """Euclidean distance in synthetic kilometer coordinate space."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _hash_cell(point: Point, cell_size_km: float) -> Tuple[int, int]:
    """Map a point to a 2D spatial hash cell."""
    return int(point[0] // cell_size_km), int(point[1] // cell_size_km)


def generate_ground_truth(real_count: int = 120, seed: int = DEFAULT_SEED) -> List[Point]:
    """Generate synthetic friendly convoy points (non-operational coordinates)."""
    rng = random.Random(seed)
    return [(rng.uniform(0, 500), rng.uniform(0, 500)) for _ in range(real_count)]


def generate_phantom_records(
    count: int = 1500,
    contaminated_count: int = 20,
    ground_truth: Sequence[Point] | None = None,
    seed: int = DEFAULT_SEED,
) -> Tuple[List[Point], Set[int]]:
    """Generate phantom points with a known subset intentionally near ground truth."""
    if ground_truth is None:
        ground_truth = generate_ground_truth(seed=seed)

    rng = random.Random(seed + 1)
    phantoms = [(rng.uniform(0, 500), rng.uniform(0, 500)) for _ in range(count)]

    contaminated_indices = set(rng.sample(range(count), k=min(contaminated_count, count)))
    for idx in contaminated_indices:
        base = rng.choice(list(ground_truth))
        phantoms[idx] = (base[0] + rng.uniform(-2.0, 2.0), base[1] + rng.uniform(-2.0, 2.0))

    return phantoms, contaminated_indices


def validate_with_spatial_hash(
    ground_truth: Sequence[Point],
    phantoms: Sequence[Point],
    threshold_km: float = 5.0,
) -> Tuple[Set[int], ValidationMetrics]:
    """
    Reject phantom records that collide with ground truth within ``threshold_km``.

    Uses a spatial hash map to constrain pairwise checks to neighboring cells.
    """
    start = time.perf_counter()
    cell_size = threshold_km

    grid: Dict[Tuple[int, int], List[Point]] = {}
    for pt in ground_truth:
        grid.setdefault(_hash_cell(pt, cell_size), []).append(pt)

    rejected_indices: Set[int] = set()
    for idx, pt in enumerate(phantoms):
        cx, cy = _hash_cell(pt, cell_size)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for real in grid.get((cx + dx, cy + dy), []):
                    if _distance(pt, real) <= threshold_km:
                        rejected_indices.add(idx)
                        break
                if idx in rejected_indices:
                    break
            if idx in rejected_indices:
                break

    elapsed_ms = (time.perf_counter() - start) * 1000.0
    metrics = ValidationMetrics(
        validation_time_ms=round(elapsed_ms, 3),
        rejection_count=len(rejected_indices),
        throughput_rps=round(len(phantoms) / max(elapsed_ms / 1000.0, 1e-9), 2),
        false_positive_rate=0.0,
    )
    return rejected_indices, metrics


def score_false_positive_rate(rejected: Set[int], contaminated: Set[int], total_phantoms: int) -> float:
    """Compute false-positive rate using the total number of clean records."""
    false_positives = len(rejected - contaminated)
    clean_total = max(total_phantoms - len(contaminated), 1)
    return false_positives / clean_total


def main() -> None:
    """Execute validator demonstration on 1,500 synthetic phantom records."""
    ground_truth = generate_ground_truth()
    phantoms, contaminated = generate_phantom_records(ground_truth=ground_truth)
    rejected, metrics = validate_with_spatial_hash(ground_truth, phantoms)

    fp_rate = score_false_positive_rate(rejected, contaminated, total_phantoms=len(phantoms))

    print("UNCLASSIFIED SYNTHETIC PROTOTYPE - Portfolio Proof-of-Concept")
    print("Not operational telemetry | Not deployment-ready | Prototype for research/portfolio purposes")
    print(f"Ground truth points: {len(ground_truth)}")
    print(f"Phantom points validated: {len(phantoms)}")
    print(f"Validation time (ms): {metrics.validation_time_ms}")
    print(f"Rejected phantoms: {metrics.rejection_count}")
    print(f"Throughput (records/s): {metrics.throughput_rps}")
    print(f"False positive rate: {round(fp_rate, 4)}")


if __name__ == "__main__":
    main()
