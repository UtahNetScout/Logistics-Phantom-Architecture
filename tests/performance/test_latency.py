"""
tests/performance/test_latency.py
===================================

Performance benchmarks for Agent B generation and Agent C validation.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA — PORTFOLIO PROOF-OF-CONCEPT

Benchmarks:
    - Agent B: 1,000 phantom generation time (target: < 5s serial)
    - Agent C: validation time for 10,000 phantoms (target: < 100ms)
    - Parallelisation speedup measurement (serial vs. available cores)
    - Throughput metrics printed to console
"""

import time
from typing import List, Tuple

import pytest

from src.prototype.agent_b_parallel_swarm_generator import (
    generate_phantom_swarm,
)
from src.prototype.agent_c_spatial_hash_validator import SpatialHashValidator


# ============================================================================
# HELPERS
# ============================================================================

def _safe_phantom(seed: int, idx: int) -> List[Tuple[float, float]]:
    """Generate one safe (non-contaminating) phantom waypoint list."""
    import random
    rng = random.Random(seed + idx * 997)
    base_lat = rng.uniform(-60.0, 60.0)
    base_lon = rng.uniform(-170.0, 170.0)
    return [(base_lat + rng.uniform(-1, 1), base_lon + rng.uniform(-1, 1))
            for _ in range(5)]


# ============================================================================
# TESTS
# ============================================================================

class TestAgentBLatency:
    """Agent B must generate 1,000 phantoms in under 5 seconds (serial)."""

    def test_agent_b_1000_phantoms_under_5s(self):
        """
        Generate 1,000 phantom convoys in serial mode.

        Target: < 5 seconds.
        Metric: total time, per-phantom latency.
        """
        t0 = time.perf_counter()
        phantoms = generate_phantom_swarm(1000, seed=42, n_workers=1)
        elapsed_s = time.perf_counter() - t0
        per_phantom_us = (elapsed_s / 1000) * 1_000_000

        print(f"\n  Agent B (1000 phantoms, serial):")
        print(f"    Total time    : {elapsed_s * 1000:.1f} ms")
        print(f"    Per phantom   : {per_phantom_us:.2f} µs")
        print(f"    Target        : <5000 ms  {'✅' if elapsed_s < 5.0 else '❌'}")

        assert len(phantoms) == 1000
        assert elapsed_s < 5.0, (
            f"Agent B took {elapsed_s:.2f}s for 1,000 phantoms (target: <5s)"
        )

    @pytest.mark.parametrize("n", [100, 500])
    def test_agent_b_smaller_batches(self, n: int):
        """Agent B sub-batches must complete well within time budget."""
        t0 = time.perf_counter()
        phantoms = generate_phantom_swarm(n, seed=42, n_workers=1)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        print(f"\n  Agent B ({n} phantoms): {elapsed_ms:.1f} ms")
        assert len(phantoms) == n
        assert elapsed_ms < 1000, f"{n} phantoms took {elapsed_ms:.1f}ms (target: <1000ms)"


class TestAgentCLatency:
    """Agent C must validate 10,000 phantoms in under 100ms."""

    def test_agent_c_1000_phantoms_under_50ms(self):
        """
        Validate 1,000 phantoms in under 50ms.

        Target: < 50ms.
        """
        real_convoy = [(40.71 + i * 0.01, -74.0) for i in range(5)]
        validator = SpatialHashValidator(exclusion_km=5.0)
        validator.add_real_waypoints(real_convoy)

        batch = [_safe_phantom(42, i) for i in range(1000)]

        t0 = time.perf_counter()
        result = validator.validate_batch(batch)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        print(f"\n  Agent C (1,000 phantoms):")
        print(f"    Total time    : {elapsed_ms:.2f} ms")
        print(f"    Throughput    : {result['throughput_per_sec']:,.0f} phs/s")
        print(f"    Target        : <50 ms  {'✅' if elapsed_ms < 50 else '❌'}")

        assert elapsed_ms < 50.0, (
            f"Agent C took {elapsed_ms:.1f}ms for 1,000 phantoms (target: <50ms)"
        )

    def test_agent_c_10000_phantoms_under_100ms(self):
        """
        Validate 10,000 phantoms in under 100ms.

        Target: < 100ms.
        """
        real_convoy = [(40.71 + i * 0.01, -74.0) for i in range(5)]
        validator = SpatialHashValidator(exclusion_km=5.0)
        validator.add_real_waypoints(real_convoy)

        batch = [_safe_phantom(42, i) for i in range(10_000)]

        t0 = time.perf_counter()
        result = validator.validate_batch(batch)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        print(f"\n  Agent C (10,000 phantoms):")
        print(f"    Total time    : {elapsed_ms:.2f} ms")
        print(f"    Throughput    : {result['throughput_per_sec']:,.0f} phs/s")
        print(f"    Target        : <100 ms  {'✅' if elapsed_ms < 100 else '❌'}")

        assert elapsed_ms < 100.0, (
            f"Agent C took {elapsed_ms:.1f}ms for 10,000 phantoms (target: <100ms)"
        )


class TestParallelisationSpeedup:
    """Measure speedup of parallel vs. serial phantom generation."""

    def test_parallel_matches_serial_output(self):
        """
        Parallel generation with n_workers>1 must produce identical output
        to serial n_workers=1 (deterministic with fixed seed).
        """
        serial = generate_phantom_swarm(100, seed=42, n_workers=1)
        parallel = generate_phantom_swarm(100, seed=42, n_workers=2)
        for s, p in zip(serial, parallel):
            assert s["waypoints"] == p["waypoints"], (
                f"Parallel/serial mismatch at phantom {s['phantom_id']}"
            )
        print("\n  Parallel output matches serial (seed=42) ✅")

    def test_parallel_speedup_measurement(self):
        """
        Measure and print parallel vs. serial speedup.

        This benchmark does not assert a specific speedup ratio because
        GitHub Actions runners vary. It validates that parallelism completes
        correctly and prints the speedup factor for human review.
        """
        import multiprocessing
        n_cores = max(1, multiprocessing.cpu_count())

        t_serial = time.perf_counter()
        generate_phantom_swarm(500, seed=42, n_workers=1)
        serial_s = time.perf_counter() - t_serial

        t_parallel = time.perf_counter()
        generate_phantom_swarm(500, seed=42, n_workers=n_cores)
        parallel_s = time.perf_counter() - t_parallel

        speedup = serial_s / parallel_s if parallel_s > 0 else 1.0
        print(f"\n  Parallelisation speedup ({n_cores} cores):")
        print(f"    Serial   : {serial_s * 1000:.1f} ms")
        print(f"    Parallel : {parallel_s * 1000:.1f} ms")
        print(f"    Speedup  : {speedup:.2f}x")
        # Parallel must at least not be massively slower than serial
        assert parallel_s < serial_s * 3.0, (
            f"Parallel unexpectedly slow: {parallel_s:.2f}s vs serial {serial_s:.2f}s"
        )
