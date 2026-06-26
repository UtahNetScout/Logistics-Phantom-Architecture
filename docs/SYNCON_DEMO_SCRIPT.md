# SYNCON Demo Script

This script is designed for a short walkthrough with a technical product leader, engineer, recruiter, or defense-tech contact.

---

## 30-Second Version

SYNCON is a synthetic contested-logistics product demo built from the Logistics Phantom architecture. It generates phantom convoy telemetry around a protected synthetic convoy, validates the synthetic records through Agent C, runs a simplified red-team detector, and produces a complete evidence report covering pre-mission, during-mission, and post-mission activity.

The key point is not that this is operational. It is not. The key point is that the architecture is runnable, inspectable, testable, and ready for an engineering handoff.

---

## Two-Minute Walkthrough

Start with the product:

> SYNCON stands for Synthetic Convoy Operations Network. It is the runnable product shell for the Logistics Phantom architecture.

Explain the problem space:

> Contested logistics is becoming a data problem. If adversary systems can fuse movement, logistics, RF, and other signals, then protecting a convoy is not only about armor or routing. It is also about managing what the adversary thinks it can see.

Show the architecture:

> I separated the system into three agents. Agent A is the future router and ground-truth abstraction layer. Agent B generates synthetic phantom telemetry. Agent C validates the output so synthetic records do not contaminate protected ground truth.

Run or show the dashboard:

```bash
python syncon.py dashboard
```

Then open:

```text
http://127.0.0.1:8765
```

Call out the important surfaces:

- Mission setup.
- Synthetic scope labels.
- Phantom record count.
- Agent C validation metrics.
- Red-team SNR metrics.
- Run registry comparison across completed demo missions.
- Mission lifecycle timeline.
- Generated artifact links.

Show the evidence package:

```bash
python syncon.py run --scenario demo
```

Then point to:

```text
runs/demo-run-001/REPORT.md
```

Export the leave-behind:

```bash
python syncon.py export --run-id demo-run-001
```

Then point to:

```text
exports/demo-run-001/SYNCON_EXECUTIVE_REPORT.md
```

Or use the dashboard:

> Select the completed run, click **Export Brief**, then open `SYNCON_EXECUTIVE_REPORT.md` from the Executive Export panel.

Close with the boundary:

> This does not claim real-world deception or live convoy protection. It demonstrates how I think as an AI systems architect: define the product surface, separate agent responsibilities, enforce validation gates, generate evidence, and keep the claims honest.

---

## What To Emphasize

- This is a product demo, not only a whitepaper.
- The repo includes tests, a dashboard, generated artifacts, a sample evidence package, and an engineering blueprint.
- The export command generates a polished executive leave-behind from a completed run.
- The dashboard can generate the same executive export without using the command line.
- The concept is intentionally framed around synthetic data and validation boundaries.
- The long-term vision is pre-mission planning, future authorized live support, and post-mission reporting.

---

## Strong Closing Line

> SYNCON is my attempt to turn a contested-logistics idea into something an engineer could actually evaluate, build from, and challenge.
