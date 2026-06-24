"""
conftest.py - Shared pytest fixtures for Logistics Phantom test suite.

All data generated here is:
    UNCLASSIFIED SYNTHETIC PROTOTYPE DATA
    PORTFOLIO PROOF-OF-CONCEPT - NOT OPERATIONAL TELEMETRY

Fixtures provide deterministic seeds, sample route data, mock ground-truth
convoys, and historical logistics pattern arrays so that each test module
starts from a clean, reproducible state.
"""

import random
from typing import Dict, List, Tuple

import numpy as np
import pytest


# ============================================================================
# DETERMINISTIC SEEDS
# ============================================================================

FIXED_SEED: int = 42
"""Master seed used across all tests for full reproducibility."""


# ============================================================================
# GEOGRAPHIC CONSTANTS  (synthetic bounds - not operational coordinates)
# ============================================================================

GEO_LAT_MIN: float = 30.0
GEO_LAT_MAX: float = 50.0
GEO_LON_MIN: float = -100.0
GEO_LON_MAX: float = -70.0


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def fixed_seed() -> int:
    """Return the session-wide deterministic seed."""
    return FIXED_SEED


@pytest.fixture(scope="session")
def rng() -> random.Random:
    """Return a seeded stdlib Random instance (session-scoped)."""
    return random.Random(FIXED_SEED)


@pytest.fixture(scope="session")
def np_rng() -> np.random.Generator:
    """Return a seeded NumPy Generator (session-scoped)."""
    return np.random.default_rng(FIXED_SEED)


@pytest.fixture
def sample_waypoints() -> List[Tuple[float, float]]:
    """
    Return a short list of synthetic (lat, lon) waypoints.

    These represent a made-up route within the continental US bounding box.
    NOT real operational coordinates.
    """
    return [
        (36.5000, -90.0000),
        (37.2000, -88.5000),
        (38.1000, -87.3000),
        (39.0000, -86.0000),
        (39.8000, -84.5000),
    ]


@pytest.fixture
def sample_waypoints_long() -> List[Tuple[float, float]]:
    """Return a longer synthetic route (10 waypoints)."""
    rng = random.Random(FIXED_SEED + 1)
    base_lat, base_lon = 35.0, -95.0
    wps = []
    for _ in range(10):
        base_lat += rng.uniform(0.3, 0.7)
        base_lon += rng.uniform(0.3, 0.7)
        wps.append((round(base_lat, 4), round(base_lon, 4)))
    return wps


@pytest.fixture
def mock_real_convoy() -> List[Tuple[float, float]]:
    """
    Return a synthetic 'real' convoy as a list of 5 (lat, lon) waypoints.

    Represents the friendly ground-truth convoy that Agent C must protect.
    All coordinates are synthetic prototype data.
    """
    return [
        (40.7100, -74.0050),
        (40.7200, -74.0100),
        (40.7300, -74.0000),
        (40.7250, -73.9900),
        (40.7150, -73.9800),
    ]


@pytest.fixture
def mock_real_convoys_multiple() -> List[List[Tuple[float, float]]]:
    """Return a list of 3 synthetic real convoys for integration tests."""
    rng = random.Random(FIXED_SEED + 2)
    convoys = []
    for _ in range(3):
        base_lat = rng.uniform(35.0, 48.0)
        base_lon = rng.uniform(-98.0, -72.0)
        wps = []
        for _ in range(5):
            base_lat += rng.uniform(0.01, 0.05)
            base_lon += rng.uniform(0.01, 0.05)
            wps.append((round(base_lat, 6), round(base_lon, 6)))
        convoys.append(wps)
    return convoys


@pytest.fixture
def historical_logistics_features() -> np.ndarray:
    """
    Return a (500, 8) array of synthetic historical logistics features.

    Feature columns (all synthetic):
        0: speed_mean_kmh
        1: speed_std_kmh
        2: heading_change_mean_deg
        3: rest_frequency_per_hour
        4: segment_length_mean_km
        5: temporal_jitter_min
        6: payload_tonnes
        7: refuel_interval_km
    """
    rng = np.random.default_rng(FIXED_SEED)
    n = 500
    X = np.zeros((n, 8))
    X[:, 0] = rng.normal(45.0, 4.0, n)
    X[:, 1] = rng.normal(6.0, 1.5, n)
    X[:, 2] = rng.normal(12.0, 3.0, n)
    X[:, 3] = rng.normal(0.4, 0.1, n)
    X[:, 4] = rng.normal(25.0, 5.0, n)
    X[:, 5] = rng.normal(0.0, 10.0, n)
    X[:, 6] = rng.normal(15.0, 4.0, n)
    X[:, 7] = rng.normal(200.0, 40.0, n)
    return X


@pytest.fixture
def agent_b_seed_params() -> Dict:
    """
    Return a minimal Agent A seed parameter dict for Agent B.

    In the full architecture, Agent A abstracts real convoy data into these
    parameters - no coordinates. All values here are synthetic.
    """
    return {
        "region_lat_range": (GEO_LAT_MIN, GEO_LAT_MAX),
        "region_lon_range": (GEO_LON_MIN, GEO_LON_MAX),
        "multiplier": 100,
        "seed": FIXED_SEED,
        "speed_min_kmh": 35.0,
        "speed_max_kmh": 55.0,
        "waypoints_per_phantom": 8,
    }
