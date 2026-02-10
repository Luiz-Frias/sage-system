# Quality Gates Reference

This document defines the tiered quality gate policy used by SAGE during Phase 3-4
(Execution and Validation). Load this reference when deploying `sage-validator` and
making proceed/retry/escalate decisions.

Source of truth: `core/engine/planning-output-contract.yaml` (gates section) +
`core/engine/wave-orchestrator.yaml` (gate_policy section)

## Gate Taxonomy

SAGE uses a tiered gate system with increasing scope:

```
Unit Gate (per milestone)
  └── Integration Gate (per milestone, post-init)
       └── Phase-End E2E Gate (per phase)
            └── Rolling Inter-Phase Integration (phase > 1)
                 └── Rolling Cumulative E2E (phase > 1)
```

Each level validates a wider scope than the one below it.

## Gate Types

### 1. Unit Gate (Milestone Level)

**When**: After each milestone completes
**Scope**: Local correctness within the milestone's deliverables
**Required**: Always (all profiles)

**Criteria:**
- Schema and contract checks pass
- Deterministic behavior checks pass
- Type checking passes (language-appropriate)
- Lint checks pass
- Unit tests for milestone deliverables pass

**Validator invocation:**
```
sage-validator(gate_type: "unit", phase: P, milestone: M)
```

### 2. Integration Gate (Milestone Level)

**When**: After each milestone completes (starting from first post-repo-init milestone)
**Scope**: Cross-component contract compatibility
**Required**: All profiles with multi-component output

**Criteria:**
- Cross-lane contract compatibility passes
- Dependency resolution passes
- API contracts match their consumers
- Database schema matches ORM models
- Type definitions consistent across components

**Validator invocation:**
```
sage-validator(gate_type: "integration", phase: P, milestone: M)
```

### 3. Phase-End E2E Gate

**When**: After all milestones in a phase complete
**Scope**: End-to-end functionality for the entire phase
**Required**: Standard and Full profiles

**Criteria:**
- All milestones in the phase completed
- Phase-level end-to-end test suite passes
- All integration points functional
- No regressions from previous milestones

**Validator invocation:**
```
sage-validator(gate_type: "phase_e2e", phase: P)
```

### 4. Rolling Inter-Phase Integration

**When**: After each phase completes (starting from phase 2)
**Scope**: Current phase integrates with all previously completed phases
**Required**: Full profile only

**Criteria:**
- Phase N integrates cleanly with phases 1..N-1
- Cross-phase API contracts compatible
- Cross-phase data flow validated
- No regressions in previously completed phases

**Validator invocation:**
```
sage-validator(gate_type: "rolling_integration", phase: P)
```

### 5. Rolling Cumulative E2E

**When**: After each phase completes (starting from phase 2)
**Scope**: Full end-to-end across ALL completed phases
**Required**: Full profile only

**Criteria:**
- Cumulative end-to-end test suite passes across phases 1..N
- System-level integration verified
- Performance baselines maintained
- No cumulative regressions

**Validator invocation:**
```
sage-validator(gate_type: "rolling_cumulative_e2e", phase: P)
```

## Gate Policy by Profile

| Gate | Compact | Standard | Full |
|------|---------|----------|------|
| Unit | Yes | Yes | Yes |
| Integration | If multi-component | Yes | Yes |
| Phase-End E2E | No | Yes | Yes |
| Rolling Inter-Phase | No | No | Yes |
| Rolling Cumulative E2E | No | No | Yes |

## Confidence Scoring

Each gate produces a confidence score (0–100) based on weighted factors:

| Factor | Weight | Formula |
|--------|--------|---------|
| File completeness | 20% | `(found / expected) * 100` |
| Lint cleanliness | 15% | `max(0, 100 - (errors * 5))` |
| Type safety | 20% | `max(0, 100 - (type_errors * 10))` |
| Test passage | 25% | `(passing / total) * 100` |
| Integration health | 20% | `(checks_passing / checks_total) * 100` |

**Overall score:**
```
score = (0.20 * file_completeness)
      + (0.15 * lint_cleanliness)
      + (0.20 * type_safety)
      + (0.25 * test_passage)
      + (0.20 * integration_health)
```

