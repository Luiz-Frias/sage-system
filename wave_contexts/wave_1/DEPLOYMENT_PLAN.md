---
name: SAGE Deployment Plan Example (Contract-Compliant)
purpose: Reference example showing how generated plans encode 7+ phases with 5+ waves and strict milestone/task gates.
layer: example_plan
---

# Generated Plan Snapshot

## Contract Summary
- Phase Count: 7
- Waves per Phase: 5
- Milestones per Phase: 4
- Tasks per Milestone: 15
- Rolling Gates: enabled after phase 1

## Phase P01 - Repository Initialization and Baseline Contracts

### Waves (P01)
| Wave ID | Focus | Fan-Out Lanes | Dependencies | Fan-In Gate |
|--------|-------|---------------|--------------|-------------|
| P01-W01 | Repo bootstrap | scaffolding, config, docs, validation, qa | none | gate-p01w01 |
| P01-W02 | Core contract files | engine, config, interface, template, qa | P01-W01 | gate-p01w02 |
| P01-W03 | Context materialization | source ingest, dependency map, risk map, ownership map, qa | P01-W02 | gate-p01w03 |
| P01-W04 | Test harness initialization | unit harness, integration harness, e2e harness, reporting, qa | P01-W03 | gate-p01w04 |
| P01-W05 | Phase closeout | fan-in, reconciliation, gate report, release note, qa | P01-W04 | gate-p01w05 |

### Milestone P01-M1 (15 Tasks)
| Task ID | Description | Owner | Dependencies | Done Criteria |
|--------|-------------|-------|--------------|---------------|
| P01-M1-T01 | Validate repository baseline | supervisor | none | baseline report emitted |
| P01-M1-T02 | Build initial dependency graph | analysis lane | T01 | graph saved |
| P01-M1-T03 | Define lane ownership map | orchestration lane | T02 | ownership map saved |
| P01-M1-T04 | Create wave branch matrix | orchestration lane | T03 | branch matrix approved |
| P01-M1-T05 | Define gate matrix | qa lane | T04 | gate matrix saved |
| P01-M1-T06 | Run unit harness smoke | qa lane | T05 | unit smoke green |
| P01-M1-T07 | Initialize integration harness | qa lane | T06 | integration harness ready |
| P01-M1-T08 | Validate communication channels | comms lane | T05 | channel checks green |
| P01-M1-T09 | Validate conflict log wiring | comms lane | T08 | conflict checks green |
| P01-M1-T10 | Capture risk register | analysis lane | T03 | risk register saved |
| P01-M1-T11 | Capture mitigation matrix | analysis lane | T10 | mitigation matrix saved |
| P01-M1-T12 | Execute lane fan-in dry run | orchestration lane | T04-T11 | fan-in dry run pass |
| P01-M1-T13 | Execute milestone unit gate | qa lane | T12 | unit gate pass |
| P01-M1-T14 | Execute milestone integration gate | qa lane | T13 | integration gate pass |
| P01-M1-T15 | Publish milestone checkpoint | supervisor | T14 | checkpoint published |

### Milestone P01-M2
- 15 sequential tasks required.
- Unit gate required.
- Integration gate required.

### Milestone P01-M3
- 15 sequential tasks required.
- Unit gate required.
- Integration gate required.

### Milestone P01-M4
- 15 sequential tasks required.
- Unit gate required.
- Integration gate required.

### Phase P01 Gates
- Phase-End E2E: required.
- Rolling Inter-Phase Integration: not required for phase 1.
- Rolling Cumulative E2E: not required for phase 1.

## Phase P02..P07
For each subsequent phase:
1. Keep wave count >= 5.
2. Keep milestone count exactly 4.
3. Keep task count exactly 15 per milestone.
4. Enforce rolling inter-phase integration and cumulative E2E gates.

## Global Success Criteria
- [ ] Contract cardinality is satisfied for all generated phases.
- [ ] All milestone unit and integration gates pass.
- [ ] All phase-end E2E gates pass.
- [ ] All rolling gates pass after phase 1.
