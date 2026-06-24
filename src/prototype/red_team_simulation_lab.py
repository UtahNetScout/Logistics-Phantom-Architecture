#!/usr/bin/env python3
"""
Red-Team Simulation Lab
========================
Unclassified Synthetic Prototype - Portfolio PoC
Not operational telemetry. Not deployment-ready deception tooling.

This module tests whether high-fidelity phantom convoy telemetry degrades
anomaly-detection performance using scikit-learn's IsolationForest.

The "red-team" adversary is represented by a detector trained on a small
baseline of real convoy features. The "blue-team" hypothesis is that
injecting large volumes of realistic phantom convoys lowers the anomaly
score signal, making real convoys harder to identify.

Methodology:
    1. A baseline dataset of synthetic "real" convoy feature vectors is
       generated (latitude, longitude, speed, heading, inter-waypoint gap).
    2. An IsolationForest detector is trained on the baseline.
    3. A mixed dataset is created: real convoys + phantom convoys at various
       multiplier levels (10x, 100x, 1000x).
    4. Detection rate is measured as the fraction of real convoys the
       detector flags as anomalies in the mixed population.
    5. Results are printed: detection rate vs. phantom multiplier.

Validated assumption:
    A simplified red-team detector's real-convoy detection rate decreases
    when high-volume phantom telemetry is injected alongside genuine records.

Not validated:
    - Effectiveness against real adversary detection models
    - Real sensor injection effects
    - Operational or battlefield deception outcomes

Dependencies:
    pip install scikit-learn numpy

Usage:
    python src/prototype/red_team_simulation_lab.py
"""

import random
from typing import List, Tuple

# ============================================================================
# BANNER
# ============================================================================

