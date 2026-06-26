# SYNCON Reviewer Evaluation Guide

**Purpose:** give a technical reviewer, engineering lead, or defense-tech contact a fast way to evaluate SYNCON without reverse-engineering the repo.

**Scope:** unclassified synthetic prototype data only. This guide evaluates product architecture, engineering readiness, and demo clarity. It does not evaluate operational effectiveness.

---

## 10-Minute Review Path

### Minute 0-2: Understand The Product

Read the first page of the [SYNCON Executive Brief](SYNCON_EXECUTIVE_BRIEF.md).

Reviewer takeaway:

> SYNCON is a synthetic contested-logistics demo that generates phantom convoy telemetry, validates it against protected synthetic ground truth, runs simplified red-team evaluation, and produces evidence reports.

### Minute 2-4: Inspect The Sample Evidence Package

Open the [sample demo package](../examples/syncon-demo/README.md).

Look for:

- `SUMMARY.md` for a short run summary.
- `REPORT.md` for the human-readable evidence report.
- `scenario.json` for the synthetic mission configuration.
- `validation.json` for Agent C approval and rejection metrics.
- `red_team.json` for simplified red-team output.
- `timeline.json` for mission lifecycle events.

### Minute 4-7: Run The Dashboard

Start the local dashboard:

```bash
python syncon.py dashboard
```

Open:

```text
http://127.0.0.1:8765
```

Evaluate whether the dashboard makes the product understandable without reading code:

- Mission setup is visible.
- Synthetic/demo scope is obvious.
- Run summary is visible.
- Agent C validation metrics are visible.
- Red-team metrics are visible.
- Run registry comparison is visible after multiple missions have been generated.
- Comparison insights explain highest synthetic volume, validation exercise, SNR, detection-rate watch items, and scenario coverage.
- Operator decision cards recommend reviewer-safe next actions with severity, confidence, and rationale.
- Mission replay shows the selected run as a setup-to-report playback sequence.
- Pre-mission, during-mission, and post-mission lifecycle events are visible.
- Artifact links are available.
- `Export Brief` generates the executive leave-behind package for the selected run.

### Minute 7-10: Run A Fresh Evidence Package

Run:

```bash
python syncon.py run --scenario demo
```

Try additional synthetic profiles:

```bash
python syncon.py run --scenario baseline --run-id baseline-review
python syncon.py run --scenario validation-stress --run-id validation-review
python syncon.py run --scenario dense-phantom --run-id dense-review
```

Inspect:

```text
runs/demo-run-001/REPORT.md
runs/demo-run-001/validation.json
runs/demo-run-001/red_team.json
runs/demo-run-001/timeline.json
```

Expected result:

- A new evidence package is generated.
- Intentionally seeded unsafe records are rejected by Agent C.
- The run is reproducible from a deterministic seed.
- The selected scenario template is recorded in `scenario.json` and shown in the dashboard registry.

### Optional: Export A Leave-Behind Package

Run:

```bash
python syncon.py export --run-id demo-run-001
```

Inspect:

```text
exports/demo-run-001/SYNCON_EXECUTIVE_REPORT.md
exports/demo-run-001/EXPORT_MANIFEST.json
```

Expected result:

- A polished executive report is generated from the completed run.
- The package includes compact JSON artifacts and the detailed `REPORT.md`.
- `phantoms.json` is omitted by default to keep exports lightweight.

---

## Evaluation Checklist

| Area | Reviewer Question | Expected Signal |
|------|-------------------|-----------------|
| Product clarity | Can I explain SYNCON in one minute? | Executive brief and README make the concept clear |
| Engineering readiness | Could an engineer pick up the build plan? | Engineer handoff package and blueprint define responsibilities, contracts, service boundaries, and acceptance criteria |
| Demo usability | Can I run or inspect the product quickly? | Dashboard and sample evidence package are easy to evaluate |
| Product console depth | Can I compare multiple generated missions? | Dashboard registry lists completed runs with key metrics |
| Insight layer | Does the dashboard explain run differences? | Comparison Insights summarize volume, validation, SNR, detection rate, and profile coverage |
| Decision layer | Does the product translate evidence into next actions? | Operator Decision Layer provides severity, confidence, action, and rationale cards |
| Replay layer | Can I understand what happened without opening JSON? | Mission Replay shows setup, generation, validation, red-team, and evidence steps |
| Scenario depth | Can I demonstrate different synthetic review profiles? | CLI and dashboard expose reusable scenario templates |
| Export readiness | Can I hand someone a generated report? | Export command writes `SYNCON_EXECUTIVE_REPORT.md` and `EXPORT_MANIFEST.json` |
| UI export readiness | Can a reviewer export from the console? | Dashboard `Export Brief` button generates export links |
| Guardrails | Are scope boundaries explicit? | Synthetic-only, unclassified, and not deployment-ready language is repeated |
| Validation | Are results generated by code, not hand-waved? | Tests, JSON artifacts, and reports support the claims |
| Product thinking | Is there a pre/during/post mission lifecycle? | Timeline and report structure show full lifecycle thinking |

---

## Suggested Reviewer Questions

- What are the boundaries between Agent A, Agent B, and Agent C?
- How does Agent C prevent synthetic records from colliding with protected synthetic ground truth?
- What evidence does each run generate?
- What does the executive export include or omit?
- Which claims are validated by tests and which are future roadmap items?
- What would be required before live convoy support could even be considered?
- What would need to change to move from demo runner to production service?

---

## Demo Framing

Use this framing when presenting SYNCON:

> This is not a deployment system. It is an engineer-ready product prototype showing how I would structure a synthetic contested-logistics platform: generate the synthetic layer, validate it against protected ground truth, evaluate it with a red-team stand-in, and report the full mission lifecycle.

The strongest message is that SYNCON turns an abstract defense-tech idea into a runnable, testable, inspectable product workflow.

---

## What To Avoid Claiming

Do not claim:

- Real convoy protection.
- Real adversary deception.
- Real sensor integration.
- EW effects.
- C2 integration.
- Classified data handling.
- Deployment readiness.

The current repository is valuable because it is disciplined about those boundaries.

---

## Recommended Next Engineering Phase

The next engineering phase should convert the local runner into a service-oriented product skeleton:

1. Start from the [Engineer Handoff Package](ENGINEER_HANDOFF_PACKAGE.md).
2. Define stable typed models for scenario, validation, red-team, timeline, decision, and export contracts.
3. Split dashboard actions from execution logic behind an internal service/API boundary.
4. Add schema tests for persisted JSON artifacts.
5. Add richer synthetic telemetry schemas without crossing into operational claims.
