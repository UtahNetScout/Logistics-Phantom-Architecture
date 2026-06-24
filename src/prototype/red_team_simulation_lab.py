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

Red-Team Simulation Lab
=======================
Uses IsolationForest to test whether synthetic phantom telemetry reduces anomaly
detector separability under controlled prototype assumptions.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import List, Tuple

from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


DEFAULT_SEED = 20260624


@dataclass(frozen=True)
class RedTeamMetrics:
    """Evaluation metrics for prototype anomaly-detection stress testing."""

    detection_rate: float
    false_positive_rate: float
    snr_degradation: float
    detection_accuracy: float
    f1_score: float
    precision: float
    recall: float
    latency_ms: float


def _sample_logistics_pattern(rng: random.Random, phantom: bool = False, high_fidelity: bool = False) -> List[float]:
    """Generate a single synthetic feature vector for detector training/testing."""
    if not phantom:
        return [
            rng.uniform(32, 58),
            rng.uniform(0.08, 0.35),
            rng.uniform(-78, -58),
            rng.uniform(14, 24),
            rng.uniform(0.12, 0.42),
        ]

    if high_fidelity:
        return [
            rng.uniform(35, 60),
            rng.uniform(0.10, 0.46),
            rng.uniform(-84, -57),
            rng.uniform(15, 25),
            rng.uniform(0.16, 0.48),
        ]

    return [
        rng.uniform(6, 85),
        rng.uniform(0.02, 1.6),
        rng.uniform(-97, -41),
        rng.uniform(5, 40),
        rng.uniform(0.02, 0.88),
    ]


def run_red_team_lab(seed: int = DEFAULT_SEED) -> RedTeamMetrics:
    """Train IsolationForest and evaluate synthetic phantom detectability."""
    start = time.perf_counter()
    rng = random.Random(seed)

    train_data = [_sample_logistics_pattern(rng, phantom=False) for _ in range(1200)]

    detector = IsolationForest(contamination=0.12, random_state=seed, n_estimators=160)
    detector.fit(train_data)

    legit_test = [_sample_logistics_pattern(rng, phantom=False) for _ in range(500)]
    phantom_test = [_sample_logistics_pattern(rng, phantom=True, high_fidelity=True) for _ in range(500)]

    test_data = legit_test + phantom_test
    true_labels = [0] * len(legit_test) + [1] * len(phantom_test)

    predictions = detector.predict(test_data)
    predicted_labels = [1 if p == -1 else 0 for p in predictions]

    precision = precision_score(true_labels, predicted_labels, zero_division=0)
    recall = recall_score(true_labels, predicted_labels, zero_division=0)
    accuracy = accuracy_score(true_labels, predicted_labels)
    f1 = f1_score(true_labels, predicted_labels, zero_division=0)

    false_positives = sum(1 for t, p in zip(true_labels, predicted_labels) if t == 0 and p == 1)
    true_positives = sum(1 for t, p in zip(true_labels, predicted_labels) if t == 1 and p == 1)

    scores = detector.decision_function(test_data)
    legit_scores = scores[: len(legit_test)]
    phantom_scores = scores[len(legit_test) :]
    legit_mean = sum(legit_scores) / len(legit_scores)
    phantom_mean = sum(phantom_scores) / len(phantom_scores)
    snr_degradation = max(0.0, 1.0 - abs(legit_mean - phantom_mean) / max(abs(legit_mean), 1e-6))

    return RedTeamMetrics(
        detection_rate=round(true_positives / len(phantom_test), 4),
        false_positive_rate=round(false_positives / len(legit_test), 4),
        snr_degradation=round(snr_degradation, 4),
        detection_accuracy=round(accuracy, 4),
        f1_score=round(f1, 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        latency_ms=round((time.perf_counter() - start) * 1000.0, 3),
    )


def main() -> None:
    """Run the red-team simulation lab demonstration."""
    metrics = run_red_team_lab()

    print("UNCLASSIFIED SYNTHETIC PROTOTYPE - Portfolio Proof-of-Concept")
    print("Not operational telemetry | Not deployment-ready | Prototype for research/portfolio purposes")
    print(f"Detection rate: {metrics.detection_rate}")
    print(f"False positive rate: {metrics.false_positive_rate}")
    print(f"SNR degradation estimate: {metrics.snr_degradation}")
    print(f"Accuracy: {metrics.detection_accuracy}")
    print(f"F1: {metrics.f1_score}")
    print(f"Precision/Recall: {metrics.precision} / {metrics.recall}")
    print(f"Latency (ms): {metrics.latency_ms}")


if __name__ == "__main__":
    main()
