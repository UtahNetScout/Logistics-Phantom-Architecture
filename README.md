# Logistics Phantom: Multi-Agent Swarm Deception Architecture

**A Technical Whitepaper, Product Requirements Document, & Architecture Blueprint**

---

## ⚠️ Disclaimer

This repository is an **unclassified architecture concept, PRD, and limited proof-of-concept** for portfolio and research purposes. It does not contain classified data, operational routes, real military telemetry, or deployment-ready deception tooling. This is a design document and validation concept intended for review by technical product managers, systems architects, and defense engineering teams.

---

## Origin of the Concept

**Logistics Phantom** originated from a LinkedIn discussion about contested logistics and supply-chain survivability in AI-enabled threat environments. The central question: *How can agentic systems increase uncertainty for adversarial targeting systems while preserving friendly-force data integrity?*

The project explores a specific architectural approach: deploying multi-agent swarms to generate synthetic telemetry that degrades an adversary's signal-to-noise ratio (SNR), making statistical anomaly detection computationally intractable. The goal is **not** to produce an operational deception system, but to architect and validate the core safety mechanisms required before such a system could be fielded.

This document serves as:
1. **Architectural blueprint** for future engineering teams
2. **Product requirements document** (PRD) defining scope and constraints
3. **Validation baseline** for the proof-of-concept (Agent C only, to date)
4. **Research artifact** demonstrating systems thinking on AI-enabled deception

---

## Scope and Validation Status

This section clarifies what has been validated, what is architectural design, and what remains future work.

### ✅ Implemented & Validated

**Agent C (QA Gate & Ground Truth Validator)**
- Fully implemented in `agent_c_validator.py` and `src/prototype/agent_c_spatial_hash_validator.py`
- Validated claim: Can screen 1,000 generated phantom convoy records against real convoy ground truth and reject intentionally contaminated records with sub-second latency (<50ms)
- Proof: Running the script locally generates realistic phantom convoys, intentionally contaminates a small percentage, and validates separation with collision detection
- Operational claim: This validates **one critical safety assumption**—that friendly-fire contamination can be detected and rejected at operational speeds

**Prototype Modules (`src/prototype/`)**
- Agent B parallel swarm generator: generates 100×–1000× phantom batches in parallel
- Bezier path generator: smooth, realistic curved routing
- Kinematic velocity profiler: physics-constrained speed profiles
- Spatial hash validator: optimised Agent C for 10,000+ phantom throughput
- Red-team simulation lab: IsolationForest adversary degraded to SNR < 0.1 at 100× density
- Multimodal telemetry generator: cross-modal physical + RF + logistics consistency

### 🔷 Architectural Design (Not Yet Implemented)

**Agent A (Router)** - Fully specified in architecture section; requires engineering implementation

**Agent B (Phantom Swarm)** - Fully specified generator logic; requires full ML/agent implementation

### ❌ Not Yet Validated (Future Work)

- **Full swarm-scale deployment**: Prototype tested on 10,000 phantoms; field may require 100,000+
- **Adversary detection degradation**: Simplified IsolationForest stand-in tested; real adversary models not available
- **Operational effectiveness**: No measurement of SNR degradation vs. targeting success in real systems
- **Sensor-fusion authenticity**: Phantom signatures are illustrative prototypes; cryptographic realism not implemented
- **Phase 6 EW/C2**: Cross-domain coordination and EW-adjacent modelling are future research concepts and are not implemented in this repository

---

## Validated Claim vs. Future Claim

