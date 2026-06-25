#!/usr/bin/env python3
"""
SYNCON Phase 1 product runner.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA
PORTFOLIO PROOF-OF-CONCEPT - NOT OPERATIONAL TELEMETRY
NOT DEPLOYMENT-READY DECEPTION TOOLING
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

from src.prototype.agent_b_parallel_swarm_generator import generate_phantom_swarm
from src.prototype.agent_c_spatial_hash_validator import SpatialHashValidator
from src.prototype.red_team_simulation_lab import (
    HISTORICAL_CONVOY_COUNT,
    _make_historical_features,
    _make_real_convoy_features,
    run_detection_experiment,
    train_anomaly_detector,
)

BANNER = (
    "UNCLASSIFIED SYNTHETIC PROTOTYPE DATA | "
    "PORTFOLIO PROOF-OF-CONCEPT | "
    "NOT OPERATIONAL TELEMETRY | "
    "NOT DEPLOYMENT-READY DECEPTION TOOLING"
)

DEFAULT_SYNTHETIC_REAL_CONVOY: List[Tuple[float, float]] = [
    (40.7100, -74.0050),
    (40.7200, -74.0100),
    (40.7300, -74.0000),
    (40.7250, -73.9900),
    (40.7150, -73.9800),
]


@dataclass(frozen=True)
class ScenarioConfig:
    """Synthetic scenario configuration for one SYNCON demo run."""

    scenario_id: str
    run_id: str
    seed: int
    real_convoy_count: int
    phantom_count: int
    contaminated_phantoms: int
    exclusion_km: float
    classification: str = BANNER
    product_name: str = "SYNCON"
    product_expansion: str = "Synthetic Convoy Operations Network"
    architecture_name: str = "Logistics Phantom"
    future_live_mode: str = "Convoy Shield"
    mode: str = "synthetic-demo"

    @property
    def phantom_multiplier(self) -> int:
        return int(self.phantom_count / max(1, self.real_convoy_count))


def run_demo(
    output_dir: Path,
    scenario_id: str = "synthetic-contested-logistics-demo",
    run_id: str = "demo-run-001",
    seed: int = 42,
    phantom_count: int = 10_000,
    contaminated_phantoms: int = 5,
    n_workers: int | None = None,
) -> Dict[str, Any]:
    """Run the SYNCON synthetic product demo and write run artifacts."""
    started_at = _utc_now()
    scenario = ScenarioConfig(
        scenario_id=scenario_id,
        run_id=run_id,
        seed=seed,
        real_convoy_count=1,
        phantom_count=phantom_count,
        contaminated_phantoms=min(contaminated_phantoms, phantom_count),
        exclusion_km=5.0,
    )
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    timeline: List[Dict[str, Any]] = []
    _add_event(
        timeline,
        stage="pre-mission",
        event="Scenario configured",
        detail=(
            f"Configured {scenario.real_convoy_count} protected synthetic convoy "
            f"and {scenario.phantom_count:,} phantom convoy records."
        ),
    )

    t0 = time.perf_counter()
    phantoms = generate_phantom_swarm(
        num_phantoms=scenario.phantom_count,
        seed=scenario.seed,
        n_workers=n_workers,
    )
    generation_ms = (time.perf_counter() - t0) * 1000
    contaminated_ids = _seed_validation_challenges(
        phantoms=phantoms,
        real_convoy=DEFAULT_SYNTHETIC_REAL_CONVOY,
        count=scenario.contaminated_phantoms,
    )
    _add_event(
        timeline,
        stage="during-mission",
        event="Synthetic phantom telemetry generated",
        detail=(
            f"Generated {len(phantoms):,} phantom convoy records in "
            f"{generation_ms:.1f} ms."
        ),
    )

    validator = SpatialHashValidator(exclusion_km=scenario.exclusion_km)
    validator.add_real_waypoints(DEFAULT_SYNTHETIC_REAL_CONVOY)
    validation_result = validator.validate_batch([p["waypoints"] for p in phantoms])
    validation_summary = _build_validation_summary(
        validation_result=validation_result,
        contaminated_ids=contaminated_ids,
        phantom_count=len(phantoms),
    )
    _add_event(
        timeline,
        stage="during-mission",
        event="Agent C validation completed",
        detail=(
            f"Approved {validation_summary['approved_count']:,} and rejected "
            f"{validation_summary['rejected_count']:,} synthetic records."
        ),
    )

    red_team_result = _run_red_team(
        multiplier=scenario.phantom_multiplier,
        seed=scenario.seed,
    )
    _add_event(
        timeline,
        stage="during-mission",
        event="Red-team evaluation completed",
        detail=(
            "Simplified detector SNR "
            f"{red_team_result['snr']:.4f} at {scenario.phantom_multiplier:,}x."
        ),
    )

    completed_at = _utc_now()
    _add_event(
        timeline,
        stage="post-mission",
        event="Evidence report generated",
        detail="Run artifacts and report were written for review.",
    )

    scenario_artifact = {
        **asdict(scenario),
        "phantom_multiplier": scenario.phantom_multiplier,
        "started_at_utc": started_at,
        "completed_at_utc": completed_at,
        "synthetic_real_convoy_waypoints": _waypoints_as_lists(DEFAULT_SYNTHETIC_REAL_CONVOY),
        "notes": [
            "All coordinates and telemetry are synthetic prototype data.",
            "Contaminated phantoms are intentionally seeded to demonstrate Agent C rejection.",
            "This run does not represent operational effectiveness or deployment readiness.",
        ],
    }
    phantoms_artifact = {
        "classification": BANNER,
        "count": len(phantoms),
        "generation_ms": round(generation_ms, 3),
        "contaminated_demo_phantom_ids": contaminated_ids,
        "records": phantoms,
    }
    validation_artifact = {
        "classification": BANNER,
        **validation_summary,
        "raw_validator_metrics": _json_safe(validation_result),
    }
    red_team_artifact = {
        "classification": BANNER,
        "caveat": "Simplified prototype detector; not operational effectiveness.",
        **_json_safe(red_team_result),
    }
    timeline_artifact = {
        "classification": BANNER,
        "scenario_id": scenario.scenario_id,
        "run_id": scenario.run_id,
        "events": timeline,
    }

    artifacts = {
        "scenario": scenario_artifact,
        "phantoms": phantoms_artifact,
        "validation": validation_artifact,
        "red_team": red_team_artifact,
        "timeline": timeline_artifact,
    }

    _write_json(run_dir / "scenario.json", scenario_artifact)
    _write_json(run_dir / "phantoms.json", phantoms_artifact)
    _write_json(run_dir / "validation.json", validation_artifact)
    _write_json(run_dir / "red_team.json", red_team_artifact)
    _write_json(run_dir / "timeline.json", timeline_artifact)
    report = render_report(artifacts)
    (run_dir / "REPORT.md").write_text(report, encoding="utf-8")

    return {
        "run_dir": str(run_dir),
        "scenario": scenario_artifact,
        "validation": validation_artifact,
        "red_team": red_team_artifact,
        "timeline": timeline_artifact,
        "report": report,
    }


def render_report(artifacts: Dict[str, Any]) -> str:
    """Render a human-readable SYNCON evidence report."""
    scenario = artifacts["scenario"]
    validation = artifacts["validation"]
    red_team = artifacts["red_team"]
    timeline = artifacts["timeline"]
    multiplier = scenario["phantom_multiplier"]

    lines = [
        "# SYNCON Evidence Report",
        "",
        "**Product:** SYNCON - Synthetic Convoy Operations Network",
        "",
        f"**Architecture:** {scenario['architecture_name']}",
        "",
        f"**Run ID:** `{scenario['run_id']}`",
        "",
        f"**Scenario:** `{scenario['scenario_id']}`",
        "",
        f"**Classification / Scope:** {scenario['classification']}",
        "",
        "## Executive Summary",
        "",
        (
            f"SYNCON generated {scenario['phantom_count']:,} synthetic phantom "
            f"convoy records around {scenario['real_convoy_count']} protected "
            f"synthetic convoy in demo mode."
        ),
        "",
        (
            f"The Agent C validation gate approved {validation['approved_count']:,} "
            f"records and rejected {validation['rejected_count']:,} records, "
            "including intentionally seeded unsafe phantoms used to prove the "
            "validation boundary."
        ),
        "",
        (
            f"The simplified red-team detector reported SNR {red_team['snr']:.4f} "
            f"at {multiplier:,}x phantom density. This is a prototype metric, "
            "not an operational effectiveness claim."
        ),
        "",
        "## Mission Lifecycle",
        "",
    ]

    for event in timeline["events"]:
        lines.append(
            f"- **{event['stage']} / {event['event']}:** {event['detail']}"
        )

    lines.extend(
        [
            "",
            "## Run Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Protected synthetic convoys | {scenario['real_convoy_count']} |",
            f"| Phantom records generated | {scenario['phantom_count']:,} |",
            f"| Phantom multiplier | {multiplier:,}x |",
            f"| Intentionally seeded unsafe phantoms | {scenario['contaminated_phantoms']} |",
            f"| Approved records | {validation['approved_count']:,} |",
            f"| Rejected records | {validation['rejected_count']:,} |",
            f"| Validation elapsed | {validation['elapsed_ms']:.3f} ms |",
            f"| Red-team SNR | {red_team['snr']:.4f} |",
            f"| Red-team detection rate | {red_team['detection_rate']:.2%} |",
            "",
            "## Safety Boundary",
            "",
            "- All run data is synthetic prototype data.",
            "- No classified data, real convoy route, real sensor feed, or operational telemetry is used.",
            "- Future live support remains a Convoy Shield roadmap concept requiring authorization, accreditation, legal review, and human-in-the-loop control.",
            "- This report demonstrates product workflow readiness, not deployment readiness.",
            "",
            "## Artifacts",
            "",
            "- `scenario.json`",
            "- `phantoms.json`",
            "- `validation.json`",
            "- `red_team.json`",
            "- `timeline.json`",
            "- `REPORT.md`",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Build the SYNCON CLI parser."""
    parser = argparse.ArgumentParser(
        prog="syncon",
        description="SYNCON synthetic convoy operations demo runner.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a synthetic demo scenario.")
    run_parser.add_argument("--scenario", default="demo", choices=["demo"])
    run_parser.add_argument("--run-id", default="demo-run-001")
    run_parser.add_argument("--output-dir", default="runs")
    run_parser.add_argument("--phantoms", type=int, default=10_000)
    run_parser.add_argument("--contaminated", type=int, default=5)
    run_parser.add_argument("--seed", type=int, default=42)
    run_parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Worker count for phantom generation. Default 1 keeps demo runs stable on Windows.",
    )
    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="Start the local SYNCON dashboard.",
    )
    dashboard_parser.add_argument("--host", default="127.0.0.1")
    dashboard_parser.add_argument("--port", type=int, default=8765)
    dashboard_parser.add_argument("--output-dir", default="runs")
    dashboard_parser.add_argument("--run-id", default="demo-run-001")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the SYNCON CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        result = run_demo(
            output_dir=Path(args.output_dir),
            scenario_id=f"synthetic-contested-logistics-{args.scenario}",
            run_id=args.run_id,
            seed=args.seed,
            phantom_count=args.phantoms,
            contaminated_phantoms=args.contaminated,
            n_workers=args.workers,
        )
        print("SYNCON synthetic demo complete.")
        print(f"Run directory: {result['run_dir']}")
        print("Report: " + str(Path(result["run_dir"]) / "REPORT.md"))
        return 0
    if args.command == "dashboard":
        from src.syncon.dashboard import serve_dashboard

        serve_dashboard(
            host=args.host,
            port=args.port,
            output_dir=Path(args.output_dir),
            default_run_id=args.run_id,
        )
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 2