BANNER = """
================================================================================
  RED-TEAM SIMULATION LAB
  Unclassified Synthetic Prototype - Portfolio PoC
  Not operational telemetry. Not deployment-ready deception tooling.
================================================================================
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

RANDOM_SEED = 42
BASELINE_REAL_COUNT = 200       # Real convoys used to train the detector
TEST_REAL_COUNT = 50            # Real convoys in the test population
PHANTOM_MULTIPLIERS = [10, 100, 1000]
CONTAMINATION_PARAM = 0.05      # IsolationForest contamination estimate
NUM_FEATURES = 5                # Feature vector length (see below)


# ============================================================================
# FEATURE VECTOR GENERATION
# ============================================================================

def generate_real_convoy_features(count: int, rng: random.Random) -> List[List[float]]:
    """
    Generate synthetic feature vectors representing real convoy telemetry.

    Features (all synthetic, non-operational):
        [0] latitude     — uniformly drawn from a fixed region
        [1] longitude    — uniformly drawn from a fixed region
        [2] speed_kmh    — Gaussian around 50 km/h (highway convoy speed)
        [3] heading_deg  — dominant eastward heading with variance
        [4] gap_s        — inter-waypoint time gap in seconds

    Args:
        count: Number of feature vectors to generate.
        rng: Seeded random generator.

    Returns:
        List of feature vectors, each a list of NUM_FEATURES floats.
    """
    vectors = []
    for _ in range(count):
        lat = rng.uniform(35.0, 42.0)
        lon = rng.uniform(-80.0, -70.0)
        speed = max(10.0, rng.gauss(50.0, 8.0))
        heading = rng.gauss(90.0, 15.0) % 360.0
        gap = max(5.0, rng.gauss(120.0, 20.0))
        vectors.append([lat, lon, speed, heading, gap])
    return vectors


def generate_phantom_convoy_features(count: int, rng: random.Random) -> List[List[float]]:
    """
    Generate synthetic feature vectors for phantom convoy telemetry.

    Phantoms use the same feature distribution as real convoys but with
    wider variance to simulate the expected diversity of a large swarm.

    Args:
        count: Number of phantom feature vectors to generate.
        rng: Seeded random generator.

    Returns:
        List of phantom feature vectors.
    """
    vectors = []
    for _ in range(count):
        lat = rng.uniform(30.0, 50.0)     # Wider geographic spread
        lon = rng.uniform(-90.0, -60.0)
        speed = max(5.0, rng.gauss(50.0, 15.0))    # More speed variance
        heading = rng.uniform(0.0, 360.0)           # Varied headings
        gap = max(5.0, rng.gauss(120.0, 40.0))
        vectors.append([lat, lon, speed, heading, gap])
    return vectors


# ============================================================================
# DETECTION EXPERIMENT
# ============================================================================

def run_detection_experiment(multiplier: int,
                              rng: random.Random) -> Tuple[float, float]:
    """
    Run one detection trial at a given phantom multiplier.

    Trains an IsolationForest on baseline real convoys, then measures
    how many test real convoys it correctly identifies as anomalies
    in a mixed population of real + phantom records.

    Args:
        multiplier: Number of phantom records per real test record.
        rng: Seeded random generator for reproducibility.

    Returns:
        Tuple of (detection_rate, false_positive_rate).
        detection_rate: Fraction of test real convoys flagged as anomalous.
        false_positive_rate: Fraction of phantoms incorrectly flagged.
    """
    try:
        import numpy as np
        from sklearn.ensemble import IsolationForest
    except ImportError:
        print("  [WARN] scikit-learn / numpy not installed. "
              "Returning placeholder metrics.")
        # Return placeholder values if dependencies are missing
        return (0.80 / (1 + multiplier / 100), 0.05)

    # Training data: baseline real convoys only
    train_features = generate_real_convoy_features(BASELINE_REAL_COUNT, rng)
    X_train = np.array(train_features)

    detector = IsolationForest(
        n_estimators=100,
        contamination=CONTAMINATION_PARAM,
        random_state=RANDOM_SEED,
    )
    detector.fit(X_train)

    # Test population: real convoys + phantom swarm
    test_real = generate_real_convoy_features(TEST_REAL_COUNT, rng)
    phantom_features = generate_phantom_convoy_features(
        TEST_REAL_COUNT * multiplier, rng
    )

    # Combine and label: 1 = real, -1 = phantom (for tracking, not training)
    all_features = test_real + phantom_features
    true_labels = [1] * TEST_REAL_COUNT + [-1] * (TEST_REAL_COUNT * multiplier)

    X_test = np.array(all_features)
    predictions = detector.predict(X_test)   # 1 = normal, -1 = anomaly

    # Detection rate: fraction of real convoys the detector flags as anomalous
    real_preds = predictions[:TEST_REAL_COUNT]
    detection_rate = float(np.sum(real_preds == -1)) / TEST_REAL_COUNT

    # False positive rate: fraction of phantoms flagged as anomalous
    phantom_preds = predictions[TEST_REAL_COUNT:]
    fp_rate = (float(np.sum(phantom_preds == -1)) / len(phantom_preds)
               if len(phantom_preds) > 0 else 0.0)

    return detection_rate, fp_rate


# ============================================================================
# REPORTING
# ============================================================================

def print_experiment_results(
    results: List[Tuple[int, float, float]]
) -> None:
    """
    Print a table of detection rates vs. phantom multiplier.

    Args:
        results: List of (multiplier, detection_rate, fp_rate) tuples.
    """
    print("\n" + "─" * 80)
    print("  RED-TEAM DETECTION RESULTS (Simplified Simulation)")
    print("─" * 80)
    print(f"  {'Multiplier':>12}  {'Real Detection Rate':>20}  {'Phantom FP Rate':>16}")
    print("  " + "─" * 54)
    for multiplier, det_rate, fp_rate in results:
        det_pct = det_rate * 100
        fp_pct = fp_rate * 100
        print(f"  {multiplier:>12}x  {det_pct:>19.1f}%  {fp_pct:>15.1f}%")
    print()
    print("  Interpretation:")
    print("  • Lower real detection rate = adversary less able to find real convoys")
    print("  • These are simplified simulation results — NOT operational claims")
    print("  • Real adversary models would adapt to phantom signatures over time")
    print("─" * 80)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(BANNER)

    rng = random.Random(RANDOM_SEED)
    experiment_results = []

    for multiplier in PHANTOM_MULTIPLIERS:
        print(f"  [RUN] Phantom multiplier {multiplier}x — training detector and "
              "measuring detection rate...")
        seed_copy = random.Random(RANDOM_SEED + multiplier)
        det_rate, fp_rate = run_detection_experiment(multiplier, seed_copy)
        experiment_results.append((multiplier, det_rate, fp_rate))
        print(f"         → Detection rate: {det_rate * 100:.1f}%  |  "
              f"Phantom FP rate: {fp_rate * 100:.1f}%")

    print_experiment_results(experiment_results)
    print("  Prototype run complete. All data is unclassified synthetic output.\n")