| Claim | Status | Evidence | Caveat |
|-------|--------|----------|--------|
| **Agent C validates 1,000 phantoms with sub-second latency** | ✅ VALIDATED | `agent_c_validator.py` executes in <50ms | Does not validate Agent B's phantom generator realism |
| **Agent C rejection rate for contaminated records <1%** | ✅ VALIDATED | Script rejects all 5 intentionally contaminated records | Distance-based only; no temporal correlation analysis |
| **Agent B generates 1,000 phantoms in <5 seconds** | ✅ VALIDATED | `agent_b_parallel_swarm_generator.py` executes in ~40ms | Synthetic data only; real sensor integration not tested |
| **Bezier paths are smooth (score ≥ 0.90)** | ✅ VALIDATED | `bezier_path_generator.py` scores 1.0 in tests | Simulated path only; real road network not used |
| **Kinematic profiling realistic (score ≥ 0.80)** | ✅ VALIDATED | `kinematic_velocity_profiler.py` scores 1.0 in tests | Physics model simplified; not terrain-aware |
| **SNR < 0.1 with 100× phantom multiplier** | ✅ VALIDATED | `red_team_simulation_lab.py` IsolationForest stand-in | Simplified adversary model; real adversary untested |
| **Phantom swarms degrade SNR below thresholds** | ✅ VALIDATED (simplified) | IsolationForest SNR = 0.023 at 100× | Depends on adversary sensor model and ML detection |
| **Full system prevents friendly-fire contamination** | ⚠️ NOT YET VALIDATED | Architecture sound; operational validation pending | Requires real C2 integration testing |

---

## Executive Summary

### The Problem: Contested Logistics in an AI-Enabled Threat Environment

Modern supply chain networks face critical vulnerability: adversarial AI systems with multi-sensor fusion (SIGINT, IMINT, radar, GPS) can now track and target logistics networks with unprecedented precision.

**The Signal-to-Noise Ratio Crisis**: Current decoys assume 1-to-1 threat model and fail against adversarial AI using statistical anomaly detection and temporal correlation.

### The Solution: Swarm-Based Agentic Cyber Deception

**Logistics Phantom** implements a multi-agent swarm architecture that floods adversarial sensors with thousands of synthetic logistics signatures. For every real convoy, Logistics Phantom generates orders of magnitude more phantom convoys that exhibit realistic spatiotemporal behavior but exist only in telemetry.

**Strategic Effect**: The adversarial AI's decision problem becomes computationally intractable.

---

## Threat Model Assumptions

These are **assumptions** requiring red-team testing:

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

**However**: This hypothesis has **not been tested** against real adversary models.

---

## Proof of Concept (PoC): Agent C Validation

### What This Proves
- Synthetic phantom data can be screened against ground truth at operational latency
- Contaminated records can be rejected at sub-second speeds (<50ms)

### What This Does NOT Prove
- Phantom fidelity or adversary evasion capability
- Full system integration or production scalability
- Operational effectiveness against real detection models

### Key Results
- **Latency**: <50 milliseconds (validates sub-second requirement)
- **Rejection Rate**: 0.5% (5 intentional contaminations rejected)
- **Approval Rate**: 99.5% throughput
- **No False Positives**: Zero legitimate phantoms rejected

### How to Run

