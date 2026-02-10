# Agent Coordination Reference

This document defines the fan-out/fan-in coordination protocol used during SAGE
Phase 3 (Execution). Load this reference when deploying builder agents and managing
wave merges.

Source of truth: `core/engine/wave-orchestrator.yaml` (fan-out/fan-in section) +
`core/communication/communication-protocol.yaml`

## Fan-Out Protocol

### Deployment

For each wave, the supervisor deploys one `sage-builder` instance per active lane:

```
Supervisor
  ├── sage-builder (lane: contract_updates)     → branch: codex/p{P}/w{W}/lane-contract_updates
  ├── sage-builder (lane: logic_updates)         → branch: codex/p{P}/w{W}/lane-logic_updates
  ├── sage-builder (lane: validation_and_tests)  → branch: codex/p{P}/w{W}/lane-validation_and_tests
  └── sage-builder (lane: integration_and_refs)  → branch: codex/p{P}/w{W}/lane-integration_and_references
```

### Lane Responsibilities

| Lane | What It Builds | Key Constraint |
|------|---------------|----------------|
| `contract_updates` | Schema, types, API contracts, interfaces | Must complete before lanes that consume contracts |
| `logic_updates` | Business logic, services, algorithms | Must not modify contract files |
| `validation_and_tests` | Tests, fixtures, mocks | May run concurrently with logic when testing prior work |
| `integration_and_references` | Wiring, docs, configs, CI | Must not modify source code files |

### Builder Agent Assignment

Each builder receives:
1. **Phase and wave ID** — e.g., `P02-W03`
2. **Lane assignment** — e.g., `logic_updates`
3. **File list** — explicit list of files to create/modify (no overlap with other lanes)
4. **Dependencies** — what must be complete before this lane can start
5. **Done criteria** — what constitutes completion for this lane

### Builder Agent Workflow

1. Create branch: `codex/p{PHASE}/w{WAVE}/lane-{CONCERN}`
2. Work ONLY on assigned files within the lane
3. Follow the planning contract for the scope profile
4. Commit work with structured messages: `[P{NN}-W{NN}] lane-{CONCERN}: {description}`
5. Signal completion with structured handoff:
   - Files created/modified
   - Tests written (if applicable)
   - Dependencies consumed
   - Issues encountered

## Fan-In Protocol

### Wave Fan-In

After all lanes in a wave complete:

```
Lane branches ──merge──► Wave integration point
                              │
                         Conflict check
                              │
                    ┌─────────┴──────────┐
                    │                     │
              Clean merge           Conflicts found
                    │                     │
              Wave complete         Resolve conflicts
                                          │
                                   ┌──────┴──────┐
                                   │              │
                              Auto-resolve   Logic conflict
                              (formatting)   (escalate to user)
```

### Merge Order

1. `contract_updates` first (other lanes may depend on it)
2. `logic_updates` second
3. `validation_and_tests` third
4. `integration_and_references` last

### Conflict Resolution

| Conflict Type | Resolution Strategy |
|---------------|-------------------|
| Formatting/whitespace | Auto-resolve with formatter |
| Import ordering | Auto-resolve with linter |
| Same file, different sections | Manual merge (safe) |
| Same file, same lines | Escalate to supervisor |
| Logic/semantic conflict | Escalate to user |

### Merge Cascade

The full merge cascade from lane to project:

```
Lane → Wave fan-in
  Wave fan-in → Milestone gate check
    Milestone fan-in → Phase gate check
      Phase fan-in → Project integration (main/staging)
```

Each level requires its gate to pass before merging upward.

## Branch Isolation Rules

### Naming Convention

```
codex/p{PHASE}/w{WAVE}/lane-{CONCERN}
```

Examples:
- `codex/p01/w01/lane-contract_updates`
- `codex/p03/w07/lane-logic_updates`
- `codex/p05/w02/lane-validation_and_tests`

### Isolation Guarantees

1. Each lane branch is created from the latest integration point
2. No lane branch may be force-pushed or rebased during execution
3. Merge conflicts are resolved at fan-in time, not during execution
4. Branches are cleaned up after successful phase gate

### File Locking

- **Granularity**: File-level
- **Duration**: Until lane fan-in or 2-hour timeout
- **Enforcement**: Pre-assigned file ownership in wave plan
- **Violation**: If a builder attempts to modify a file owned by another lane, it must stop and signal the supervisor

## Communication Protocol

### Status Signals

Builders emit structured status during execution:

| Signal | When | Content |
|--------|------|---------|
| `STARTED` | Lane begins | Branch name, assigned files |
| `PROGRESS` | Every significant step | Files completed, percentage |
| `BLOCKED` | Dependency unresolved | What's needed, from whom |
| `COMPLETED` | All lane work done | Files created/modified, test results |
| `FAILED` | Unrecoverable error | Error details, affected files |

### Dependency Signaling

When a lane depends on another lane's output:

1. **Hard dependency**: Wait for the dependency lane to signal `COMPLETED`
2. **Soft dependency**: Start with placeholders, resolve at fan-in
3. **Runtime dependency**: Signal `BLOCKED`, supervisor re-plans

### Supervisor Coordination

The supervisor (main conversation) manages:
- Deploying builders at wave start
- Monitoring builder status
- Resolving dependencies between lanes
- Triggering fan-in when all lanes complete
- Deploying validator at gate boundaries
- Deciding proceed/retry/escalate based on gate results

## Retry Protocol

### Lane Retry

When a builder fails or produces insufficient quality:

1. Identify specific failure (which files, which tests)
2. Re-deploy builder for the same lane with clarified instructions
3. Builder works on the SAME branch (continues, doesn't restart)
4. Maximum 3 retries per lane per wave

### Wave Retry

When fan-in produces unresolvable conflicts:

1. Identify conflicting lanes
2. Re-deploy conflicting builders with explicit conflict resolution instructions
3. Re-attempt fan-in
4. Maximum 2 wave-level retries

### Escalation

After retry limits are exhausted:
- Present detailed failure report to user
- Include: what was attempted, what failed, what's needed
- Wait for user guidance before proceeding

## Parallelization Rules

1. Maximize independent work streams per wave
2. Preserve strict milestone and task ordering
3. Block fan-in on unresolved contract violations
4. Allow wave cardinality growth when parallelism is beneficial
5. No two agents modify the same file in the same wave
6. Shared types/contracts committed before any consumer lane deploys