## Decision Matrix

| Score | Decision | Supervisor Action |
|-------|----------|-------------------|
| 90–100 | **PASS** (excellent) | Merge branches, proceed |
| 85–89 | **PASS** (good) | Merge branches, proceed |
| 70–84 | **CONDITIONAL** | Merge, document issues, carry forward |
| 50–69 | **RETRY** | Re-deploy failing lanes (max 3 retries) |
| 0–49 | **ESCALATE** | Present report to user, await guidance |

### Decision Rules

- **PASS**: All critical checks pass. Minor warnings acceptable.
- **CONDITIONAL**: No blocking failures, but issues exist that should be tracked. Document in milestone notes.
- **RETRY**: Specific, addressable failures. Re-deploy only the failing lanes/agents with clarified instructions.
- **ESCALATE**: Systemic failure or ambiguous issues. Requires human judgment.

## Failure Handling

### Milestone Gate Failure

1. Stop milestone progression
2. Identify failing components
3. Generate remediation tasks
4. Re-deploy affected lanes
5. Rerun gate after remediation
6. After 3 retries → ESCALATE

### Phase Gate Failure

1. Stop phase progression
2. Identify cross-milestone issues
3. Generate remediation plan
4. Execute remediation (may require new wave)
5. Rerun phase gate
6. After 2 retries → ESCALATE

### Rolling Gate Failure

1. Block next phase from starting
2. Identify inter-phase integration issues
3. Emit remediation tasks targeting the integration boundary
4. Execute remediation
5. Rerun rolling gate
6. After 2 retries → ESCALATE

## Validation Scripts

For Full profile, the validator invokes bundled scripts:

### `validate_generated_plan_contract.py`

Validates structural contract compliance:
- Phase count >= 7
- Waves per phase >= 5
- Milestones per phase == 4
- Tasks per milestone == 15
- Strict milestone/task sequencing
- Required gates present at every level
- Rolling gates present for phases after P01

**Usage:**
```bash
python skills/sage/scripts/validate_generated_plan_contract.py <plan.json>
```

### `validate_agent_native_wrappers.sh`

Validates agent-native document format:
- Frontmatter present in Markdown files
- Objective section present
- Applies to `source_documents/`, `languages/`, `domains/`, `core/communication/history/`

**Usage:**
```bash
bash skills/sage/scripts/validate_agent_native_wrappers.sh
```

### `validate_repo_redesign_contract.sh`

Validates repo structure compliance:
- Required contract fields in core engine files
- No stale references in master instructions
- Cardinality constraints in wave templates

**Usage:**
```bash
bash skills/sage/scripts/validate_repo_redesign_contract.sh
```

## Gate Report Format

Every gate produces a structured report:

```markdown
# Gate Report: {gate_type}

## Summary
- **Gate**: {unit|integration|phase_e2e|rolling_integration|rolling_cumulative_e2e}
- **Phase**: P{NN}
- **Milestone**: M{N} (if applicable)
- **Status**: PASS | CONDITIONAL | RETRY | ESCALATE
- **Confidence Score**: {score}/100
- **Timestamp**: {ISO-8601}

## Factor Breakdown
| Factor | Score | Details |
|--------|-------|---------|
| File completeness | {x}/100 | {found}/{expected} files |
| Lint cleanliness | {x}/100 | {errors} errors |
| Type safety | {x}/100 | {type_errors} errors |
| Test passage | {x}/100 | {passing}/{total} tests |
| Integration health | {x}/100 | {checks_passing}/{checks_total} checks |

## Issues
1. {issue description and affected files}

## Recommendation
{Specific recommendation for proceeding or remediation}
```

## Gate Preconditions

| Gate | Preconditions |
|------|--------------|
| Unit | Milestone tasks all marked complete |
| Integration | Unit gate passed for current milestone |
| Phase-End E2E | All milestone integration gates passed |
| Rolling Inter-Phase | Phase-end E2E passed for current phase |
| Rolling Cumulative E2E | Rolling inter-phase integration passed |
