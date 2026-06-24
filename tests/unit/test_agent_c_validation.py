"""
tests/unit/test_agent_c_validation.py
======================================

Unit tests for Agent C Spatial Hash Validator.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA — PORTFOLIO PROOF-OF-CONCEPT

Validates:
    - Phantoms within 5 km of real waypoints are correctly rejected
    - Phantoms outside the contamination zone are approved (false positive rate = 0%)
    - Latency < 50 ms for 1,000 phantoms
    - Correct scaling to 10,000+ phantoms

Metrics: validation time, rejection count, throughput.
"""

import random
import time
from typing import List, Tuple

import pytest

from src.prototype.agent_c_spatial_hash_validator import (
    DEFAULT_EXCLUSION_KM,
    SpatialHashValidator,
)


# ============================================================================
# HELPERS
# ============================================================================

def _make_safe_phantom(rng: random.Random) -> List[Tuple[float, float]]:
    """Generate a phantom far from any real convoy (safe)."""
    base_lat = rng.uniform(-60.0, 60.0)
    base_lon = rng.uniform(-170.0, 170.0)
    return [(base_lat + rng.uniform(-1, 1), base_lon + rng.uniform(-1, 1))
            for _ in range(5)]


def _make_contaminated_phantom(
    real_waypoints: List[Tuple[float, float]],
    rng: random.Random,
    offset_deg: float = 0.001,
) -> List[Tuple[float, float]]:
    """Generate a phantom dangerously close to a real waypoint (< 1 km)."""
    wp = rng.choice(real_waypoints)
    return [(wp[0] + rng.uniform(0, offset_deg), wp[1] + rng.uniform(0, offset_deg))
            for _ in range(5)]


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def validator() -> SpatialHashValidator:
    return SpatialHashValidator(cell_size_km=5.0, exclusion_km=DEFAULT_EXCLUSION_KM)


@pytest.fixture
def real_convoy_fixture() -> List[Tuple[float, float]]:
    return [
        (40.7100, -74.0050),
        (40.7200, -74.0100),
        (40.7300, -74.0000),
        (40.7250, -73.9900),
        (40.7150, -73.9800),
    ]


# ============================================================================
# TESTS
# ============================================================================

class TestRejectionOfContaminatedPhantoms:
    """Phantoms within exclusion zone must always be rejected."""

    def test_rejects_phantom_within_exclusion_zone(
        self, validator: SpatialHashValidator, real_convoy_fixture
    ):
        """
        A phantom placed within 1 km of a real waypoint must be rejected.
        """
        validator.add_real_waypoints(real_convoy_fixture)
        rng = random.Random(42)
        contaminated = _make_contaminated_phantom(real_convoy_fixture, rng, offset_deg=0.001)
        result = validator.is_phantom_safe(contaminated)
        print(f"\n  Contaminated phantom safe={result}  (expected False)")
        assert result is False, "Contaminated phantom should be rejected"

    def test_rejects_all_intentionally_contaminated_phantoms(
        self, validator: SpatialHashValidator, real_convoy_fixture
    ):
        """All 5 intentionally contaminated phantoms in a batch must be rejected."""
        validator.add_real_waypoints(real_convoy_fixture)
        rng = random.Random(42)
        # Build a batch of 100 safe + 5 contaminated
        batch = [_make_safe_phantom(rng) for _ in range(100)]
        contaminated_indices = random.sample(range(100), 5)
        for idx in contaminated_indices:
            batch[idx] = _make_contaminated_phantom(real_convoy_fixture, rng)

        result = validator.validate_batch(batch)
        print(f"\n  Rejected: {result['rejected_count']} (expected 5)")
        assert result["rejected_count"] >= 5, (
            f"Expected at least 5 rejections, got {result['rejected_count']}"
        )


