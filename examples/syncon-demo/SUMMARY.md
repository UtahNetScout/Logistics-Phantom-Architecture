# SYNCON Demo Summary

SYNCON generated a complete synthetic evidence package for a contested-logistics demo scenario.

## Headline

**1 protected synthetic convoy was surrounded by 250 synthetic phantom convoy records in demo mode.**

Agent C rejected all 3 intentionally seeded unsafe phantom records. The simplified red-team detector reported SNR `0.0000` at 250x phantom density.

## Mission Lifecycle

| Stage | Result |
|-------|--------|
| Pre-mission | Scenario configured with 1 protected synthetic convoy and 250 phantom records. |
| During mission | Phantom telemetry generated and validated through Agent C. |
| During mission | Simplified red-team detector evaluated SNR and detection rate. |
| Post-mission | JSON artifacts and `REPORT.md` generated for review. |

## Safety Boundary

- Synthetic prototype data only.
- No classified data.
- No real convoy movement.
- No live sensor integration.
- No operational deployment claim.

## How To Reproduce

```bash
python syncon.py run --scenario demo --run-id syncon-demo --output-dir examples --phantoms 250 --contaminated 3 --workers 1
```
