#!/usr/bin/env python3
"""
UNCLASSIFIED SYNTHETIC PROTOTYPE - Portfolio Proof-of-Concept

unclassified synthetic prototype data
portfolio proof-of-concept
not operational telemetry
not deployment-ready deception tooling
prototype for research/portfolio purposes

Multimodal Synthetic Telemetry Generator
========================================
Creates synthetic, internally-consistent physical, RF, and logistics metadata
for research validation workflows.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, List


DEFAULT_SEED = 20260624


@dataclass(frozen=True)
class TelemetryMetrics:
    """Quality metrics for multimodal synthetic telemetry output."""

    data_completeness: float
    consistency_score: float
    generation_latency_ms: float


def _rf_signature(rng: random.Random, speed_kmh: float) -> Dict:
    """Generate synthetic RF metadata consistent with movement state."""
    base_strength = max(-95.0, -52.0 - speed_kmh * 0.2 + rng.uniform(-2.5, 2.5))
    return {
        "radio_frequency_mhz": round(rng.uniform(220.0, 512.0), 3),
        "encryption_type": rng.choice(["AES256", "ChaCha20", "prototype-null"]),
        "signal_strength_dbm": round(base_strength, 3),
    }


def generate_multimodal_telemetry(record_count: int = 300, seed: int = DEFAULT_SEED) -> tuple[List[Dict], TelemetryMetrics]:
    """
    Generate representative synthetic telemetry records with cross-modal ties.

    Physical dynamics, RF metadata, and logistics manifests are linked through
    fuel usage and signal-strength plausibility checks.
    """
    start = time.perf_counter()
    rng = random.Random(seed)

    records: List[Dict] = []
    consistency_hits = 0

    for idx in range(record_count):
        speed = rng.uniform(12.0, 72.0)
        acceleration = rng.uniform(-1.6, 1.8)
        cargo_tons = rng.uniform(3.0, 22.0)
        fuel_lph = 8.0 + 0.17 * speed + 0.42 * cargo_tons + max(0.0, acceleration) * 2.0

        physical = {
            "x_km": round(rng.uniform(0.0, 600.0), 3),
            "y_km": round(rng.uniform(0.0, 600.0), 3),
            "speed_kmh": round(speed, 3),
            "acceleration_mps2": round(acceleration, 4),
        }
        rf = _rf_signature(rng, speed)
        logistics = {
            "cargo_tonnage": round(cargo_tons, 3),
            "fuel_consumption_lph": round(fuel_lph, 3),
            "maintenance_code": rng.choice(["green", "amber", "scheduled"]),
        }

        consistent = (
            logistics["fuel_consumption_lph"] > 0
            and -100.0 <= rf["signal_strength_dbm"] <= -45.0
            and physical["speed_kmh"] >= 0
        )
        consistency_hits += int(consistent)

        records.append(
            {
                "record_id": f"telemetry-{idx:05d}",
                "physical": physical,
                "rf": rf,
                "logistics": logistics,
            }
        )

    filled_fields = 0
    total_fields = 0
    for rec in records:
        for section in ("physical", "rf", "logistics"):
            for value in rec[section].values():
                total_fields += 1
                filled_fields += int(value is not None)

    metrics = TelemetryMetrics(
        data_completeness=round(filled_fields / max(total_fields, 1), 4),
        consistency_score=round(consistency_hits / max(record_count, 1), 4),
        generation_latency_ms=round((time.perf_counter() - start) * 1000.0, 3),
    )
    return records, metrics


def main() -> None:
    """Run a deterministic telemetry generation example."""
    records, metrics = generate_multimodal_telemetry(record_count=250)

    print("UNCLASSIFIED SYNTHETIC PROTOTYPE - Portfolio Proof-of-Concept")
    print("Not operational telemetry | Not deployment-ready | Prototype for research/portfolio purposes")
    print(f"Generated records: {len(records)}")
    print(f"Data completeness: {metrics.data_completeness}")
    print(f"Consistency score: {metrics.consistency_score}")
    print(f"Latency (ms): {metrics.generation_latency_ms}")


if __name__ == "__main__":
    main()