```bash
# Original Agent C validator
python3 agent_c_validator.py

# Prototype modules
python3 src/prototype/agent_b_parallel_swarm_generator.py
python3 src/prototype/bezier_path_generator.py
python3 src/prototype/kinematic_velocity_profiler.py
python3 src/prototype/agent_c_spatial_hash_validator.py
python3 src/prototype/red_team_simulation_lab.py
python3 src/prototype/multimodal_telemetry_generator.py
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
- **Status**: Prototype implemented (`src/prototype/agent_b_parallel_swarm_generator.py`)
- **Architecture**: Hundreds of parallelizable, stateless agents (100x-1000x multiplier)
- **Generator Logic**: Receives seed parameters → randomizes behavior → outputs synthetic telemetry

### Agent C: The HITL/QA Gate (Ground Truth Validator)
- **Status**: Implemented and validated
- **Responsibilities**: Poison prevention, fidelity validation, anomaly detection
- **Security Mechanisms**: Strict isolation, output segregation, decision gate logic

---

## Recommended Next Experiment: Red-Team Simulation Lab

### Objective
Validate whether phantom swarms actually degrade adversary detection rates.

### Experimental Design
- **Blue Team**: Real convoy data + Agent A routing + Agent B phantom generation (100x, 250x, 1000x multipliers)
- **Red Team**: Detection model trained on historical logistics + multi-sensor fusion + statistical anomaly detection

### Success Metrics
| Metric | Target |
|--------|--------|
| Real Convoy Detection Rate | < 50% |
| SNR Reduction | < 0.1 (10:1 ratio) |
| Agent C Latency | < 100ms for 10,000 phantoms |
| Friendly-Fire Risk | 0% |

### Iteration Plan
1. **Phase 1 (Months 1-2)**: Static detector vs. 100x multiplier
2. **Phase 2 (Months 2-3)**: Scale to 250x, 1000x multipliers
3. **Phase 3 (Months 3-4)**: Adaptive red team with model retraining
4. **Phase 4 (Months 4-6)**: Multiple real convoys (100+) + operational load
5. **Phase 5 (Months 6+)**: Integration with logistics simulators (JANUS, OneSAF)

---

## Project Limitations & Future Roadmap

### Current Constraints

1. **Computational Overhead**: 1000x multiplier requires ~100 GPU-hours, 50TB/day I/O, 2Gbps bandwidth
2. **Adversarial Adaptation**: Adversary ML will evolve to exploit phantom signatures
3. **Friendly-Fire Risk**: Validation gate failures could contaminate friendly systems
4. **Regulatory Ambiguity**: Legal review required before operational deployment
5. **Sensor Fusion Authenticity**: Achieving cryptographic realism is non-trivial

### Future Roadmap

**Phase 2**: Adversary-specific personalization based on threat intelligence profiles

**Phase 3**: Hierarchical phantom generation (mother ship + child variants)

**Phase 4**: Closed-loop learning from observable adversary detection attempts

**Phase 5**: Multimodal sensor fusion (radar, acoustic, financial telemetry)

**Phase 6**: Cross-domain coordination (phantom logistics + fake C&C + EW)

---

## Deployment Recommendations

### Success Metrics
1. Adversary SNR < 0.1 (90% noise saturation)
2. Real convoy survival rate improvement measurable
3. System overhead < 20% of logistics budget
4. Validation false negatives < 0.1%

### Governance Structure
- **Operational Owner**: J-3 (Logistics) / J-2 (Intelligence) joint authority
- **Technical Review Board**: Monthly assessments of swarm fidelity
- **HITL Oversight**: Required for parameter changes, anomaly escalation, deactivation

---

## Conclusion

Logistics Phantom represents an **architectural approach** to degrading adversarial AI's targeting capability while maintaining friendly-force operational security.

**What This Repository Provides:**
- Comprehensive architecture for three-tier agent orchestration
- Validated safety mechanism (Agent C sub-second latency)
- Clear distinction between design, implementation, and validation
- Threat model assumptions and experimental roadmap

**What This Repository Does NOT Provide:**
- Production-ready code for all three agents
- Deployed system or operational telemetry
- Red-team validation results
- Operational effectiveness claims

**Path Forward**: This blueprint suits engineering teams, security architects, red teams, acquisition teams, and policy makers evaluating legal/compliance implications.

The architecture is **sound and tractable**, but operational effectiveness requires rigorous red-team testing and adversarial arms-race preparation.

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
| Agent B Generation (1,000 phantoms) | < 5 s | ~40 ms | ✅ PASS |
| Agent C Validation (10,000 phantoms) | < 100 ms | ~95 ms | ✅ PASS |
| Agent C Validation (1,000 phantoms) | < 50 ms | ~10 ms | ✅ PASS |
| Bezier Path Smoothness | ≥ 0.90 score | 1.00 | ✅ PASS |
| Kinematic Realism Score | ≥ 0.80 | 1.00 | ✅ PASS |
| Red-Team SNR at 100× | < 0.1 | ~0.023 | ✅ PASS |
| Red-Team SNR at 1000× | < 0.1 | ~0.002 | ✅ PASS |
| False Positive Rate | 0% | 0% | ✅ PASS |
| End-to-End Pipeline (1,000×) | < 10 s | ~0.05 s | ✅ PASS |
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
- Agent C can validate generated phantom coordinates against friendly ground truth using spatial hashing at sub-50ms latency.
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

# Run with coverage report
pytest tests/ --cov=src/prototype --cov-report=html
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

**Version**: 2.0  
**Classification**: UNCLASSIFIED (Whitepaper & Architecture Blueprint)  
**Last Updated**: 2026-06-23  
**Authored By**: Technical Architecture Division  
**Review Cycle**: Quarterly  
**Next Review**: 2026-09-23

---

*For questions, inquiries, or collaboration opportunities, contact the Defense Tech Architecture team.*
