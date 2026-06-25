# Logistics Phantom: Multi-Agent Swarm Deception Architecture

**A Technical Whitepaper, Product Requirements Document, & Architecture Blueprint**

---

## ⚠️ Disclaimer

This repository is an **unclassified architecture concept, PRD, and prototype proof-of-concept** for portfolio and research purposes. It does not contain classified data, operational routes, real military telemetry, or deployment-ready deception tooling. All code is labeled as unclassified synthetic prototype data. This is a design document and prototype validation artifact intended for review by technical product managers, systems architects, and defense engineering teams.

---

## Origin of the Concept

**Logistics Phantom** originated from a LinkedIn discussion about contested logistics and supply-chain survivability in AI-enabled threat environments. The central question: *How can agentic systems increase uncertainty for adversarial targeting systems while preserving friendly-force data integrity?*

The project explores a specific architectural approach: deploying multi-agent swarms to generate synthetic telemetry that degrades an adversary's signal-to-noise ratio (SNR), making statistical anomaly detection computationally intractable. The goal is **not** to produce an operational deception system, but to architect and validate the core safety mechanisms required before such a system could be fielded.

This document serves as:
1. **Architectural blueprint** for future engineering teams
2. **Product requirements document** (PRD) defining scope and constraints
3. **Prototype validation baseline** demonstrating feasibility of core assumptions
4. **Research artifact** demonstrating systems thinking on AI-enabled deception

For an implementation-oriented handoff, see the dedicated [Engineering Blueprint](docs/ENGINEERING_BLUEPRINT.md). It translates the current prototype into a buildable product plan with product surfaces, data contracts, API boundaries, acceptance criteria, and a phased engineering backlog.

The ultimate product vision is a full convoy lifecycle platform: pre-mission deception planning, future authorized live convoy support, and post-mission reporting that documents the process from beginning to end.

The Phase 1 product shell is named **SYNCON**: Synthetic Convoy Operations Network.

---

## Validation Status Matrix

| Component | Status |
|-----------|--------|
| Architecture Blueprint | ✅ Complete |
| Agent C Validation Gate | ✅ Prototype Tested |
| Parallel Swarm Generation | ✅ Prototype Tested |
| Bezier Pathing | ✅ Prototype Tested |
| Kinematic Velocity Profiling | ✅ Prototype Tested |
| Red-Team Detection Lab | ✅ Prototype Tested |
| Multimodal Synthetic Telemetry | ✅ Concept Prototype |
| Operational Deployment | ❌ Not Implemented |
| Real Sensor Integration | ❌ Not Implemented |
| Classified Data Usage | ❌ None |
| Phase 6 EW/C2 Coordination | ⏳ Future Roadmap Only |

---

## Prototype Modules Overview

All modules reside in `src/prototype/` and are labeled **unclassified synthetic prototype data — portfolio proof-of-concept — not operational telemetry — not deployment-ready deception tooling**.

### `agent_b_parallel_swarm_generator.py`
Validates one prototype assumption: Agent B can generate large synthetic telemetry batches in parallel. Uses Python's `multiprocessing.Pool` to distribute convoy generation across worker processes, demonstrating 100x–1000x phantom multipliers with sub-second wall-clock latency. Connects to Agent B (Phantom Swarm Generator) in the three-agent architecture.

### `bezier_path_generator.py`
Validates prototype feasibility of realistic phantom route generation. Generates smooth, road-like convoy paths using cubic Bezier curves instead of straight-line coordinate noise, producing spatially plausible waypoint sequences. Feeds into Agent B output and increases adversary filtering cost.

### `kinematic_velocity_profiler.py`
Validates that kinematic pathing creates more realistic movement than straight-line coordinate noise. Assigns physically plausible speed profiles to Bezier routes — slowing on curves and accelerating on straights — producing (lat, lon, speed, timestamp) telemetry records. Consumes `bezier_path_generator` output.

