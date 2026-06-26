"""
Integration tests for SYNCON executive export packages.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA - PORTFOLIO PROOF-OF-CONCEPT
"""

import json

from src.syncon.exporter import EXPORT_MANIFEST_NAME, EXPORT_REPORT_NAME, export_run
from src.syncon.runner import main, run_demo


def test_export_run_writes_executive_package(tmp_path):
    runs_dir = tmp_path / "runs"
    exports_dir = tmp_path / "exports"
    run_demo(
        output_dir=runs_dir,
        run_id="export-run",
        phantom_count=75,
        contaminated_phantoms=2,
        n_workers=1,
    )

    result = export_run(
        run_dir=runs_dir / "export-run",
        output_dir=exports_dir,
    )

    export_dir = exports_dir / "export-run"
    assert result["export_dir"] == str(export_dir)
    assert (export_dir / EXPORT_REPORT_NAME).exists()
    assert (export_dir / EXPORT_MANIFEST_NAME).exists()
    assert (export_dir / "scenario.json").exists()
    assert (export_dir / "validation.json").exists()
    assert (export_dir / "red_team.json").exists()
    assert (export_dir / "timeline.json").exists()
    assert (export_dir / "REPORT.md").exists()
    assert not (export_dir / "phantoms.json").exists()

    report = (export_dir / EXPORT_REPORT_NAME).read_text(encoding="utf-8")
    assert "SYNCON Executive Export Report" in report
    assert "Executive Takeaway" in report
    assert "At-A-Glance Metrics" in report
    assert "Validation Boundary" in report
    assert "not operational use" in report
    assert "export-run" in report

    manifest = json.loads((export_dir / EXPORT_MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["run_id"] == "export-run"
    assert manifest["executive_report"] == EXPORT_REPORT_NAME
    assert manifest["phantom_payload_included"] is False


def test_export_run_can_include_phantom_payload(tmp_path):
    runs_dir = tmp_path / "runs"
    exports_dir = tmp_path / "exports"
    run_demo(
        output_dir=runs_dir,
        run_id="with-phantoms",
        phantom_count=20,
        contaminated_phantoms=1,
        n_workers=1,
    )

    export_run(
        run_dir=runs_dir / "with-phantoms",
        output_dir=exports_dir,
        include_phantoms=True,
    )

    export_dir = exports_dir / "with-phantoms"
    manifest = json.loads((export_dir / EXPORT_MANIFEST_NAME).read_text(encoding="utf-8"))
    assert (export_dir / "phantoms.json").exists()
    assert manifest["phantom_payload_included"] is True


def test_export_cli_generates_package(tmp_path):
    runs_dir = tmp_path / "runs"
    exports_dir = tmp_path / "exports"
    run_demo(
        output_dir=runs_dir,
        run_id="cli-export",
        phantom_count=25,
        contaminated_phantoms=1,
        n_workers=1,
    )

    exit_code = main(
        [
            "export",
            "--run-id",
            "cli-export",
            "--input-dir",
            str(runs_dir),
            "--output-dir",
            str(exports_dir),
        ]
    )

    assert exit_code == 0
    assert (exports_dir / "cli-export" / EXPORT_REPORT_NAME).exists()
    assert (exports_dir / "cli-export" / EXPORT_MANIFEST_NAME).exists()
