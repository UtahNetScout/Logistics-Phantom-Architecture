# SYNCON Final Demo Guide

**Purpose:** provide the cleanest way to present SYNCON to a technical product leader, engineering reviewer, recruiter, or defense-tech contact.

**Scope:** unclassified synthetic prototype data only. SYNCON is a product demo and engineering blueprint, not an operational deployment system.

---

## 1. What To Show First

Start with the dashboard, then use the documents as proof.

1. Open the local dashboard with `python syncon.py dashboard`.
2. Show the Mission Command Brief and synthetic scope labels.
3. Run or select a completed scenario.
4. Show the Run Registry and Comparison Insights.
5. Show the Operator Decision Layer.
6. Show Mission Replay.
7. Open the Evidence Artifacts.
8. Generate the Executive Export.
9. Point to the Engineer Handoff Package.

This order makes the project feel like a product first, then proves that the architecture and engineering package are real.

---

## 2. Five-Minute Demo Path

Use this when time is short.

```bash
python syncon.py dashboard
```

Open:

```text
http://127.0.0.1:8765
```

Talk track:

> SYNCON is a synthetic contested-logistics product demo. It generates phantom convoy telemetry, validates every synthetic record through Agent C, evaluates the result with a simplified red-team detector, and turns the run into dashboard decisions, replay, timeline, and evidence reports.

Show:

- Mission setup.
- Phantom record count.
- Agent C rejected records.
- Red-team SNR and detection rate.
- Operator decision cards.
- Mission replay cards.
- Export Brief button.

Close:

> The important part is not an operational claim. The important part is the architecture discipline: synthetic-only data, explicit agent boundaries, validation gates, deterministic artifacts, and an engineer-ready handoff package.

---

## 3. Fifteen-Minute Demo Path

Use this when a reviewer wants depth.

1. Read the first paragraph of the Executive Brief.
2. Run the dashboard.
3. Generate a demo scenario.
4. Generate one contrast scenario:

```bash
python syncon.py run --scenario validation-stress --run-id validation-review
```

5. Compare runs in the dashboard registry.
6. Explain the Comparison Insights and Operator Decision Layer.
7. Open `runs/demo-run-001/REPORT.md`.
8. Generate an export:

```bash
python syncon.py export --run-id demo-run-001
```

9. Open `exports/demo-run-001/SYNCON_EXECUTIVE_REPORT.md`.
10. Finish with `docs/ENGINEER_HANDOFF_PACKAGE.md`.

---

## 4. Reviewer Proof Points

| Claim | Where To Prove It |
|-------|-------------------|
| Runnable product surface | Dashboard command and local UI |
| Synthetic generation | `phantoms.json` and run summary metrics |
| Validation boundary | `validation.json`, Agent C metrics, rejected seeded records |
| Red-team evaluation | `red_team.json`, SNR, detection rate, caveat language |
| Product decision support | Operator Decision Layer |
| Mission lifecycle thinking | Mission Replay and `timeline.json` |
| Engineer readiness | Engineer Handoff Package and Engineering Blueprint |
| Evidence export | `SYNCON_EXECUTIVE_REPORT.md` and `EXPORT_MANIFEST.json` |
| Scope discipline | README, Executive Brief, generated reports, and tests |

---

## 5. Strongest Positioning

Use this sentence when someone asks what the project is:

> SYNCON is a runnable synthetic contested-logistics product demo that shows how I would structure an agentic AI platform with generation, validation, red-team evaluation, decision support, mission replay, evidence reporting, and engineer-ready handoff boundaries.

Use this sentence when someone asks whether it is operational:

> No. It is intentionally synthetic and not deployment-ready. The value is the product architecture, validation discipline, test coverage, and handoff clarity.

---

## 6. What Not To Say

Do not present SYNCON as:

- Real convoy protection.
- A live deception tool.
- A C2 or sensor integration.
- A classified or operational system.
- A validated adversary defeat capability.
- A deployment-ready defense product.

The project is stronger because it is clear about those boundaries.

---

## 7. Final Repository Readiness Checklist

- README explains the product in the first screen.
- Executive Brief explains value and boundaries.
- Reviewer Guide provides a 10-minute evaluation path.
- Engineer Handoff Package gives a buildable next-step packet.
- Engineering Blueprint contains the deeper architecture.
- Dashboard provides setup, metrics, comparisons, decisions, replay, timeline, artifacts, and export controls.
- Tests validate the runnable workflow and reviewer package.
- Generated reports and exports repeat the synthetic prototype caveat.

---

## 8. Related Documents

- [README](../README.md)
- [Executive Brief](SYNCON_EXECUTIVE_BRIEF.md)
- [Engineer Handoff Package](ENGINEER_HANDOFF_PACKAGE.md)
- [Engineering Blueprint](ENGINEERING_BLUEPRINT.md)
- [Reviewer Evaluation Guide](REVIEWER_EVALUATION_GUIDE.md)
- [Demo Script](SYNCON_DEMO_SCRIPT.md)
