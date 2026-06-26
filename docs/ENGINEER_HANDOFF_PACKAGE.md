# SYNCON Engineer Handoff Package

**Purpose:** give an engineer enough context to build, extend, or critique SYNCON without reverse-engineering the repository.

**Scope:** unclassified synthetic prototype data only. This package does not authorize or describe operational deployment, live convoy use, real sensor integration, classified data handling, EW effects, C2 integration, or deployment-ready deception tooling.

**Primary build objective:** convert the current local prototype into a service-oriented product skeleton while preserving the same synthetic boundaries, evidence artifacts, and reviewer-facing product story.

---

## 1. Handoff Summary

SYNCON is the runnable product shell for the Logistics Phantom architecture. It demonstrates a synthetic contested-logistics workflow:

1. Configure a synthetic scenario.
2. Generate phantom convoy telemetry.
3. Validate synthetic records through Agent C.
4. Evaluate results with a simplified red-team detector.
5. Render dashboard insights, operator decision cards, mission replay, timeline, and evidence exports.

The current implementation is intentionally local and file-backed. The next engineer should keep the current behavior stable while separating the product into typed models, service interfaces, and a future API boundary.

---

## 2. Current Executable Surfaces

| Surface | Command Or File | Engineer Notes |
|---------|-----------------|----------------|
| CLI run | `python syncon.py run --scenario demo` | Runs one synthetic scenario and writes `runs/{run_id}/`. |
| Dashboard | `python syncon.py dashboard` | Starts the local browser dashboard on `127.0.0.1:8765`. |
| Export | `python syncon.py export --run-id demo-run-001` | Creates `exports/{run_id}/SYNCON_EXECUTIVE_REPORT.md`. |
| Tests | `pytest -q` | Validates prototype behavior, dashboard rendering, exports, examples, and performance expectations. |
| Deep blueprint | `docs/ENGINEERING_BLUEPRINT.md` | Full architecture, data contracts, API sketch, roadmap, and backlog. |

---

## 3. Module Responsibilities

| Module | Current Responsibility | Handoff Guidance |
|--------|------------------------|------------------|
| `syncon.py` | Root CLI entry point. | Keep as a thin wrapper around `src/syncon/runner.py`. |
| `src/syncon/runner.py` | Scenario templates, pipeline orchestration, artifact writing, report generation. | Split into scenario service, run service, artifact writer, and report renderer when hardening. |
| `src/syncon/dashboard.py` | Local HTTP dashboard, run registry, comparison insights, operator decisions, mission replay, export controls. | Preserve rendering tests; later replace direct runner calls with API/service calls. |
| `src/syncon/exporter.py` | Executive export package generation. | Keep export manifest stable; add schema validation before broadening package formats. |
| `src/prototype/agent_b_parallel_swarm_generator.py` | Agent B synthetic phantom generation. | Wrap behind a typed `PhantomGenerator` interface. |
| `src/prototype/agent_c_spatial_hash_validator.py` | Agent C optimized validation gate. | Promote to core validation package with typed validation inputs and outputs. |
| `src/prototype/red_team_simulation_lab.py` | Simplified detector experiment. | Treat as a non-operational evaluation plugin, not as an adversary effectiveness claim. |
| `tests/` | Behavioral, integration, adversary, performance, and reviewer-package checks. | Add schema and API tests before refactoring service boundaries. |

---

## 4. Interface Contracts To Stabilize

These are the first contracts an engineer should formalize with dataclasses, Pydantic models, or JSON Schema.

| Contract | Required Fields | Producer | Consumer |
|----------|-----------------|----------|----------|
| `ScenarioConfig` | `run_id`, `scenario_template`, `seed`, `phantom_count`, `contaminated_phantoms`, `classification` | Dashboard or CLI | Run service |
| `ScenarioArtifact` | `scenario_id`, `run_id`, `scenario_label`, `started_at_utc`, `completed_at_utc`, `notes` | Run service | Dashboard, export, report |
| `PhantomRecord` | `phantom_id`, `waypoints`, telemetry metadata, synthetic classification | Agent B | Agent C, artifact writer |
| `ValidationSummary` | `approved_count`, `rejected_count`, `approval_rate`, `all_seeded_unsafe_rejected`, sanitized metrics | Agent C | Dashboard, report, decision layer |
| `RedTeamResult` | `detection_rate`, `snr`, `precision`, `recall`, `f1`, `caveat` | Red-team service | Dashboard, report, comparison insights |
| `TimelineEvent` | `stage`, `event`, `detail` | Run service | Mission replay, report |
| `OperatorDecision` | `severity`, `confidence`, `title`, `action`, `rationale` | Decision service | Dashboard |
| `ExportManifest` | `run_id`, `included_artifacts`, `phantom_payload_included`, `scope` | Export service | Reviewer package |

Contract rule: all persisted outputs must include synthetic scope labels or caveats. No service should silently emit unlabeled operational-looking data.

---

## 5. Dashboard/API Boundary

The current dashboard is a local HTTP surface that directly calls runner/export functions. The hardening path should introduce a backend service layer before any frontend rewrite.

Recommended service boundary:

