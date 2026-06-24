#!/usr/bin/env python3
"""
Multimodal Telemetry Generator
================================
Unclassified Synthetic Prototype - Portfolio PoC
Not operational telemetry. Not deployment-ready deception tooling.

This module synthesizes multi-domain telemetry records that represent the
kind of cross-modal signatures a phantom convoy would need to produce to
be plausible across different sensor modalities.

A single-modal phantom (position only) is trivially filtered by any sensor
that correlates across domains. To raise the cost of adversary filtering,
phantoms must exhibit correlated physical, RF, and logistics metadata.

Modalities generated:
    Physical:  Lat/lon position, speed, heading, vehicle class estimate
    RF:        Synthetic frequency band, signal strength, duty cycle
    Logistics: Manifest weight class, cargo category, origin/destination codes

All values are statistically plausible ranges for training and simulation
purposes only. No real frequencies, call signs, or logistics networks are
referenced.

Connections to Architecture:
    - Extends Agent B output with cross-modal metadata fields
    - Increases adversary anomaly-detection cost (multi-domain correlation)
    - Feeds Agent C for cross-modal consistency validation (future work)

Usage:
    python src/prototype/multimodal_telemetry_generator.py
"""

import random
import uuid
from typing import Dict, List

# ============================================================================
# BANNER
# ============================================================================