### `agent_c_spatial_hash_validator.py`
Optimized Agent C implementation demonstrating that phantom-vs-ground-truth collision detection scales sub-linearly with phantom count. Replaces the O(P·R·W²) pairwise Haversine scan with an expanded-bounds spatial hash grid, validating prototype-scale phantom batches while guarding against latitude-related cell misses. Same functional contract as `agent_c_validator.py`.

### `red_team_simulation_lab.py`
Shows prototype feasibility of using anomaly detection to evaluate phantom realism. Trains an IsolationForest detector on synthetic real-convoy features, then measures how the real-convoy detection rate changes as phantom multiplier increases (10x → 100x → 1000x). Results are simplified simulation metrics — **not operational claims**.

### `multimodal_telemetry_generator.py`
Concept prototype demonstrating cross-modal synthetic telemetry synthesis. Each phantom record includes correlated physical (position/speed/heading), RF (frequency/power/duty cycle), and logistics (manifest/cargo/weight) metadata. Extends Agent B output and raises adversary cross-domain correlation cost.

---

## Scope and Validation Status

This section clarifies what has been validated within prototype scope, what is architectural design, and what remains future work.

### ✅ Implemented & Prototype Tested

**Agent C (QA Gate & Ground Truth Validator)**
- Baseline implemented in `agent_c_validator.py`; optimized in `src/prototype/agent_c_spatial_hash_validator.py`
- Validated claim: Can screen 1,000 generated phantom convoy records against real convoy ground truth and reject intentionally contaminated records with sub-second latency (<50ms)
- This validates **one prototype assumption**—that friendly-fire contamination can be detected and rejected at prototype speeds

**Agent B Parallel Generation**
- Prototype in `src/prototype/agent_b_parallel_swarm_generator.py`
- Validates one prototype assumption: large synthetic telemetry batches can be generated in parallel using multiprocessing

**Bezier Pathing & Kinematic Profiling**
- Prototypes in `src/prototype/bezier_path_generator.py` and `src/prototype/kinematic_velocity_profiler.py`
- Validates that kinematic pathing creates more realistic movement behavior than straight-line coordinate noise

**Red-Team Simulation Lab**
- Prototype in `src/prototype/red_team_simulation_lab.py`
- Shows prototype feasibility in simplified simulation: a basic IsolationForest detector can be used to evaluate phantom realism at varying multipliers

**Prototype Modules (`src/prototype/`)**
- Agent B parallel swarm generator: generates 100×–1000× phantom batches in parallel
- Bezier path generator: smooth, realistic curved routing
- Kinematic velocity profiler: physics-constrained speed profiles
- Spatial hash validator: optimized Agent C for 10,000+ phantom throughput with high-latitude collision regression coverage
- Red-team simulation lab: IsolationForest adversary degraded to SNR < 0.1 at 100× density
- Multimodal telemetry generator: cross-modal physical + RF + logistics consistency

### 🔷 Architectural Design (Not Yet Implemented)

**Agent A (Router)** - Fully specified in architecture section; requires engineering implementation

### ❌ Not Yet Validated (Future Work)

- **Full swarm-scale deployment**: Prototype tested on 10,000 phantoms; field may require 100,000+
- **Adversary detection degradation**: Simplified IsolationForest stand-in tested; real adversary models not available
- **Operational effectiveness**: No measurement of SNR degradation vs. targeting success in real systems
- **Sensor-fusion authenticity**: Phantom signatures are illustrative prototypes; cryptographic realism not implemented
- **Phase 6 EW/C2**: Cross-domain coordination and EW-adjacent modelling are future research concepts and are not implemented in this repository

---

## Validated Claims vs. Future Claims

### ✅ Validated (within prototype scope)

