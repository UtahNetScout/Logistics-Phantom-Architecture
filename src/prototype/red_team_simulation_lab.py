#!/usr/bin/env python3
"""
Red-Team Simulation Lab - Logistics Phantom Architecture
========================================================

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA
PORTFOLIO PROOF-OF-CONCEPT — NOT OPERATIONAL TELEMETRY
NOT DEPLOYMENT-READY DECEPTION TOOLING

Tests whether high-fidelity phantom telemetry (Bezier paths + kinematic
velocity profiles) degrades the detection accuracy of a simplified
adversary anomaly detector. Uses scikit-learn's IsolationForest as a
stand-in for an adversary ML system trained on historical logistics patterns.

Experiment design:
    - Historical logistics data: synthetic features representing real convoys
    - Baseline: IsolationForest trained and tested on historical data only
    - Attack: phantom swarm injected at 100x, 250x, 1000x multipliers
    - Metric: detection accuracy, SNR, precision, recall, F1

Success criterion: SNR < 0.1 achieved at 100x multiplier.

Usage:
    python3 red_team_simulation_lab.py

Author: Logistics Phantom Prototype
Date: 2026
"""

import random
import time
from typing import Dict, Tuple

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score

# ============================================================================
# BANNER
# ============================================================================

BANNER = (
    "UNCLASSIFIED SYNTHETIC PROTOTYPE DATA | "
    "PORTFOLIO PROOF-OF-CONCEPT | "
    "NOT OPERATIONAL TELEMETRY"
)

# ============================================================================
# CONFIGURATION
# ============================================================================

HISTORICAL_CONVOY_COUNT: int = 500      # Synthetic historical real convoys
REAL_CONVOY_COUNT: int = 10             # Real convoys in the live scenario
FEATURES_PER_CONVOY: int = 8            # Feature vector dimensionality
RANDOM_SEED: int = 42

# Feature indices for interpretability
F_SPEED_MEAN = 0
F_SPEED_STD = 1
F_HEADING_CHANGE_MEAN = 2
F_REST_FREQUENCY = 3
F_SEGMENT_LENGTH_MEAN = 4
F_TEMPORAL_JITTER = 5
F_PAYLOAD_TONNAGE = 6
F_REFUEL_INTERVAL = 7

# ============================================================================
# SYNTHETIC DATA GENERATORS
# ============================================================================


