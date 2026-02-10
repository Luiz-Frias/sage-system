# Wave Orchestration Reference

This document defines the phase/wave/milestone/task execution model used by the SAGE
supervisor. Load this reference during Phase 2 (Plan Generation) and Phase 3 (Execution).

Source of truth: `core/engine/wave-orchestrator.yaml` + `core/engine/planning-output-contract.yaml`

## Execution Hierarchy

```
Project
 └── Phase (major delivery milestone)
      ├── Waves[] (parallel execution units)
      │    └── Lanes[] (concern-separated tracks)
      │         └── Branch: codex/p{P}/w{W}/lane-{CONCERN}
      └── Milestones[] (sequential checkpoints, exactly 4 per phase)
           └── Tasks[] (atomic work units, sequential)
```

Waves execute in parallel (fan-out); milestones execute sequentially (strict order).
Waves produce the work; milestones measure the progress.

## Scope Profiles

### Compact (< 10 files, single concern)

| Dimension | Range |
|-----------|-------|
| Phases | 1–3 |
| Waves per phase | 1–3 |
| Milestones per phase | 2 |
| Tasks per milestone | 5–8 |
| Gate policy | Unit + integration (if multi-component) |

### Standard (10–50 files, multi-component)

| Dimension | Range |
|-----------|-------|
| Phases | 3–6 |
| Waves per phase | 3–5 |
| Milestones per phase | 3–4 |
| Tasks per milestone | 8–12 |
| Gate policy | Unit + integration + phase-E2E |

### Full (50+ files, enterprise, regulatory)

| Dimension | Range |
|-----------|-------|
| Phases | >= 7 (recommended 7–12, unbounded) |
| Waves per phase | >= 5 (recommended 5–10, unbounded) |
| Milestones per phase | Exactly 4 |
| Tasks per milestone | Exactly 15 |
| Gate policy | Full tiered (unit, integration, phase-E2E, rolling) |

All profiles use the same structural patterns — only cardinality differs.

## ID Scheme (Deterministic)

All IDs are deterministic and machine-parseable:

| Entity | Pattern | Example |
|--------|---------|---------|
| Phase | `P{NN}` | `P01`, `P02`, `P12` |
| Wave | `P{NN}-W{NN}` | `P01-W01`, `P03-W07` |
| Milestone | `P{NN}-M{N}` | `P01-M1`, `P01-M4` |
| Task | `P{NN}-M{N}-T{NN}` | `P01-M1-T01`, `P01-M1-T15` |

IDs must be sequential and non-overlapping within their parent scope.

## Fan-Out Lane Definitions

Each wave decomposes into parallel lanes by separation of concerns:

| Lane | Responsibility | Typical Files |
|------|---------------|---------------|
| `contract_updates` | Schema, type definitions, API contracts, interfaces | `*.schema.*`, `types.*`, `*.d.ts`, `*.proto` |
| `logic_updates` | Business logic, services, algorithms, state management | `src/**/*.{rs,py,ts}` (non-test) |
| `validation_and_tests` | Unit tests, integration tests, test fixtures, mocks | `tests/**/*`, `*.test.*`, `*.spec.*` |
| `integration_and_references` | Cross-component wiring, docs, configs, CI/CD | `*.yaml`, `*.toml`, `*.json`, `docs/**` |

### Lane Assignment Rules

- Not all lanes are active in every wave — assign based on wave focus
- A file may appear in only ONE lane per wave (no overlap)
- Contract lane should execute first when other lanes depend on its output
- Test lane may run concurrently with logic lane when tests exist for prior work

## Branch Isolation

Each lane operates on an isolated branch:

```
codex/p{PHASE}/w{WAVE}/lane-contract_updates
codex/p{PHASE}/w{WAVE}/lane-logic_updates
codex/p{PHASE}/w{WAVE}/lane-validation_and_tests
codex/p{PHASE}/w{WAVE}/lane-integration_and_references
```

### Merge Cascade

```
Lane branches → Wave fan-in
  Wave fan-ins → Milestone gate
    Milestone gates → Phase gate
      Phase gates → Main integration
```

### File Locking

- Lock granularity: file-level
- Lock duration: until lane fan-in or 2-hour timeout
- No two lanes may modify the same file in the same wave
- Pre-assign file ownership in wave plan to prevent conflicts

## Dependency Categories

| Category | Description | Handling |
|----------|-------------|----------|
| **Hard** | Dependent work cannot start before prerequisite completes | Block until resolved |
| **Soft** | Dependent work can start with temporary placeholders | Proceed with contract placeholders |
| **Runtime** | Dependency discovered during execution | Resolve via replan and message queue |

## Milestone Sequencing

Milestones within a phase are strictly sequential and non-overlapping:

```
M1 → M2 → M3 → M4
```

For Full profile, each milestone contains exactly 15 tasks in strict order:

```
T01 → T02 → ... → T15
```

For Compact/Standard, task counts are flexible but still sequential.

## Dynamic Expansion Rules

### Phase Expansion
- **Trigger**: Roadmap backlog not exhausted after planned phases
- **Action**: Append phase N+1 with fresh waves and milestones
- **Approval**: Not required (supervisor decides)
- **Constraint**: Preserve milestone/task cardinality per profile

### Wave Expansion
- **Trigger**: Lane collision or critical-path overload detected
- **Action**: Append wave M+1 to redistribute work
- **Approval**: Not required (supervisor decides)
- **Constraint**: Preserve file ownership isolation

### Scope Reallocation
- **Trigger**: Overload detected in a wave
- **Process**: Detect → Propose reallocation → Validate contract → Apply and broadcast
- **Constraint**: Milestone sequence and task cardinality preserved

## Plan Generation Algorithm

1. Ingest roadmap scope and dependency graph
2. Emit initial phases in profile range
3. Append phases until backlog coverage = 100%
4. For each phase: decompose into waves (at least profile minimum)
5. Expand wave count until critical-path depth and lane conflicts are acceptable
6. For each phase: emit milestones (exact count per profile)
7. For each milestone: emit tasks (exact count per profile)
8. Attach gates and done criteria per milestone
9. Attach dependency map and fan-out/fan-in path
10. Validate against contract (Full profile: run script validator)

## Required Plan Structure

A valid plan artifact must include:

```yaml
phases:
  - phase_id: "P01"
    phase_name: "..."
    objective: "..."
    waves:
      - wave_id: "P01-W01"
        focus: "..."
        fan_out_lanes: [...]
        fan_in_gate: {...}
        dependencies: [...]
    milestones:
      - milestone_id: "P01-M1"
        objective: "..."
        tasks:
          - task_id: "P01-M1-T01"
            description: "..."
            owner: "..."
            dependencies: [...]
            done_criteria: "..."
        unit_gate: {...}
        integration_gate: {...}
    phase_gates:
      phase_end_e2e: {...}
      rolling_inter_phase_integration: {...}  # phase > 1
      rolling_cumulative_e2e: {...}            # phase > 1
```

## Performance Metrics

Track these during execution:

| Metric | What It Measures |
|--------|-----------------|
| Plan conformance | Phase/wave/milestone/task count compliance |
| Lane parallelization factor | Active lanes / available lanes per wave |
| Fan-in delay | Time between last lane completion and successful merge |
| Dependency resolution time | Time from dependency discovery to resolution |
| Rework rate | Tasks requiring re-execution / total tasks |
| Gate pass rates | Milestone, phase-E2E, and rolling gate pass rates |