| UI Action | Service Function | Future API Shape |
|-----------|------------------|------------------|
| Create run | `RunService.start_run(config)` | `POST /api/runs` |
| Load run | `RunService.get_run(run_id)` | `GET /api/runs/{run_id}` |
| List runs | `RunRegistry.list_runs()` | `GET /api/runs` |
| Load artifacts | `ArtifactStore.load(run_id, artifact_name)` | `GET /api/runs/{run_id}/artifacts/{name}` |
| Export brief | `ExportService.export_run(run_id, include_phantoms)` | `POST /api/runs/{run_id}/export` |
| Build decisions | `DecisionService.generate(run_artifacts, registry)` | `GET /api/runs/{run_id}/decisions` |

Implementation note: keep the local file-backed store first. Do not introduce a database until the artifact contracts are stable.

---

## 6. Data Persistence Layout

Current generated run layout:

```text
runs/{run_id}/
|-- scenario.json
|-- phantoms.json
|-- validation.json
|-- red_team.json
|-- timeline.json
|-- REPORT.md
```

Current export layout:

```text
exports/{run_id}/
|-- SYNCON_EXECUTIVE_REPORT.md
|-- EXPORT_MANIFEST.json
|-- REPORT.md
|-- scenario.json
|-- validation.json
|-- red_team.json
|-- timeline.json
|-- phantoms.json          # optional, omitted by default
```

Engineering rule: generated directories remain ignored by git. Committed examples should stay lightweight and reviewer-safe.

---

## 7. Acceptance Criteria For The Next Engineer

Before a handoff branch is considered complete:

- `pytest -q` passes locally.
- `python syncon.py run --scenario demo` produces all required run artifacts.
- `python syncon.py dashboard` renders mission setup, registry, comparison insights, operator decisions, replay, timeline, metrics, and export controls.
- `python syncon.py export --run-id demo-run-001` produces an executive report and manifest.
- Scenario runs are deterministic for a fixed seed.
- Agent C rejects intentionally seeded unsafe synthetic records.
- Dashboard decision cards are deterministic and traceable to local artifacts.
- Every report and export repeats the synthetic, unclassified, not-deployment-ready caveat.
- No code path requires real convoy data, classified input, external sensors, or live network services.

---

## 8. Deployment Assumptions

Current prototype assumptions:

- Runs locally on Windows or Linux.
- Uses local filesystem storage for artifacts.
- Uses synthetic data only.
- Uses Python and standard local test tooling.
- Serves the dashboard on localhost only.

Future production-like prototype assumptions:

- Backend service can be FastAPI or equivalent.
- Frontend can remain server-rendered first, then move to React if the product surface grows.
- Artifact storage can remain file-backed until schema versioning is stable.
- CI should run correctness, reviewer-package, and benchmark smoke checks separately.
- Any cloud deployment would still be a synthetic demo unless legal, security, classification, and operational authority requirements are satisfied.

---

## 9. Security And Safety Boundaries

Hard requirements:

- Do not ingest real convoy telemetry.
- Do not ingest classified data.
- Do not integrate real sensors.
- Do not add live C2 integration.
- Do not describe the current prototype as operational protection.
- Do not remove synthetic/unclassified/not-deployment-ready scope labels.
- Do not let Agent B receive protected ground-truth coordinates in any future architecture.
- Do not let Agent C output protected ground truth; output sanitized validation decisions only.

Future live-support architecture must remain a separate Convoy Shield roadmap item. It would require legal authorization, operational ownership, cybersecurity accreditation, classification handling, C2 integration review, subject-matter expert validation, human approval gates, emergency stop controls, and immutable audit logs before implementation.

---

## 10. Suggested First Engineering Sprint

| Priority | Task | Done When |
|----------|------|-----------|
| P0 | Add typed models for `ScenarioConfig`, `ValidationSummary`, `RedTeamResult`, `TimelineEvent`, and `OperatorDecision`. | Artifacts validate before writing and before dashboard rendering. |
| P0 | Introduce `RunService`, `ArtifactStore`, `ExportService`, and `DecisionService`. | Dashboard no longer calls orchestration helpers directly. |
| P0 | Add schema tests for persisted JSON artifacts. | Schema-breaking changes fail CI. |
| P1 | Add version fields to generated artifacts. | Reports show artifact schema version. |
| P1 | Add API skeleton around the service layer. | Local dashboard can still run without changing user commands. |
| P1 | Add golden export tests. | Executive report structure stays stable. |
| P2 | Add optional frontend polish after services are stable. | Product surface improves without changing artifact contracts. |

---

## 11. Engineer Handoff Checklist

An engineer should be able to answer yes to each item before beginning implementation:

- I understand that SYNCON is synthetic-only and not operational.
- I know which command runs the demo, dashboard, tests, and export.
- I know where run artifacts and exports are written.
- I know which modules own runner, dashboard, export, generator, validator, and detector responsibilities.
- I know which contracts must be stabilized first.
- I know that Convoy Shield is a future authorized live-support roadmap concept, not implemented behavior.
- I know the acceptance criteria for a safe handoff branch.

---

## 12. Related Documents

- [Engineering Blueprint](ENGINEERING_BLUEPRINT.md)
- [SYNCON Executive Brief](SYNCON_EXECUTIVE_BRIEF.md)
- [Reviewer Evaluation Guide](REVIEWER_EVALUATION_GUIDE.md)
- [SYNCON Demo Script](SYNCON_DEMO_SCRIPT.md)