BANNER = """
================================================================================
  MULTIMODAL TELEMETRY GENERATOR
  Unclassified Synthetic Prototype - Portfolio PoC
  Not operational telemetry. Not deployment-ready deception tooling.
================================================================================
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

RANDOM_SEED = 42

# Physical parameters (synthetic, non-operational)
SPEED_MEAN_KMH = 50.0
SPEED_STD_KMH = 12.0
HEADING_RANGE = (0.0, 360.0)

# RF parameters (synthetic, representative ranges only)
RF_FREQUENCY_BANDS_MHZ = [30.0, 88.0, 225.0, 400.0, 1350.0]   # Generic band centers
RF_POWER_DBM_RANGE = (-90.0, -50.0)
RF_DUTY_CYCLE_RANGE = (0.05, 0.95)

# Logistics parameters (generic categories, no real network data)
CARGO_CATEGORIES = ["SUPPLY", "EQUIPMENT", "FUEL", "MEDICAL", "PERSONNEL"]
WEIGHT_CLASSES = ["LIGHT", "MEDIUM", "HEAVY"]
REGION_CODES = ["REG-A", "REG-B", "REG-C", "REG-D", "REG-E"]


# ============================================================================
# MODALITY GENERATORS
# ============================================================================

def generate_physical_record(rng: random.Random) -> Dict:
    """
    Generate a synthetic physical telemetry record.

    Represents position, velocity, and vehicle class data that would be
    produced by GPS/INS sensors on a logistics vehicle.

    Args:
        rng: Seeded random generator.

    Returns:
        Dict with physical telemetry fields.
    """
    return {
        "lat": round(rng.uniform(-60.0, 60.0), 6),
        "lon": round(rng.uniform(-170.0, 170.0), 6),
        "speed_kmh": round(max(0.0, rng.gauss(SPEED_MEAN_KMH, SPEED_STD_KMH)), 2),
        "heading_deg": round(rng.uniform(*HEADING_RANGE), 1),
        "vehicle_class": rng.choice(["WHEELED", "TRACKED", "ROTARY", "FIXED"]),
        "modality": "PHYSICAL",
        "classification": "UNCLASSIFIED-SYNTHETIC",
    }


def generate_rf_record(physical_record: Dict, rng: random.Random) -> Dict:
    """
    Generate a synthetic RF telemetry record correlated with a physical record.

    The RF record shares positional context with the physical record to
    simulate cross-modal correlation. Frequency and power values are
    representative of generic communications bands and are NOT tied to
    any real spectrum allocations or signal intelligence.

    Args:
        physical_record: Associated physical telemetry (for position correlation).
        rng: Seeded random generator.

    Returns:
        Dict with RF metadata fields.
    """
    freq_center = rng.choice(RF_FREQUENCY_BANDS_MHZ)
    freq_offset = rng.uniform(-5.0, 5.0)
    return {
        "lat": physical_record["lat"] + rng.uniform(-0.001, 0.001),
        "lon": physical_record["lon"] + rng.uniform(-0.001, 0.001),
        "frequency_mhz": round(freq_center + freq_offset, 2),
        "signal_strength_dbm": round(rng.uniform(*RF_POWER_DBM_RANGE), 2),
        "duty_cycle": round(rng.uniform(*RF_DUTY_CYCLE_RANGE), 3),
        "burst_count": rng.randint(1, 20),
        "modality": "RF",
        "classification": "UNCLASSIFIED-SYNTHETIC",
    }


def generate_logistics_manifest(rng: random.Random) -> Dict:
    """
    Generate a synthetic logistics manifest record.

    Represents supply chain metadata such as cargo category, weight class,
    and notional origin/destination region codes. No real logistics networks,
    supply routes, or operational data are referenced.

    Args:
        rng: Seeded random generator.

    Returns:
        Dict with logistics manifest fields.
    """
    return {
        "manifest_id": f"MFT-{uuid.UUID(int=rng.getrandbits(128)).hex[:8].upper()}",
        "cargo_category": rng.choice(CARGO_CATEGORIES),
        "weight_class": rng.choice(WEIGHT_CLASSES),
        "unit_count": rng.randint(1, 50),
        "origin_region": rng.choice(REGION_CODES),
        "destination_region": rng.choice(REGION_CODES),
        "priority_level": rng.randint(1, 5),
        "modality": "LOGISTICS",
        "classification": "UNCLASSIFIED-SYNTHETIC",
    }


# ============================================================================
# MULTIMODAL RECORD ASSEMBLY
# ============================================================================

def generate_multimodal_record(convoy_id: str, rng: random.Random) -> Dict:
    """
    Assemble a complete multimodal telemetry record for one phantom convoy.

    Combines physical, RF, and logistics fields into a single record that
    a phantom convoy would emit across multiple sensor domains.

    Args:
        convoy_id: Unique identifier for this phantom convoy.
        rng: Seeded random generator.

    Returns:
        Dict with all three modality sub-records nested under their keys.
    """
    physical = generate_physical_record(rng)
    rf = generate_rf_record(physical, rng)
    logistics = generate_logistics_manifest(rng)

    return {
        "convoy_id": convoy_id,
        "record_type": "MULTIMODAL_PHANTOM",
        "classification": "UNCLASSIFIED-SYNTHETIC-PROTOTYPE",
        "physical": physical,
        "rf": rf,
        "logistics": logistics,
    }


def batch_generate_multimodal(count: int, seed: int = RANDOM_SEED) -> List[Dict]:
    """
    Generate a batch of multimodal phantom telemetry records.

    Args:
        count: Number of phantom records to generate.
        seed: Random seed for reproducibility.

    Returns:
        List of multimodal phantom records.
    """
    rng = random.Random(seed)
    return [
        generate_multimodal_record(f"PHANTOM-MM-{i:06d}", rng)
        for i in range(count)
    ]


# ============================================================================
# REPORTING
# ============================================================================

def print_batch_stats(records: List[Dict]) -> None:
    """
    Print summary statistics for a generated multimodal batch.

    Args:
        records: List of multimodal phantom records.
    """
    cargo_counts: Dict[str, int] = {}
    weight_counts: Dict[str, int] = {}
    vehicle_counts: Dict[str, int] = {}

    for rec in records:
        cat = rec["logistics"]["cargo_category"]
        cargo_counts[cat] = cargo_counts.get(cat, 0) + 1
        wt = rec["logistics"]["weight_class"]
        weight_counts[wt] = weight_counts.get(wt, 0) + 1
        vc = rec["physical"]["vehicle_class"]
        vehicle_counts[vc] = vehicle_counts.get(vc, 0) + 1

    print("\n" + "─" * 80)
    print("  MULTIMODAL TELEMETRY BATCH STATS")
    print("─" * 80)
    print(f"  Records generated:    {len(records):,}")
    print(f"  Modalities per record: 3 (physical, RF, logistics)")
    print()
    print("  Cargo categories:     " +
          "  ".join(f"{k}={v}" for k, v in sorted(cargo_counts.items())))
    print("  Weight classes:       " +
          "  ".join(f"{k}={v}" for k, v in sorted(weight_counts.items())))
    print("  Vehicle classes:      " +
          "  ".join(f"{k}={v}" for k, v in sorted(vehicle_counts.items())))

    if records:
        sample = records[0]
        print()
        print(f"  Sample record — convoy_id: {sample['convoy_id']}")
        phys = sample["physical"]
        rf = sample["rf"]
        logi = sample["logistics"]
        print(f"    Physical:  lat={phys['lat']}, lon={phys['lon']}, "
              f"speed={phys['speed_kmh']} km/h, heading={phys['heading_deg']}°")
        print(f"    RF:        freq={rf['frequency_mhz']} MHz, "
              f"power={rf['signal_strength_dbm']} dBm, "
              f"duty={rf['duty_cycle']}")
        print(f"    Logistics: {logi['cargo_category']} / "
              f"{logi['weight_class']} / manifest={logi['manifest_id']}")
    print("─" * 80)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(BANNER)

    print("  Generating 1,000 multimodal synthetic phantom telemetry records...")
    records = batch_generate_multimodal(count=1000, seed=RANDOM_SEED)
    print_batch_stats(records)

    print("\n  Prototype run complete. All data is unclassified synthetic output.\n")