| Claim | Evidence |
|-------|----------|
| Agent B can generate large synthetic telemetry batches within prototype latency budgets | `agent_b_parallel_swarm_generator.py` — 1,000 convoys in <5s, with serial fallback for small batches and multiprocessing for larger batches |
| Agent C can validate phantom coordinates against ground truth using spatial hashing | `agent_c_spatial_hash_validator.py` — 1,000 phantoms <50ms and 10,000 phantoms <100ms in non-instrumented tests |
| Kinematic pathing creates more realistic movement than straight-line coordinate noise | `kinematic_velocity_profiler.py` — speed varies with curve severity while staying within logistics speed bounds |
| A simplified red-team anomaly detector can evaluate phantom realism | `red_team_simulation_lab.py` — detection rate decreases with higher phantom multiplier |

### ❌ Not Yet Validated (require further testing)

| Claim | Why Not Yet Validated |
|-------|----------------------|
| Operational effectiveness against real adversary detection models | Requires red-team testing with real or realistic adversary models |
| Real sensor injection and electromagnetic spectrum effects | Requires physical sensor testbed and RF environment |
| Full production deployment and classified integration | Requires operational environment, legal review, and HITL governance |
| Phase 6 cross-domain EW coordination | Future research concept — not implemented in this repository |

---

## Validated Claim vs. Future Claim (Summary Table)

| Claim | Status | Evidence | Caveat |
|-------|--------|----------|--------|
| **Agent C validates 1,000 phantoms with sub-second latency** | ✅ VALIDATED | `agent_c_validator.py` and spatial hash tests execute under the prototype latency budget | Does not validate Agent B's phantom generator realism |
| **Agent C rejection rate for contaminated records <1%** | ✅ VALIDATED | Script rejects all 5 intentionally contaminated records | Distance-based only; no temporal correlation analysis |
| **Agent B generates 1,000 phantoms in <5 seconds** | ✅ VALIDATED | `agent_b_parallel_swarm_generator.py` executes comfortably below the 5s target in local and CI-style tests | Synthetic data only; real sensor integration not tested |
| **Bezier paths are smooth (score ≥ 0.90)** | ✅ VALIDATED | `bezier_path_generator.py` scores 1.0 in tests | Simulated path only; real road network not used |
| **Kinematic profiling realistic (score ≥ 0.80)** | ✅ VALIDATED | `kinematic_velocity_profiler.py` scores 1.0 in tests | Physics model simplified; not terrain-aware |
| **SNR < 0.1 with 100× phantom multiplier** | ✅ VALIDATED | `red_team_simulation_lab.py` IsolationForest stand-in | Simplified adversary model; real adversary untested |
| **Phantom swarms degrade SNR below thresholds** | ✅ VALIDATED (simplified) | IsolationForest SNR = 0.023 at 100× | Depends on adversary sensor model and ML detection |
| **Full system prevents friendly-fire contamination** | ⚠️ NOT YET VALIDATED | Architecture sound; operational validation pending | Requires real C2 integration testing |

---

## Executive Summary

### The Problem: Contested Logistics in an AI-Enabled Threat Environment

Modern supply chain networks face critical vulnerability: adversarial AI systems with multi-sensor fusion (SIGINT, IMINT, radar, GPS) can now track and target logistics networks with unprecedented precision.

**The Signal-to-Noise Ratio Crisis**: Current decoys assume a 1-to-1 threat model and fail against adversarial AI using statistical anomaly detection and temporal correlation.

### The Approach: Swarm-Based Agentic Synthetic Telemetry Generation

**Logistics Phantom** explores a multi-agent swarm architecture designed to flood adversarial sensors with thousands of synthetic logistics signatures. For every real convoy, the architecture generates orders of magnitude more phantom convoys that exhibit realistic spatiotemporal behavior but exist only in synthetic telemetry.

**Hypothesis**: The adversarial AI's decision problem becomes computationally intractable. **This hypothesis has not been tested against real adversary models and represents a future validation need.**

---

## Threat Model Assumptions

These are **assumptions** requiring red-team testing before any operational claims can be made:

