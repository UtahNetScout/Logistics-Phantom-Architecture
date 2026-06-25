"""
Integration checks for the reviewer-facing SYNCON package.

UNCLASSIFIED SYNTHETIC PROTOTYPE DATA - PORTFOLIO PROOF-OF-CONCEPT
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_reviewer_documents_are_linked_from_readme():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    expected_links = [
        "docs/ENGINEERING_BLUEPRINT.md",
        "docs/SYNCON_EXECUTIVE_BRIEF.md",
        "docs/REVIEWER_EVALUATION_GUIDE.md",
        "docs/SYNCON_DEMO_SCRIPT.md",
        "examples/syncon-demo/README.md",
    ]

    for link in expected_links:
        assert link in readme
        assert (ROOT / link).exists()


def test_reviewer_docs_keep_scope_boundaries_visible():
    docs = [
        ROOT / "README.md",
        ROOT / "docs" / "SYNCON_EXECUTIVE_BRIEF.md",
        ROOT / "docs" / "REVIEWER_EVALUATION_GUIDE.md",
        ROOT / "docs" / "SYNCON_DEMO_SCRIPT.md",
    ]

    for doc in docs:
        text = doc.read_text(encoding="utf-8").lower()
        assert "synthetic" in text
        assert "operational" in text


def test_readme_has_no_common_encoding_artifacts():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    mojibake_markers = ["â", "ð", "Ã", "Â"]
    for marker in mojibake_markers:
        assert marker not in readme
