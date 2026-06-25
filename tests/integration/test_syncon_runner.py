"""
Integration tests for the SYNCON Phase 1 product runner.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA - PORTFOLIO PROOF-OF-CONCEPT
"""

import json

from src.syncon.runner import run_demo


def test_syncon_demo_writes_expected_artifacts(tmp_path):
    result = run_demo(
        output_dir=tmp_path,
        run_id="test-run",
        phantom_count=100,
        contaminated_phantoms=3,
        n_workers=1,
    )

    run_dir = tmp_path / "test-run"
    assert result["run_dir"] == str(run_dir)
    for name in [
        "scenario.json",
        "phantoms.json",
        "validation.json",
        "red_team.json",
        "timeline.json",
        "REPORT.md",
    ]:
        assert (run_dir / name).exists(), f"Missing artifact: {name}"

    validation = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
    assert validation["phantom_count"] == 100
    assert validation["all_seeded_unsafe_rejected"] is True
    assert len(validation["seeded_unsafe_rejected_ids"]) == 3


def test_syncon_report_contains_lifecycle_and_boundaries(tmp_path):
    run_demo(
        output_dir=tmp_path,
        run_id="report-run",
        phantom_count=50,
        contaminated_phantoms=2,
        n_workers=1,
    )

    report = (tmp_path / "report-run" / "REPORT.md").read_text(encoding="utf-8")
    assert "SYNCON - Synthetic Convoy Operations Network" in report
    assert "Mission Lifecycle" in report
    assert "pre-mission" in report
    assert "during-mission" in report
    assert "post-mission" in report
    assert "not deployment readiness" in report