### Adversary Capabilities (Assumed)
1. Multi-sensor fusion integrating SIGINT, IMINT, radar, GPS, and financial data
2. Statistical anomaly detection trained on logistics patterns
3. Temporal correlation across sensor modalities
4. Access to commercial supply chain and open-source intelligence

### Why Current Decoys Fail
- 1-to-1 Decoys: Single phantom filtered if statistically inconsistent
- Isolated Signatures: Phantom without correlated logistics data flagged as synthetic
- Temporal Clustering: Phantoms clustered around real convoys easily filtered

### Logistics Phantom Hypothesis

**If** phantom convoys are statistically consistent, outnumber reals 100:1-1000:1, and include correlated cross-domain signatures, **Then** adversary detection becomes intractable.

**However**: This hypothesis has **not been tested** against real adversary models. Prototypes validate one simplified simulation pathway, not operational deception effectiveness.

---

## Proof of Concept (PoC): Agent C Validation

### What This Validates
- Synthetic phantom data can be screened against ground truth within prototype latency budgets
- Intentionally contaminated records can be rejected at sub-second speeds (<50ms)

### What This Does NOT Validate
- Phantom fidelity or adversary evasion capability
- Full system integration or production scalability
- Operational effectiveness against real detection models

### Key Prototype Results
- **Latency**: <50 milliseconds (validates sub-second requirement at prototype scale)
- **Rejection Rate**: 0.5% (5 intentional contaminations rejected out of 1,000)
- **Approval Rate**: 99.5% throughput
- **No False Positives**: Zero legitimate phantoms rejected in prototype test

---

## How to Run

### Run the SYNCON Product Demo

SYNCON runs the Phase 1 product flow and writes a complete synthetic evidence package under `runs/{run_id}/`.

```bash
python syncon.py run --scenario demo
```

Generated artifacts:
- `scenario.json`
- `phantoms.json`
- `validation.json`
- `red_team.json`
- `timeline.json`
- `REPORT.md`

The default demo generates 10,000 synthetic phantom convoy records around 1 protected synthetic convoy in demo mode. It intentionally seeds a small number of unsafe synthetic phantoms so Agent C can prove the validation gate rejects them.

### Run Prototype Modules

The prototype modules are standalone scripts with deterministic seeds for reproducibility.

```bash
# Run the original Agent C validator (baseline)
python3 agent_c_validator.py

# Run Agent B parallel swarm generator (100x and 1000x multipliers)
python src/prototype/agent_b_parallel_swarm_generator.py

# Run Bezier phantom path generator (500 routes)
python src/prototype/bezier_path_generator.py

# Run kinematic velocity profiler (applies speed profiles to Bezier routes)
python src/prototype/kinematic_velocity_profiler.py

# Run optimized Agent C spatial hash validator (1,000 and 5,000 phantoms)
python src/prototype/agent_c_spatial_hash_validator.py

# Run red-team simulation lab (requires: pip install scikit-learn numpy)
python src/prototype/red_team_simulation_lab.py

# Run multimodal telemetry generator (1,000 records with physical/RF/logistics metadata)
python src/prototype/multimodal_telemetry_generator.py
```

See the **How to Run Tests Locally** section below for the full `pytest` workflow.

---

## System Architecture: The Multi-Agent Workflow

Logistics Phantom uses **three-tier agentic orchestration** with strict agent isolation.

### Agent A: The Router (Real Payload Handler)
- **Status**: Architectural design; not yet implemented
- **Responsibilities**: Ingest logistics data, abstract to seed parameters, maintain ground truth
- **Security**: Isolated container, outputs only abstracted parameters (no coordinates)

### Agent B: The Phantom Swarm (Synthetic Telemetry Generator)
- **Status**: Prototype modules implemented (`agent_b_parallel_swarm_generator.py`, `bezier_path_generator.py`, `kinematic_velocity_profiler.py`, `multimodal_telemetry_generator.py`)
- **Architecture**: Hundreds of parallelizable, stateless agents (100x-1000x multiplier)
- **Generator Logic**: Receives seed parameters → randomizes behavior → outputs synthetic telemetry