class TestApprovalOfLegitimatePhantoms:
    """Phantoms outside the exclusion zone must never be rejected (FP rate = 0%)."""

    def test_approves_phantom_outside_exclusion_zone(
        self, validator: SpatialHashValidator, real_convoy_fixture
    ):
        """A phantom on the opposite side of the globe must be approved."""
        validator.add_real_waypoints(real_convoy_fixture)
        distant_phantom = [(-35.0 + i * 0.01, 140.0 + i * 0.01) for i in range(5)]
        result = validator.is_phantom_safe(distant_phantom)
        print(f"\n  Distant phantom safe={result}  (expected True)")
        assert result is True

    def test_false_positive_rate_is_zero(
        self, validator: SpatialHashValidator, real_convoy_fixture
    ):
        """
        No legitimate (safe) phantom should ever be rejected.

        FP rate target: 0%.
        """
        validator.add_real_waypoints(real_convoy_fixture)
        rng = random.Random(99)
        # Generate 500 safe phantoms far from the convoy
        safe_batch = [_make_safe_phantom(rng) for _ in range(500)]
        result = validator.validate_batch(safe_batch)
        fp_rate = result["rejected_count"] / 500
        print(f"\n  False positive rate: {fp_rate:.4f}  (target: 0.0)")
        assert fp_rate == 0.0, (
            f"False positive rate {fp_rate:.4f} > 0% — legitimate phantoms rejected"
        )


class TestLatency:
    """Validation latency must meet sub-50ms target for 1,000 phantoms."""

    def test_latency_under_50ms_for_1000_phantoms(
        self, validator: SpatialHashValidator, real_convoy_fixture
    ):
        """
        Validating 1,000 phantoms must complete in under 50 ms.

        Target: <50ms.
        """
        validator.add_real_waypoints(real_convoy_fixture)
        rng = random.Random(42)
        batch = [_make_safe_phantom(rng) for _ in range(1000)]

        result = validator.validate_batch(batch)
        elapsed_ms = result["elapsed_ms"]
        throughput = result["throughput_per_sec"]
        print(f"\n  1,000 phantoms: {elapsed_ms:.2f} ms  ({throughput:,.0f} phs/s)")
        assert elapsed_ms < 50.0, (
            f"Latency {elapsed_ms:.1f}ms exceeds 50ms target"
        )

    def test_latency_under_100ms_for_10000_phantoms(
        self, validator: SpatialHashValidator, real_convoy_fixture
    ):
        """
        Validating 10,000 phantoms must complete in under 100 ms.

        Target: <100ms.
        """
        validator.add_real_waypoints(real_convoy_fixture)
        rng = random.Random(42)
        batch = [_make_safe_phantom(rng) for _ in range(10_000)]

        result = validator.validate_batch(batch)
        elapsed_ms = result["elapsed_ms"]
        throughput = result["throughput_per_sec"]
        print(f"\n  10,000 phantoms: {elapsed_ms:.2f} ms  ({throughput:,.0f} phs/s)")
        assert elapsed_ms < 100.0, (
            f"Latency {elapsed_ms:.1f}ms exceeds 100ms target"
        )


class TestScaling:
    """Validator must scale to large phantom counts without errors."""

    @pytest.mark.parametrize("n", [1_000, 5_000, 10_000])
    def test_scales_to_large_phantom_counts(
        self, validator: SpatialHashValidator, real_convoy_fixture, n: int
    ):
        """
        validate_batch must handle n phantoms without raising exceptions.
        """
        validator.add_real_waypoints(real_convoy_fixture)
        rng = random.Random(42)
        batch = [_make_safe_phantom(rng) for _ in range(n)]
        result = validator.validate_batch(batch)
        total = result["approved_count"] + result["rejected_count"]
        print(f"\n  {n:,} phantoms: {result['elapsed_ms']:.1f} ms  "
              f"({result['throughput_per_sec']:,.0f} phs/s)")
        assert total == n, f"Total processed {total} != {n}"

    def test_clear_and_reinitialise(self, validator: SpatialHashValidator):
        """Validator can be cleared and reused with a new real convoy."""
        convoy_a = [(40.0 + i * 0.01, -74.0) for i in range(5)]
        convoy_b = [(35.0 + i * 0.01, -80.0) for i in range(5)]
        validator.add_real_waypoints(convoy_a)
        validator.clear()
        validator.add_real_waypoints(convoy_b)
        # A phantom near convoy_a should now be safe
        near_a = [(40.0 + 0.002 * i, -74.0 + 0.002 * i) for i in range(5)]
        assert validator.is_phantom_safe(near_a) is True
