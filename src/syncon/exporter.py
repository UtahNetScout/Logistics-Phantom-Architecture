#!/usr/bin/env python3
"""
SYNCON executive export package generator.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA
PORTFOLIO PROOF-OF-CONCEPT - NOT OPERATIONAL TELEMETRY
NOT DEPLOYMENT-READY DECEPTION TOOLING
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .runner import BANNER

EXPORT_REPORT_NAME = "SYNCON_EXECUTIVE_REPORT.md"
EXPORT_MANIFEST_NAME = "EXPORT_MANIFEST.json"
COPIED_ARTIFACTS = (
    "scenario.json",
    "validation.json",
    "red_team.json",
    "timeline.json",
    "REPORT.md",
)


def export_run(
    run_dir: Path,
    output_dir: Path,
    include_phantoms: bool = False,
) -> Dict[str, str]:
    """Export one completed SYNCON run into a reviewer-ready package."""
    artifacts = load_export_artifacts(run_dir)
    scenario = artifacts["scenario"]
    run_id = str(scenario.get("run_id", run_dir.name))
    export_dir = output_dir / run_id
    export_dir.mkdir(parents=True, exist_ok=True)

    copied = copy_export_artifacts(
        run_dir=run_dir,
        export_dir=export_dir,
        include_phantoms=include_phantoms,
    )
    report = render_executive_report(artifacts, copied)
    report_path = export_dir / EXPORT_REPORT_NAME
    report_path.write_text(report, encoding="utf-8")

    manifest = {
        "classification": BANNER,
        "product": "SYNCON - Synthetic Convoy Operations Network",
        "architecture": scenario.get("architecture_name", "Logistics Phantom"),
        "run_id": run_id,
        "source_run_dir": str(run_dir),
        "exported_at_utc": _utc_now(),
        "executive_report": EXPORT_REPORT_NAME,
        "included_artifacts": [path.name for path in copied],
        "phantom_payload_included": include_phantoms and (export_dir / "phantoms.json").exists(),
        "scope": "Synthetic prototype export package; not operational evidence.",
    }
    manifest_path = export_dir / EXPORT_MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    return {
        "export_dir": str(export_dir),
        "report_path": str(report_path),
        "manifest_path": str(manifest_path),
    }


def load_export_artifacts(run_dir: Path) -> Dict[str, Any]:
    """Load required artifacts for an executive export."""
    required = {
        "scenario": "scenario.json",
        "validation": "validation.json",
        "red_team": "red_team.json",
        "timeline": "timeline.json",
    }
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    artifacts: Dict[str, Any] = {}
    missing: list[str] = []
    for key, filename in required.items():
        path = run_dir / filename
        if not path.exists():
            missing.append(filename)
            continue
        artifacts[key] = json.loads(path.read_text(encoding="utf-8"))

    if missing:
        raise FileNotFoundError(
            f"Run directory {run_dir} is missing required artifact(s): {', '.join(missing)}"
        )

    report_path = run_dir / "REPORT.md"
    artifacts["report"] = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    return artifacts


def copy_export_artifacts(
    run_dir: Path,
    export_dir: Path,
    include_phantoms: bool,
) -> list[Path]:
    """Copy compact run artifacts into the export package."""
    names = list(COPIED_ARTIFACTS)
    if include_phantoms:
        names.append("phantoms.json")

    copied: list[Path] = []
    for name in names:
        source = run_dir / name
        if not source.exists():
            continue
        destination = export_dir / name
        shutil.copyfile(source, destination)
        copied.append(destination)
    return copied


def render_executive_report(artifacts: Dict[str, Any], copied_artifacts: list[Path]) -> str:
    """Render a polished executive report for a completed SYNCON run."""
    scenario = artifacts["scenario"]
    validation = artifacts["validation"]
    red_team = artifacts["red_team"]
    timeline = artifacts["timeline"]
    multiplier = scenario.get("phantom_multiplier", "-")
    run_id = scenario.get("run_id", "-")
    scenario_id = scenario.get("scenario_id", "-")
    events = timeline.get("events", [])

    lines = [
        "# SYNCON Executive Export Report",
        "",
        "**Product:** SYNCON - Synthetic Convoy Operations Network",
        "",
        f"**Architecture:** {scenario.get('architecture_name', 'Logistics Phantom')}",
        "",
        f"**Run ID:** `{run_id}`",
        "",
        f"**Scenario:** `{scenario_id}`",
        "",
        f"**Scenario Template:** {scenario.get('scenario_label', 'Demo')}",
        "",
        f"**Review Focus:** {scenario.get('review_focus', 'end-to-end product flow')}",
        "",
        f"**Generated:** {_utc_now()}",
        "",
        f"**Scope:** {BANNER}",
        "",
        "---",
        "",
        "## Executive Takeaway",
        "",
        (
            "SYNCON generated a controlled synthetic contested-logistics evidence package "
            "that can be reviewed without real convoy data, classified inputs, or deployment claims."
        ),
        "",
        (
            f"For this run, the system generated {int(scenario.get('phantom_count', 0)):,} "
            f"synthetic phantom records around {scenario.get('real_convoy_count', '-')} "
            "protected synthetic convoy and preserved a validation boundary through Agent C."
        ),
        "",
        "## At-A-Glance Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Phantom records | {_fmt_int(scenario.get('phantom_count'))} |",
        f"| Phantom multiplier | {_fmt_int(multiplier)}x |",
        f"| Seeded unsafe records | {_fmt_int(scenario.get('contaminated_phantoms'))} |",
        f"| Approved records | {_fmt_int(validation.get('approved_count'))} |",
        f"| Rejected records | {_fmt_int(validation.get('rejected_count'))} |",
        f"| Agent C approval rate | {_fmt_percent(validation.get('approval_rate'))} |",
        f"| Validation elapsed | {_fmt_float(validation.get('elapsed_ms'), 3)} ms |",
        f"| Red-team SNR | {_fmt_float(red_team.get('snr'), 4)} |",
        f"| Red-team detection rate | {_fmt_percent(red_team.get('detection_rate'))} |",
        "",
        "## Mission Lifecycle",
        "",
    ]

    if events:
        lines.extend(_timeline_rows(events))
    else:
        lines.append("- No lifecycle events were found in `timeline.json`.")

    lines.extend(
        [
            "",
            "## Validation Boundary",
            "",
            "- Agent C validated synthetic phantom records against protected synthetic ground truth.",
            "- Intentionally seeded unsafe records are included only to prove rejection behavior.",
            "- The output is suitable for product review and engineering handoff, not operational use.",
            "- Future live support remains a Convoy Shield roadmap concept requiring authority, accreditation, legal review, and human-in-the-loop control.",
            "",
            "## Included Export Files",
            "",
        ]
    )

    for path in copied_artifacts:
        lines.append(f"- `{path.name}`")
    lines.extend(
        [
            f"- `{EXPORT_MANIFEST_NAME}`",
            "",
            "## Reviewer Use",
            "",
            "Use this export as a concise leave-behind after a SYNCON walkthrough. The detailed `REPORT.md` remains available for evidence review, while this executive report summarizes product value, validation behavior, caveats, and included artifacts.",
            "",
            "## Claims Boundary",
            "",
            "This export does not claim real-world adversary deception, operational convoy protection, real sensor integration, classified data handling, EW/C2 effects, or deployment readiness.",
            "",
        ]
    )
    return "\n".join(lines)


def _timeline_rows(events: list[Dict[str, Any]]) -> list[str]:
    rows = ["| Stage | Event | Detail |", "|-------|-------|--------|"]
    for event in events:
        rows.append(
            "| "
            + " | ".join(
                [
                    _escape_table(str(event.get("stage", "-"))),
                    _escape_table(str(event.get("event", "-"))),
                    _escape_table(str(event.get("detail", "-"))),
                ]
            )
            + " |"
        )
    return rows


def _fmt_int(value: object) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    return "-"


def _fmt_float(value: object, decimals: int) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.{decimals}f}"
    return "-"


def _fmt_percent(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.2%}"
    return "-"


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
