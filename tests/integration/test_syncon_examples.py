"""
Integration tests for committed SYNCON example artifacts.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA - PORTFOLIO PROOF-OF-CONCEPT
"""

import json
from pathlib import Path


EXAMPLE_DIR = Path("examples/syncon-demo")


def test_syncon_example_package_is_lightweight():
    assert EXAMPLE_DIR.exists()
    assert not (EXAMPLE_DIR / "phantoms.json").exists()
    assert (EXAMPLE_DIR / "REPORT.md").exists()
    assert (EXAMPLE_DIR / "SUMMARY.md").exists()

    total_bytes = sum(path.stat().st_size for path in EXAMPLE_DIR.glob("*") if path.is_file())
    assert total_bytes < 25_000


def test_syncon_example_json_artifacts_are_parseable():
    scenario = json.loads((EXAMPLE_DIR / "scenario.json").read_text(encoding="utf-8"))
    validation = json.loads((EXAMPLE_DIR / "validation.json").read_text(encoding="utf-8"))
    red_team = json.loads((EXAMPLE_DIR / "red_team.json").read_text(encoding="utf-8"))
    timeline = json.loads((EXAMPLE_DIR / "timeline.json").read_text(encoding="utf-8"))

    assert scenario["product_name"] == "SYNCON"
    assert scenario["phantom_count"] == 250
    assert validation["all_seeded_unsafe_rejected"] is True
    assert red_team["multiplier"] == 250
    assert len(timeline["events"]) >= 4