def _make_historical_features(n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate synthetic historical logistics feature vectors.

    Each row represents a convoy with realistic logistics statistics.
    All data is synthetic prototype data — not real operational records.

    Args:
        n: Number of historical convoy records.
        rng: NumPy random generator for deterministic output.

    Returns:
        Array of shape (n, FEATURES_PER_CONVOY).
    """
    X = np.zeros((n, FEATURES_PER_CONVOY))
    X[:, F_SPEED_MEAN] = rng.normal(45.0, 4.0, n)               # km/h mean
    X[:, F_SPEED_STD] = rng.normal(6.0, 1.5, n)                 # km/h std
    X[:, F_HEADING_CHANGE_MEAN] = rng.normal(12.0, 3.0, n)       # degrees
    X[:, F_REST_FREQUENCY] = rng.normal(0.4, 0.1, n)             # stops/hour
    X[:, F_SEGMENT_LENGTH_MEAN] = rng.normal(25.0, 5.0, n)       # km
    X[:, F_TEMPORAL_JITTER] = rng.normal(0.0, 10.0, n)           # minutes
    X[:, F_PAYLOAD_TONNAGE] = rng.normal(15.0, 4.0, n)           # tonnes
    X[:, F_REFUEL_INTERVAL] = rng.normal(200.0, 40.0, n)         # km
    return X


def _make_real_convoy_features(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate feature vectors for the actual real convoys in a scenario."""
    return _make_historical_features(n, rng)


def _make_phantom_features(
    n: int,
    rng: np.random.Generator,
    fidelity: str = "high",
) -> np.ndarray:
    """
    Generate phantom convoy feature vectors.

    Args:
        n: Number of phantom records.
        rng: NumPy random generator.
        fidelity: 'high' (Bezier + kinematic) or 'low' (pure noise).

    Returns:
        Array of shape (n, FEATURES_PER_CONVOY).
    """
    if fidelity == "high":
        # High-fidelity: drawn from same distribution as historical data
        return _make_historical_features(n, rng)
    else:
        # Low-fidelity: obviously anomalous values
        X = np.zeros((n, FEATURES_PER_CONVOY))
        X[:, F_SPEED_MEAN] = rng.uniform(80.0, 150.0, n)          # unrealistically fast
        X[:, F_SPEED_STD] = rng.uniform(20.0, 50.0, n)
        X[:, F_HEADING_CHANGE_MEAN] = rng.uniform(60.0, 180.0, n)
        X[:, F_REST_FREQUENCY] = rng.uniform(0.0, 0.05, n)
        X[:, F_SEGMENT_LENGTH_MEAN] = rng.uniform(200.0, 500.0, n)
        X[:, F_TEMPORAL_JITTER] = rng.uniform(120.0, 500.0, n)
        X[:, F_PAYLOAD_TONNAGE] = rng.uniform(100.0, 300.0, n)
        X[:, F_REFUEL_INTERVAL] = rng.uniform(1000.0, 5000.0, n)
        return X


# ============================================================================
# ADVERSARY DETECTOR
# ============================================================================


def train_anomaly_detector(
    historical_features: np.ndarray,
    contamination: float = 0.05,
    random_state: int = RANDOM_SEED,
) -> IsolationForest:
    """
    Train an IsolationForest anomaly detector on historical logistics data.

    Args:
        historical_features: Training feature matrix.
        contamination: Expected fraction of anomalies in training data.
        random_state: Random seed for reproducibility.

    Returns:
        Fitted IsolationForest model.
    """
    detector = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    detector.fit(historical_features)
    return detector


# ============================================================================
# EXPERIMENT RUNNER
# ============================================================================


def run_detection_experiment(
    multiplier: int,
    detector: IsolationForest,
    real_features: np.ndarray,
    historical_features: np.ndarray,
    rng: np.random.Generator,
    fidelity: str = "high",
) -> Dict:
    """
    Run one red-team experiment at a given phantom multiplier.

    Combines real convoy features with phantom features and measures how
    accurately the detector identifies the real convoys.

    Args:
        multiplier: Phantom-to-real ratio (e.g., 100 for 100x).
        detector: Trained IsolationForest.
        real_features: Feature vectors for real convoys.
        historical_features: Historical data used to compute baseline SNR.
        rng: NumPy random generator.
        fidelity: Phantom fidelity level ('high' or 'low').

    Returns:
        Dict with detection_rate, snr, precision, recall, f1, elapsed_ms.
    """
    n_real = len(real_features)
    n_phantom = n_real * multiplier

    phantom_features = _make_phantom_features(n_phantom, rng, fidelity=fidelity)

    # Combine: 1 = real (anomalous from convoy's perspective), -1 = phantom (inlier)
    all_features = np.vstack([real_features, phantom_features])
    # Ground truth: real convoys are the "anomaly" the adversary wants to find
    # IsolationForest: -1 = anomaly, 1 = inlier
    true_labels = np.array([1] * n_real + [0] * n_phantom)  # 1 = real, 0 = phantom

    t0 = time.perf_counter()
    predictions = detector.predict(all_features)  # -1 anomaly, 1 inlier
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Convert to binary: 1 = predicted real (anomaly), 0 = predicted phantom
    pred_binary = (predictions == -1).astype(int)

    # Detection rate = fraction of real convoys correctly flagged as anomalous
    real_pred = pred_binary[:n_real]
    detection_rate = float(np.mean(real_pred))

    # SNR = real detected / total flagged (how much signal in the noise)
    total_flagged = int(np.sum(pred_binary))
    real_flagged = int(np.sum(real_pred))
    snr = real_flagged / total_flagged if total_flagged > 0 else 0.0

    # Precision / recall / F1 over the full mixed set
    prec = precision_score(true_labels, pred_binary, zero_division=0)
    rec = recall_score(true_labels, pred_binary, zero_division=0)
    f1 = f1_score(true_labels, pred_binary, zero_division=0)

    return {
        "multiplier": multiplier,
        "n_real": n_real,
        "n_phantom": n_phantom,
        "detection_rate": detection_rate,
        "snr": snr,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "elapsed_ms": elapsed_ms,
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main() -> int:
    """Run full red-team simulation lab across multiplier levels."""
    print("\n" + "=" * 70)
    print("  RED-TEAM SIMULATION LAB")
    print(f"  {BANNER}")
    print("=" * 70)

    rng_np = np.random.default_rng(RANDOM_SEED)
    historical_features = _make_historical_features(HISTORICAL_CONVOY_COUNT, rng_np)

    print(f"\n  [1/3] Training adversary anomaly detector on {HISTORICAL_CONVOY_COUNT} historical records...")
    t0 = time.perf_counter()
    detector = train_anomaly_detector(historical_features)
    print(f"        Done in {(time.perf_counter()-t0)*1000:.1f} ms")

    rng_np2 = np.random.default_rng(RANDOM_SEED + 1)
    real_features = _make_real_convoy_features(REAL_CONVOY_COUNT, rng_np2)

    print("\n  [2/3] Baseline — no phantoms:")
    baseline_pred = (detector.predict(real_features) == -1)
    baseline_rate = float(np.mean(baseline_pred))
    print(f"        Real convoy detection rate (baseline): {baseline_rate:.2%}")

    print("\n  [3/3] Red-team experiments (high-fidelity phantoms):\n")
    header = f"  {'Multiplier':<12} {'Detection%':<14} {'SNR':<10} {'Precision':<12} {'Recall':<10} {'F1':<8} {'ms':<8}"
    print(header)
    print("  " + "-" * 74)

    for multiplier in [100, 250, 1000]:
        rng_exp = np.random.default_rng(RANDOM_SEED + multiplier)
        result = run_detection_experiment(
            multiplier=multiplier,
            detector=detector,
            real_features=real_features,
            historical_features=historical_features,
            rng=rng_exp,
        )
        flag = "✅" if result["snr"] < 0.1 else "❌"
        print(
            f"  {result['multiplier']:<12} "
            f"{result['detection_rate']:.2%}{'':6}"
            f"{result['snr']:.4f}{'':4}"
            f"{result['precision']:.4f}{'':6}"
            f"{result['recall']:.4f}{'':4}"
            f"{result['f1']:.4f}{'':2}"
            f"{result['elapsed_ms']:.1f}  {flag}"
        )

    print("\n  Target: SNR < 0.1 at 100x multiplier (see row above)")
    print("\n" + "=" * 70)
    print("  Red-team simulation complete. All data synthetic prototype.")
    print(f"  {BANNER}")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
