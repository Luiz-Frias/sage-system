---
name: SAGE Phase/Wave Plan Template
purpose: Template for generated implementation plans that satisfy SAGE planning output contract.
layer: execution_template
constraints:
  - phases >= 7
  - waves_per_phase >= 5
  - milestones_per_phase = 4
  - tasks_per_milestone = 15
  - strict sequencing for milestones and tasks
---

# Objective
Generate a phase and wave execution plan that satisfies the planning output contract and gate policy.

## Contract Header
- Plan ID: [plan-id]
- Generated At: [ISO-8601]
- Source Roadmap: [path]
- Phase Count: [>=7]
- Notes: [why expanded above recommended range if applicable]

## Phase Template
Repeat this section for each phase.

### Phase Metadata
- Phase ID: [P01]
- Phase Name: [name]
- Objective: [directive]
- Wave Count: [>=5]
- Milestone Count: [must be 4]

### Waves
Repeat for each wave in phase.

| Wave ID | Focus | Fan-Out Lanes | Hard Dependencies | Fan-In Gate |
|--------|-------|---------------|-------------------|-------------|
| P01-W01 | [focus] | [lane-a, lane-b, lane-c] | [deps] | [gate-id] |

### Milestones
Milestones are sequential and fixed to 4.

#### Milestone P01-M1
- Objective: [directive]
- Sequencing: [strict]
- Tasks: [must include 15 tasks T01..T15]

| Task ID | Description | Owner | Dependencies | Done Criteria |
|--------|-------------|-------|--------------|---------------|
| P01-M1-T01 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T02 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T03 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T04 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T05 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T06 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T07 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T08 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T09 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T10 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T11 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T12 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T13 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T14 | [task] | [owner] | [deps] | [criteria] |
| P01-M1-T15 | [task] | [owner] | [deps] | [criteria] |

- Unit Gate: [required]
- Integration Gate: [required post-init]

#### Milestone P01-M2
- Objective: [directive]
- Tasks: [15 tasks required]
- Unit Gate: [required]
- Integration Gate: [required]

#### Milestone P01-M3
- Objective: [directive]
- Tasks: [15 tasks required]
- Unit Gate: [required]
- Integration Gate: [required]

#### Milestone P01-M4
- Objective: [directive]
- Tasks: [15 tasks required]
- Unit Gate: [required]
- Integration Gate: [required]

### Phase Gates
- Phase-End E2E: [required]
- Rolling Inter-Phase Integration: [required for phase > 1]
- Rolling Cumulative E2E: [required for phase > 1]

## Global Gate Matrix
| Gate ID | Scope | Trigger | Required | Status |
|--------|-------|---------|----------|--------|
| unit-gate | milestone | milestone completion | yes | [ ] |
| integration-gate | milestone | post-init milestone completion | yes | [ ] |
| phase-e2e | phase | phase completion | yes | [ ] |
| rolling-inter-phase | phase | phase>1 completion | yes | [ ] |
| rolling-cumulative-e2e | phase | phase>1 completion | yes | [ ] |

## Validation Checklist
- [ ] phase count >= 7
- [ ] every phase wave count >= 5
- [ ] every phase has exactly 4 milestones
- [ ] every milestone has exactly 15 tasks
- [ ] milestones strictly sequential
- [ ] tasks strictly sequential
- [ ] all required gates declared
