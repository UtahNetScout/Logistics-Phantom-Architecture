# SYNCON: Synthetic Convoy Operations Network

**Architecture:** Logistics Phantom  
**Scope:** unclassified synthetic prototype data only  
**Status:** runnable product demo, engineering blueprint, and reviewer evidence package

[![Tests](https://github.com/UtahNetScout/Logistics-Phantom-Architecture/actions/workflows/test.yml/badge.svg)](https://github.com/UtahNetScout/Logistics-Phantom-Architecture/actions/workflows/test.yml)
[![Benchmarks](https://github.com/UtahNetScout/Logistics-Phantom-Architecture/actions/workflows/benchmark.yml/badge.svg)](https://github.com/UtahNetScout/Logistics-Phantom-Architecture/actions/workflows/benchmark.yml)

SYNCON is a portfolio-grade AI systems architecture demo for contested-logistics planning. It shows how an agentic platform could generate large volumes of synthetic phantom convoy telemetry, validate those records against protected synthetic ground truth, evaluate them with a simplified red-team detector, and produce mission-lifecycle evidence reports.

This repository does not contain classified data, real convoy telemetry, real routes, operational sensor integration, or deployment-ready deception tooling. It is a synthetic product prototype and engineer-ready blueprint.

---

## Quick Evaluation Path

If you are reviewing this project cold, use this path:

1. Read the [SYNCON Executive Brief](docs/SYNCON_EXECUTIVE_BRIEF.md).
2. Open the [Engineer Handoff Package](docs/ENGINEER_HANDOFF_PACKAGE.md).
3. Open the [Reviewer Evaluation Guide](docs/REVIEWER_EVALUATION_GUIDE.md).
4. Inspect the committed [sample demo evidence package](examples/syncon-demo/README.md).
5. Run the local dashboard:

```bash
python syncon.py dashboard
```

Then open:

```text
http://127.0.0.1:8765
```

6. Run a fresh synthetic mission package:

```bash
python syncon.py run --scenario demo
```

Generated artifacts are written to `runs/{run_id}/`.

Available synthetic scenario templates include `demo`, `baseline`, `dense-phantom`, `validation-stress`, and `high-threat-synthetic`.

7. Export a reviewer-ready executive package:

```bash
python syncon.py export --run-id demo-run-001
```

Exported reports are written to `exports/{run_id}/`.

---

## Why This Exists

Modern logistics networks operate in environments where adversary AI systems may fuse open-source, commercial, cyber, RF, imagery, and movement signals. SYNCON explores one product question:

**Can a controlled synthetic telemetry layer increase adversary uncertainty while preserving strict validation boundaries around friendly ground truth?**

The current prototype demonstrates the product workflow, validation gate, evidence reporting, and red-team evaluation pattern. It does not claim operational effectiveness.

---

## What Makes The Demo Stand Out

- Generates up to 10,000 synthetic phantom convoy records in the default demo.
- Seeds intentionally unsafe phantom records so Agent C can prove it rejects them.
- Produces a complete evidence package: scenario, phantoms, validation, red-team metrics, timeline, and Markdown report.
- Provides a local high-tech dashboard for non-code review.
- Replays each generated mission as a deterministic setup-to-report sequence in the dashboard.
- Converts run evidence into deterministic operator decision cards for reviewer-safe next actions.
- Separates the product shell, engineering blueprint, validation boundaries, and future operational vision.
- Keeps all data synthetic and unclassified.

---

## Product Surface

| Surface | Purpose |
|---------|---------|
| `python syncon.py dashboard` | Local browser dashboard for mission setup, metrics, run registry comparison, operator decisions, mission replay, lifecycle timeline, and artifact links |
| `python syncon.py run --scenario demo` | CLI runner that generates a complete synthetic evidence package from a selected scenario template |
| `python syncon.py export --run-id demo-run-001` | Executive export command that creates a reviewer-ready leave-behind package |
| Dashboard `Export Brief` button | UI action that generates and opens the executive export package for the selected run |
| `docs/ENGINEER_HANDOFF_PACKAGE.md` | First-read engineering handoff packet with module responsibilities, service boundaries, acceptance criteria, and safety rules |
| `docs/ENGINEERING_BLUEPRINT.md` | Engineer-ready build plan with architecture, data contracts, APIs, and acceptance criteria |
| `docs/SYNCON_EXECUTIVE_BRIEF.md` | Concise product brief for technical and non-technical reviewers |
| `docs/REVIEWER_EVALUATION_GUIDE.md` | Step-by-step review path, acceptance checklist, and demo framing |
| `docs/SYNCON_DEMO_SCRIPT.md` | Short talk track for walking someone through the project |
| `examples/syncon-demo/` | Lightweight committed evidence package for quick inspection |

---

## Architecture Summary

SYNCON is built around the Logistics Phantom three-agent architecture:

| Agent | Role | Current Status |
|-------|------|----------------|
| Agent A | Router and ground-truth abstraction boundary | Architected, not implemented |
| Agent B | Phantom swarm generator | Prototype modules implemented |
| Agent C | Validation gate and protected-ground-truth guardrail | Implemented and tested |

The long-term product vision includes pre-mission planning, future authorized live-support mode, and post-mission reporting. The future live-support concept is named **Convoy Shield**. It is not implemented here and would require legal authorization, operational ownership, cybersecurity accreditation, classification handling, C2 integration review, and human-in-the-loop controls before any live use.

---

## Generated Evidence Artifacts

Each SYNCON run writes:

| Artifact | Description |
|----------|-------------|
| `scenario.json` | Scenario configuration, synthetic convoy count, seed, and scope notes |
| `phantoms.json` | Generated phantom convoy telemetry records |
| `validation.json` | Agent C approval/rejection metrics |
| `red_team.json` | Simplified red-team detector results |
| `timeline.json` | Pre-mission, during-mission, and post-mission event timeline |
| `REPORT.md` | Human-readable evidence report |
| `exports/{run_id}/SYNCON_EXECUTIVE_REPORT.md` | Reviewer-ready executive leave-behind generated from a completed run |
| `exports/{run_id}/EXPORT_MANIFEST.json` | Export manifest listing included artifacts and scope |

The committed sample package omits `phantoms.json` because full telemetry payloads can be large. Running SYNCON locally regenerates the full artifact set.

---

## Run Tests

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

Run the full suite:

```bash
pytest tests/ -v -s
```

Run by category:

```bash
pytest tests/unit/ -v -s
pytest tests/integration/ -v -s
pytest tests/adversary/ -v -s
pytest tests/performance/ -v -s
```

---

## Validation Boundaries

Validated within prototype scope:

- Deterministic synthetic scenario execution.
- Phantom convoy generation at demo scale.
- Agent C validation against protected synthetic ground truth.
- Rejection of intentionally seeded unsafe phantom records.
- Simplified red-team SNR and detection metrics.
- Local dashboard and generated evidence reports.
- Run registry and side-by-side mission comparison inside the dashboard.
- Deterministic comparison insights that explain key differences across generated runs.
- Operator decision layer with severity, confidence, recommended action, and rationale cards.
- Mission replay console that turns run artifacts into a setup-to-report playback view.
- Executive export packages generated from completed runs.
- Dashboard export controls for reviewer-ready leave-behinds.
- Scenario templates for baseline, dense phantom, validation stress, and high-threat synthetic review profiles.

Not validated:

- Real-world adversary deception.
- Operational convoy protection.
- Real sensor injection.
- Electromagnetic, cyber, EW, or C2 effects.
- Classified data handling.
- Deployment readiness.

---

## Repository Map

```text
.
|-- syncon.py                         # SYNCON CLI entry point
|-- src/syncon/                       # Product runner and local dashboard
|-- src/prototype/                    # Prototype modules for architecture validation
|-- tests/                            # Unit, integration, adversary, and performance tests
|-- docs/ENGINEER_HANDOFF_PACKAGE.md  # Engineer handoff packet
|-- docs/ENGINEERING_BLUEPRINT.md     # Engineer-ready implementation blueprint
|-- docs/SYNCON_EXECUTIVE_BRIEF.md    # Product overview
|-- docs/REVIEWER_EVALUATION_GUIDE.md # Reviewer walkthrough and acceptance checklist
|-- docs/SYNCON_DEMO_SCRIPT.md        # Short demo talk track
|-- examples/syncon-demo/             # Lightweight committed sample evidence package
|-- exports/                          # Generated executive export packages, ignored by git
```

---

## Document Control

**Version:** 4.0  
**Classification:** UNCLASSIFIED synthetic prototype artifact  
**Last updated:** 2026-06-24  
**Author:** Ronald Taylor / UtahNetScout
