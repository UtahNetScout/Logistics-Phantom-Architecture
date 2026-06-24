#!/usr/bin/env python3
"""
Agent B Parallel Swarm Generator
=================================
Unclassified Synthetic Prototype - Portfolio PoC
Not operational telemetry. Not deployment-ready deception tooling.

This module demonstrates Agent B's capability to generate large batches of
synthetic phantom convoy telemetry using Python's multiprocessing library.
It validates one prototype assumption: that parallel generation can achieve
100x-1000x phantom multipliers within practical latency budgets.

Methodology:
    - Spawns a configurable number of worker processes via multiprocessing.Pool
    - Each worker generates a batch of synthetic phantom convoy records
    - Records include randomized but plausible waypoint sequences
    - Deterministic seeds allow reproducible benchmark runs
    - Throughput and latency metrics are printed to console

Connections to Architecture:
    - Implements Agent B (Phantom Swarm Generator) from the three-agent design
    - Output is consumed by Agent C (spatial-hash validator) before broadcast
    - Agent A (Router) would supply seed parameters in an operational pipeline

Usage:
    python src/prototype/agent_b_parallel_swarm_generator.py
"""

import multiprocessing
import random
import time
from typing import Dict, List, Tuple

# ============================================================================
# BANNER
# ============================================================================

BANNER = """
================================================================================
  AGENT B PARALLEL SWARM GENERATOR
  Unclassified Synthetic Prototype - Portfolio PoC
  Not operational telemetry. Not deployment-ready deception tooling.
================================================================================
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_MULTIPLIER = 1000       # Number of phantom convoys to generate
WAYPOINTS_PER_CONVOY = 5        # Waypoints per synthetic convoy
NUM_WORKERS = max(2, multiprocessing.cpu_count() - 1)  # Worker processes
RANDOM_SEED = 42                # Deterministic seed for reproducibility


# ============================================================================
# CONVOY GENERATION (runs in worker processes)
# ============================================================================

def generate_phantom_batch(args: Tuple[int, int, int]) -> List[Dict]:
    """
    Generate a batch of synthetic phantom convoy records.

    This function is executed in a separate worker process. Each phantom record
    contains a synthetic convoy ID and a sequence of randomized (lat, lon)
    waypoints. The coordinates are not tied to any real operational area.

    Args:
        args: Tuple of (batch_id, batch_size, seed_offset) used to produce
              a deterministic but unique set of records per worker.

    Returns:
        List of phantom convoy dicts, each with 'convoy_id' and 'waypoints'.
    """
    batch_id, batch_size, seed_offset = args
    rng = random.Random(RANDOM_SEED + seed_offset)

    records = []
    for i in range(batch_size):
        # Generate a random anchor point (non-operational synthetic coordinates)
        anchor_lat = rng.uniform(-60.0, 60.0)
        anchor_lon = rng.uniform(-170.0, 170.0)

        waypoints = []
        for _ in range(WAYPOINTS_PER_CONVOY):
            lat = anchor_lat + rng.uniform(-1.0, 1.0)
            lon = anchor_lon + rng.uniform(-1.0, 1.0)
            waypoints.append({"lat": round(lat, 6), "lon": round(lon, 6)})

        records.append({
            "convoy_id": f"PHANTOM-B{batch_id:03d}-{i:06d}",
            "waypoints": waypoints,
            "label": "synthetic_phantom",
            "classification": "UNCLASSIFIED-SYNTHETIC-PROTOTYPE",
        })

    return records


def run_parallel_swarm(multiplier: int = DEFAULT_MULTIPLIER,
                       num_workers: int = NUM_WORKERS) -> Tuple[List[Dict], float]:
    """
    Run parallel phantom convoy generation across multiple worker processes.

    Divides the total requested phantom count into equal batches, distributes
    those batches to a multiprocessing pool, and collects results. Returns
    the full list of generated records along with wall-clock generation time.

    Args:
        multiplier: Total number of phantom convoys to generate.
        num_workers: Number of parallel worker processes to use.

    Returns:
        Tuple of (all_records, elapsed_ms) where elapsed_ms is wall-clock
        generation time in milliseconds.
    """
    batch_size = max(1, multiplier // num_workers)
    remainder = multiplier - batch_size * num_workers

    # Build batch argument list
    batch_args = []
    for worker_idx in range(num_workers):
        size = batch_size + (1 if worker_idx < remainder else 0)
        batch_args.append((worker_idx, size, worker_idx * 10000))

    start_time = time.perf_counter()
    with multiprocessing.Pool(processes=num_workers) as pool:
        batch_results = pool.map(generate_phantom_batch, batch_args)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # Flatten results
    all_records: List[Dict] = []
    for batch in batch_results:
        all_records.extend(batch)

    return all_records, elapsed_ms


# ============================================================================
# REPORTING
# ============================================================================

def print_metrics(records: List[Dict], elapsed_ms: float,
                  multiplier: int, num_workers: int) -> None:
    """
    Print generation throughput and latency metrics to console.

    Args:
        records: All generated phantom convoy records.
        elapsed_ms: Total wall-clock time in milliseconds.
        multiplier: Requested phantom count.
        num_workers: Number of worker processes used.
    """
    throughput = len(records) / (elapsed_ms / 1000.0) if elapsed_ms > 0 else 0.0

    print("\n" + "─" * 80)
    print("  GENERATION METRICS")
    print("─" * 80)
    print(f"  Requested multiplier:       {multiplier:,} phantoms")
    print(f"  Records generated:          {len(records):,}")
    print(f"  Worker processes:           {num_workers}")
    print(f"  Waypoints per convoy:       {WAYPOINTS_PER_CONVOY}")
    print(f"  Wall-clock latency:         {elapsed_ms:.2f} ms")
    print(f"  Throughput:                 {throughput:,.0f} convoys/second")
    print()
    print("  Sample record (first phantom):")
    if records:
        sample = records[0]
        print(f"    convoy_id: {sample['convoy_id']}")
        print(f"    label:     {sample['label']}")
        print(f"    waypoints: {sample['waypoints'][:2]} ...")
    print("─" * 80)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(BANNER)

    for multiplier in [100, 1000]:
        print(f"\n  [RUN] Generating {multiplier:,} phantom convoys with "
              f"{NUM_WORKERS} worker(s)...")
        records, elapsed_ms = run_parallel_swarm(
            multiplier=multiplier, num_workers=NUM_WORKERS
        )
        print_metrics(records, elapsed_ms, multiplier, NUM_WORKERS)

    print("\n  Prototype run complete. All data is unclassified synthetic output.\n")