def _seed_validation_challenges(
    phantoms: List[Dict[str, Any]],
    real_convoy: List[Tuple[float, float]],
    count: int,
) -> List[int]:
    """Place selected phantoms inside the exclusion boundary for gate testing."""
    contaminated_ids: List[int] = []
    for idx in range(min(count, len(phantoms))):
        real_lat, real_lon = real_convoy[idx % len(real_convoy)]
        phantoms[idx]["waypoints"] = [
            (round(real_lat + 0.001, 6), round(real_lon + 0.001, 6))
            for _ in phantoms[idx]["waypoints"]
        ]
        phantoms[idx]["demo_contamination"] = "inside_agent_c_exclusion_boundary"
        contaminated_ids.append(int(phantoms[idx]["phantom_id"]))
    return contaminated_ids


def _build_validation_summary(
    validation_result: Dict[str, Any],
    contaminated_ids: List[int],
    phantom_count: int,
) -> Dict[str, Any]:
    rejected_indices = [int(i) for i in validation_result["rejected_indices"]]
    rejected_seeded = sorted(set(rejected_indices) & set(contaminated_ids))
    return {
        "phantom_count": phantom_count,
        "approved_count": int(validation_result["approved_count"]),
        "rejected_count": int(validation_result["rejected_count"]),
        "approval_rate": int(validation_result["approved_count"]) / phantom_count,
        "rejected_indices": rejected_indices,
        "seeded_unsafe_phantom_ids": contaminated_ids,
        "seeded_unsafe_rejected_ids": rejected_seeded,
        "all_seeded_unsafe_rejected": set(contaminated_ids).issubset(set(rejected_indices)),
        "elapsed_ms": float(validation_result["elapsed_ms"]),
        "throughput_per_sec": float(validation_result["throughput_per_sec"]),
    }