### Agent C: The HITL/QA Gate (Ground Truth Validator)
- **Status**: Implemented and prototype tested (`agent_c_validator.py`, `agent_c_spatial_hash_validator.py`)
- **Responsibilities**: Poison prevention, fidelity validation, anomaly detection
- **Security Mechanisms**: Strict isolation, output segregation, decision gate logic

---

## Red-Team Simulation Lab

### Objective
Show prototype feasibility of whether phantom swarms degrade adversary anomaly-detection performance in a simplified simulation.

### Experimental Design
- **Blue Team**: Real convoy feature vectors + phantom swarm at 10x, 100x, 1000x multipliers
- **Red Team**: IsolationForest detector trained on baseline real convoys

### Success Metrics (Prototype)
| Metric | Target |
|--------|--------|
| Real Convoy Detection Rate (at 1000x) | Decreasing trend |
| Agent C Latency | < 50ms for 1,000 phantoms |
| Friendly-Fire Risk | 0% in prototype test |

### Iteration Plan (Research Roadmap)
1. **Phase 1 (Months 1-2)**: Static detector vs. 100x multiplier
2. **Phase 2 (Months 2-3)**: Scale to 250x, 1000x multipliers
3. **Phase 3 (Months 3-4)**: Adaptive red team with model retraining
4. **Phase 4 (Months 4-6)**: Multiple real convoys (100+) + operational load
5. **Phase 5 (Months 6+)**: Integration with logistics simulators (JANUS, OneSAF)

---

## Project Limitations & Future Roadmap

### Current Constraints

1. **Computational Overhead**: 1000x multiplier at production scale requires significant GPU, I/O, and bandwidth resources — not benchmarked
2. **Adversarial Adaptation**: Adversary ML will evolve to exploit phantom signatures over time
3. **Friendly-Fire Risk**: Validation gate failures could contaminate friendly systems; requires operational testing
4. **Regulatory Ambiguity**: Legal review required before any operational deployment
5. **Sensor Fusion Authenticity**: Achieving cryptographically realistic cross-modal signatures is non-trivial

### Future Roadmap

**Phase 2**: Adversary-specific personalization based on threat intelligence profiles

**Phase 3**: Hierarchical phantom generation (mother ship + child variants)

**Phase 4**: Closed-loop learning from observable adversary detection attempts

**Phase 5**: Multimodal sensor fusion (radar, acoustic, financial telemetry)

**Phase 6**: Cross-domain coordination and EW-adjacent modeling are **future research concepts and are not implemented in this repository**. This phase requires legal review, operational authority, and subject-matter expert engagement before any prototype work could begin.

---

## Deployment Considerations

### Target Success Metrics (Pre-Operational, Unvalidated)
1. Adversary SNR < 0.1 (90% noise saturation)
2. Real convoy survival rate improvement measurable
3. System overhead < 20% of logistics budget
4. Validation false negatives < 0.1%

### Governance Requirements
- **Operational Owner**: J-3 (Logistics) / J-2 (Intelligence) joint authority
- **Technical Review Board**: Monthly assessments of swarm fidelity
- **HITL Oversight**: Required for parameter changes, anomaly escalation, deactivation
- **Legal/Compliance Review**: Required before any operational deployment

---

## Conclusion

Logistics Phantom represents an **architectural approach and prototype-level validation** of synthetic telemetry generation for logistics deception concepts. The prototype modules show prototype feasibility in simplified simulation for core mechanisms; operational effectiveness requires rigorous red-team testing and adversarial arms-race preparation.

