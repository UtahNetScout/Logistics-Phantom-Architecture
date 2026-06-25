"""
Integration tests for the SYNCON local dashboard rendering helpers.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA - PORTFOLIO PROOF-OF-CONCEPT
"""

import json

from src.syncon.dashboard import load_run_artifacts, load_run_registry, render_dashboard
from src.syncon.runner import run_demo


def test_dashboard_renders_metrics_and_artifact_links(tmp_path):
    run_demo(
        output_dir=tmp_path,
        run_id="dashboard-run",
        phantom_count=50,
        contaminated_phantoms=2,
        n_workers=1,
    )

    artifacts = load_run_artifacts(tmp_path / "dashboard-run")
    html = render_dashboard(
        output_dir=tmp_path,
        run_id="dashboard-run",
        artifacts=artifacts,
        message="Run complete",
    )

    assert "SYNCON" in html
    assert "Mission Command Brief" in html
    assert "Mission Setup" in html
    assert "Run Registry And Comparison" in html
    assert "Run Summary" in html
    assert "Validation And Red-Team Metrics" in html
    assert "Mission Timeline" in html
    assert "Synthetic Demo" in html
    assert "REPORT.md" in html
    assert "dashboard-run" in html
    assert "Run complete" in html


def test_dashboard_loads_generated_artifacts(tmp_path):
    run_demo(
        output_dir=tmp_path,
        run_id="load-run",
        phantom_count=20,
        contaminated_phantoms=1,
        n_workers=1,
    )

    artifacts = load_run_artifacts(tmp_path / "load-run")
    assert artifacts["exists"] is True
    assert artifacts["scenario"]["phantom_count"] == 20
    assert artifacts["validation"]["all_seeded_unsafe_rejected"] is True
    assert artifacts["timeline"]["events"]

    validation_file = tmp_path / "load-run" / "validation.json"
    validation = json.loads(validation_file.read_text(encoding="utf-8"))
    assert validation["rejected_count"] >= 1


def test_dashboard_registry_compares_multiple_runs(tmp_path):
    run_demo(
        output_dir=tmp_path,
        run_id="alpha-run",
        phantom_count=30,
        contaminated_phantoms=1,
        seed=42,
        n_workers=1,
    )
    run_demo(
        output_dir=tmp_path,
        run_id="bravo-run",
        phantom_count=60,
        contaminated_phantoms=3,
        seed=43,
        n_workers=1,
    )

    registry = load_run_registry(tmp_path)
    assert [summary["run_id"] for summary in registry] == ["bravo-run", "alpha-run"]
    assert registry[0]["phantom_count"] == 60
    assert registry[0]["rejected_count"] >= 3

    artifacts = load_run_artifacts(tmp_path / "bravo-run")
    html = render_dashboard(
        output_dir=tmp_path,
        run_id="bravo-run",
        artifacts=artifacts,
        run_summaries=registry,
    )

    assert "Run Registry And Comparison" in html
    assert "alpha-run" in html
    assert "bravo-run" in html
    assert "Evidence Ready" in html
    assert "/?run_id=alpha-run" in html
    assert "selected-run" in html