def _run_red_team(multiplier: int, seed: int) -> Dict[str, Any]:
    """Run the simplified red-team detector for this SYNCON scenario."""
    rng_train = np.random.default_rng(seed)
    historical = _make_historical_features(HISTORICAL_CONVOY_COUNT, rng_train)
    detector = train_anomaly_detector(historical)
    rng_real = np.random.default_rng(seed + 1)
    real_features = _make_real_convoy_features(1, rng_real)
    rng_exp = np.random.default_rng(seed + multiplier)
    return run_detection_experiment(
        multiplier=multiplier,
        detector=detector,
        real_features=real_features,
        historical_features=historical,
        rng=rng_exp,
    )


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(_json_safe(payload), indent=2) + "\n", encoding="utf-8")


def _json_safe(value: Any) -> Any:
    """Convert NumPy and tuple values into JSON-safe Python values."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
        return str(value)
    return value


def _waypoints_as_lists(waypoints: List[Tuple[float, float]]) -> List[List[float]]:
    return [[lat, lon] for lat, lon in waypoints]


def _add_event(
    timeline: List[Dict[str, Any]],
    stage: str,
    event: str,
    detail: str,
) -> None:
    timeline.append(
        {
            "timestamp_utc": _utc_now(),
            "stage": stage,
            "event": event,
            "detail": detail,
        }
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