**What This Repository Provides:**
- Comprehensive architecture for three-tier agent orchestration
- Prototype-tested safety mechanism (Agent C sub-second latency at prototype scale)
- Working prototype modules for Agent B generation pipeline components
- Clear distinction between validated prototype assumptions and future validation needs
- Threat model assumptions and experimental roadmap

**What This Repository Does NOT Provide:**
- Production-ready or deployment-ready code
- Deployed system or operational telemetry
- Red-team validation results against real adversary models
- Operational effectiveness claims
- Classified data, real operational coordinates, or real sensor data

**Path Forward**: This blueprint is suitable for review by engineering teams, security architects, red teams, acquisition teams, and policy makers evaluating legal/compliance implications.

The architecture shows prototype feasibility in simplified simulation, but operational effectiveness requires rigorous red-team testing and adversarial arms-race preparation before any deployment claims can be made.

---

## Test Results & Validation

![Tests](https://github.com/UtahNetScout/Logistics-Phantom-Architecture/actions/workflows/test.yml/badge.svg)
![Benchmarks](https://github.com/UtahNetScout/Logistics-Phantom-Architecture/actions/workflows/benchmark.yml/badge.svg)

> All results below are produced by running the test suite against **synthetic prototype data only**.
> They validate architectural assumptions — not operational effectiveness.

### Validation Status Matrix

| Component | Status | Notes |
|-----------|--------|-------|
| Architecture Blueprint | ✅ Complete | Three-agent design documented |
| Agent C Validation Gate | ✅ Prototype Tested | `agent_c_validator.py` + spatial hash |
| Parallel Swarm Generation | ✅ Prototype Tested | `agent_b_parallel_swarm_generator.py` |
| Bezier Pathing | ✅ Prototype Tested | `bezier_path_generator.py` |
| Kinematic Velocity Profiling | ✅ Prototype Tested | `kinematic_velocity_profiler.py` |
| Red-Team Detection Lab | ✅ Prototype Tested | `red_team_simulation_lab.py` |
| Multimodal Synthetic Telemetry | ✅ Concept Prototype | `multimodal_telemetry_generator.py` |
| Operational Deployment | ❌ Not Implemented | Requires engineering + legal review |
| Real Sensor Integration | ❌ Not Implemented | Future work |
| Classified Data Usage | ✅ None | All data synthetic |
| Phase 6 EW/C2 Coordination | 🔷 Future Roadmap Only | Not implemented in this repository |

### Test Suite Results

| Component | Target | Observed Result | Status |
|-----------|--------|-----------------|--------|
| Agent B Generation (1,000 phantoms) | < 5 s | <1 s observed locally | ✅ PASS |
| Agent C Validation (10,000 phantoms) | < 100 ms | <100 ms non-instrumented test target | ✅ PASS |
| Agent C Validation (1,000 phantoms) | < 50 ms | <50 ms non-instrumented test target | ✅ PASS |
| Bezier Path Smoothness | ≥ 0.90 score | 1.00 | ✅ PASS |
| Kinematic Realism Score | ≥ 0.80 | 1.00 | ✅ PASS |
| Red-Team SNR at 100× | < 0.1 | ~0.023 | ✅ PASS |
| Red-Team SNR at 1000× | < 0.1 | ~0.002 | ✅ PASS |
| False Positive Rate | 0% | 0% | ✅ PASS |
| End-to-End Pipeline (1,000×) | < 10 s | Prototype pipeline remains below target in non-instrumented tests | ✅ PASS |
| Parallelisation (determinism) | Serial = Parallel | Identical | ✅ PASS |

> Exact numbers vary by machine. Run `pytest tests/ -v -s` locally to reproduce.

### Prototype Modules

Six prototype modules in `src/prototype/` validate individual architectural assumptions:

| Module | What It Validates |
|--------|-------------------|
| `agent_b_parallel_swarm_generator.py` | Parallel phantom generation at 100×–1000× multipliers with deterministic seeds |
| `bezier_path_generator.py` | Smooth curved routes that pass through all waypoints, length ≥ straight-line |
| `kinematic_velocity_profiler.py` | Physics-constrained speed profiles — vehicles slow on curves, accelerate on straights |
| `agent_c_spatial_hash_validator.py` | O(N) spatial hash validation; sub-50ms for 1,000 phantoms, sub-100ms for 10,000 |
| `red_team_simulation_lab.py` | IsolationForest adversary detector degrades to SNR < 0.1 at 100× phantom density |
| `multimodal_telemetry_generator.py` | Cross-modal consistency: fuel tracks distance, RF power tracks rest-stop state |

### Validated Claims vs. Future Claims

**✅ Validated by this prototype:**
- Agent B can generate large synthetic telemetry batches in parallel with deterministic seeds.
- Agent C can validate generated phantom coordinates against friendly ground truth using spatial hashing within the documented prototype latency budgets.
- Kinematic pathing creates more realistic movement behaviour than straight-line coordinate noise.
- A simplified red-team anomaly detector's SNR is reduced below 0.1 at a 100× phantom multiplier.
- Bezier paths produce smooth, non-jagged routes with length ≥ straight-line distance.
- Cross-modal telemetry (physical, RF, logistics manifest) maintains internal consistency.

**❌ Not validated — requires further work:**
- Operational effectiveness against real adversary detection models.
- Actual adversary deception or targeting disruption.
- Real sensor injection or cryptographic signature realism.
- Real EW, jamming, or C2 effects (Phase 6 — future roadmap concept only).
- Production deployment or classified data integration.

### Validation Boundaries

**What the tests prove** (prototype-level assumptions only):
- Architectural sub-systems function correctly in isolation and together.
- Performance targets are achievable at prototype scale on commodity hardware.
- The IsolationForest adversary stand-in is degraded by high-fidelity phantom density.

**What the tests do NOT prove:**
- Operational effectiveness against real adversary ML models.
- Electromagnetic or acoustic signature authenticity.
- Integration with real C2 systems or sensor networks.
- Legal or compliance clearance for any operational use.

---

## How to Run Tests Locally

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests (verbose + console metrics)
pytest tests/ -v -s

# Run specific test categories
pytest tests/unit/ -v -s
pytest tests/integration/ -v -s
pytest tests/adversary/ -v -s
pytest tests/performance/ -v -s

# Run correctness tests with coverage report
# Performance tests should be run separately without coverage instrumentation.
pytest tests/unit tests/integration tests/adversary -m "not performance" --cov=src/prototype --cov-report=html
# Open htmlcov/index.html to view

# Run prototype scripts directly
python src/prototype/agent_b_parallel_swarm_generator.py
python src/prototype/bezier_path_generator.py
python src/prototype/kinematic_velocity_profiler.py
python src/prototype/agent_c_spatial_hash_validator.py
python src/prototype/red_team_simulation_lab.py
python src/prototype/multimodal_telemetry_generator.py

# Run the original Agent C validator
python agent_c_validator.py
```

### Test Coverage & CI/CD

- **GitHub Actions**: Tests run automatically on every push and pull request via `.github/workflows/test.yml`
- **Monthly Benchmarks**: Performance benchmarks run monthly via `.github/workflows/benchmark.yml`
- **Reproducibility**: All tests use deterministic seeds (`seed=42`) — `pytest tests/ -v` produces identical results on every run
- **Artifacts**: Test results, coverage reports, and benchmark data are uploaded as GitHub Actions artifacts on every run

---

## Document Control

**Version**: 3.0  
**Classification**: UNCLASSIFIED (Whitepaper, Architecture Blueprint & Prototype PoC)  
**Last Updated**: 2026-06-24  
**Authored By**: Technical Architecture Division  
**Review Cycle**: Quarterly  
**Next Review**: 2026-09-24

---

*For questions, inquiries, or collaboration opportunities, contact the Defense Tech Architecture team.*
