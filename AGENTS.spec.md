# AGENTS.spec.md — SAGE Orchestration System v2.0

## State Machine

```
                         /sage <description>
                                │
                    ┌───────────▼───────────┐
                    │  SCOPE DETECTION      │
                    │  agent: supervisor     │
                    │  output: profile       │
                    └───────────┬───────────┘
                                │ Compact | Standard | Full
                    ┌───────────▼───────────┐
                    │  PHASE 1: ANALYSIS    │
                    │  agent: sage-analyzer  │
                    │  mode: read-only       │
                    └───────────┬───────────┘
                                │ output: analysis + profile recommendation
                    ┌───────────▼───────────┐
                    │  PHASE 2: PLANNING    │
                    │  agent: supervisor     │
                    │  ref: wave-orchestration│
                    └───────────┬───────────┘
                                │ output: phase/wave plan (requires user approval)
                    ┌───────────▼───────────┐
              ┌────►│  PHASE 3: EXECUTION   │◄──── retry (max 3 per lane)
              │     │  agents: fan-out lanes │
              │     │  ref: agent-coordination│
              │     └───────────┬───────────┘
              │                 │ output: lane branches + artifacts
              │     ┌───────────▼───────────┐
              │     │  MILESTONE GATE        │
              │     │  agent: sage-validator  │
              │     │  ref: quality-gates     │
              │     └───────────┬───────────┘
              │                 │
              │        ┌───────┴───────┐
              │        │ confidence?    │
              │        └──┬──┬──┬──┬───┘
              │           │  │  │  │
              │    >=85   │  │  │  │  <50
              │    PASS   │  │  │  │  ESCALATE ──► user intervention
              │           │  │  │  │
              │      70-84│  │  │50-69
              │   CONDITIONAL│  │RETRY ────────────┘
              │           │  │
              │           │  │ (more milestones in phase?)
              │           │  └── yes ──► next milestone ──► EXECUTION
              │           │
              │           ▼ (all milestones done)
              │     ┌─────────────────┐
              │     │  PHASE GATE     │
              │     │  phase-end E2E  │
              │     │  + rolling gates│
              │     └────────┬────────┘
              │              │
              │         ┌────┴────┐
              │         │ pass?   │
              │         └──┬──┬───┘
              │            │  │
              │       pass │  │ fail → remediate → rerun
              │            │
              │            ▼ (more phases?)
              └──── yes ◄──┤
                           │ no
                    ┌──────▼────────────┐
                    │ PHASE 5: LEARNING │
                    │ agent: sage-historian│
                    │ model: haiku        │
                    └──────┬────────────┘
                           │
                    ┌──────▼────────────┐
                    │ PHASE 6: COMPLETE │
                    │ final cumulative   │
                    │ E2E + summary      │
                    └───────────────────┘
```

### State Transition Table

| From | To | Trigger | Preconditions |
|------|----|---------|---------------|
| idle | SCOPE_DETECT | `/sage <desc>` | Project description provided |
| SCOPE_DETECT | ANALYSIS | Profile selected | Compact/Standard/Full determined |
| ANALYSIS | PLANNING | Analysis complete | sage-analyzer returned report |
| PLANNING | EXECUTION | User approves plan | Plan generated, validated (Full: script check) |
| EXECUTION | MILESTONE_GATE | All lanes in wave complete | Lane branches ready for fan-in |
| MILESTONE_GATE | EXECUTION (next wave) | PASS/CONDITIONAL & waves remain | Branches merged |
| MILESTONE_GATE | EXECUTION (next milestone) | PASS/CONDITIONAL & milestone boundary | Milestone gates passed |
| MILESTONE_GATE | EXECUTION (retry) | RETRY (50-69) & retries < 3 | Failing lanes identified |
| MILESTONE_GATE | ESCALATE | ESCALATE (< 50) or retries >= 3 | Gate report generated |
| PHASE_GATE | EXECUTION (next phase) | All gates pass & phases remain | Rolling gates pass |
| PHASE_GATE | LEARNING | All gates pass & no phases remain | All phases complete |
| PHASE_GATE | REMEDIATE | Gate fails | Remediation tasks emitted |
| REMEDIATE | PHASE_GATE | Remediation complete | Rerun gate |
| LEARNING | COMPLETE | Patterns captured | Historian returned |
| ESCALATE | PLANNING | User provides guidance | User responded |

### Dynamic Expansion Transitions

| Trigger | Transition | Approval |
|---------|-----------|----------|
| Backlog remaining after planned phases | Append phase N+1 | Not required |
| Lane collision or critical-path overload | Append wave M+1 | Not required |
| Scope change from user | Replan from current phase | Required |

### Invalid Transitions

| Attempted | Error Behavior |
|-----------|----------------|
| EXECUTION without PLANNING | Supervisor re-enters PLANNING |
| MILESTONE_GATE without fan-in | Deferred until all lanes complete |
| PHASE_GATE without all milestones | Deferred until milestone gates pass |
| LEARNING without all phases | Deferred until final phase gate passes |

## Invocation Contract

### Input

```
/sage <project-description>
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project-description` | free-text | yes | What to build. Include tech stack, features, scope. |

If omitted, the supervisor prompts interactively.

### Effective Input Examples

```
# Compact profile (small scope)
/sage "CLI task tracker in Rust with SQLite persistence"

# Standard profile (multi-component)
/sage "REST API with Python/FastAPI, PostgreSQL, JWT auth, CRUD for users and posts"

# Full profile (enterprise)
/sage "Insurance policy administration system with underwriting engine, claims processing, regulatory compliance, multi-state support"
```

### Output

| Artifact | Location | Format |
|----------|----------|--------|
| Source code | Lane branches (`codex/p{P}/w{W}/lane-{CONCERN}`) | Language-specific |
| Gate reports | Conversation context | Markdown |
| Phase plan | Conversation context | Markdown/JSON |
| Learned patterns | Project context | JSON |
| Decision records | Project context | Markdown (ADR-lite) |
| Progress tracking | Project context | Markdown |

## Agent Capability Matrix

### Supervisor (implicit — runs in main context)

| Capability | Details |
|------------|---------|
| Role | Orchestrator — scope detection, planning, deployment, fan-in, decisions |
| Tools | All (Task, TeamCreate, Read, Write, Edit, Bash, etc.) |
| Context | Full conversation history |
| Persistence | Maintains state across all phases |

### sage-analyzer

| Field | Value |
|-------|-------|
| Role | Pre-phase codebase/requirements analysis + profile recommendation |
| Tools | `Read`, `Grep`, `Glob`, `Bash` |
| Model | Inherited (prefer sonnet for speed) |
| Permissions | `dontAsk` (read-only) |
| Writes files | Never |
| Branch | None (read-only) |
| Input | Project description + path to source documents |
| Output | Structured analysis report with scope profile recommendation |

### sage-builder

| Field | Value |
|-------|-------|
| Role | Unified lane builder — adapts to any lane/phase combination |
| Tools | `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob` |
| Model | Inherited |
| Permissions | Default |
| Writes files | Yes — scoped to assigned lane files only |
| Branch | `codex/p{PHASE}/w{WAVE}/lane-{CONCERN}` |
| Input | Phase/wave ID, lane assignment, file list, dependencies, done criteria |
| Output | Committed branch with lane deliverables |
| Constraints | Must NOT modify files outside assigned lane |
| Replaces | `sage-foundation`, `sage-implementer`, `sage-polisher` |

### sage-validator

| Field | Value |
|-------|-------|
| Role | Tiered quality gate enforcement |
| Tools | `Read`, `Bash`, `Grep`, `Glob` |
| Model | Inherited |
| Permissions | `dontAsk` (read-only + running checks) |
| Writes files | Never |
| Branch | None (read-only) |
| Input | Gate type, phase/milestone IDs, expected files, plan artifact |
| Output | Structured gate report with confidence score and decision |

### sage-historian

| Field | Value |
|-------|-------|
| Role | Learning capture, decision documentation, progress tracking |
| Tools | `Read`, `Write`, `Edit`, `Grep`, `Glob` |
| Model | `haiku` (lightweight, cost-efficient) |
| Permissions | Default |
| Writes files | Yes — progress docs, pattern records, decision logs |
| Branch | None (writes to project context, not source code) |
| Input | Phase/milestone results, gate scores, issues encountered |
| Output | Updated PROGRESS.md, learned_patterns.json, decision records |

## Scope Profile Contract

### Profile Selection

| Profile | Files | Phases | Waves/Phase | Milestones/Phase | Tasks/Milestone |
|---------|-------|--------|-------------|------------------|-----------------|
| Compact | < 10 | 1–3 | 1–3 | 2 | 5–8 |
| Standard | 10–50 | 3–6 | 3–5 | 3–4 | 8–12 |
| Full | 50+ | 7–12+ | 5–10+ | 4 | 15 |

### Gate Policy by Profile

| Gate | Compact | Standard | Full |
|------|---------|----------|------|
| Unit (milestone) | Yes | Yes | Yes |
| Integration (milestone) | If multi-component | Yes | Yes |
| Phase-End E2E | No | Yes | Yes |
| Rolling Inter-Phase | No | No | Yes |
| Rolling Cumulative E2E | No | No | Yes |
| Script validation | No | No | Yes |

### Adaptation Rules

| Size | Gate Behavior | Lane Behavior |
|------|---------------|---------------|
| Compact | Unit + optional integration | 1–2 lanes per wave, minimal parallelism |
| Standard | Full milestone gates + phase E2E | 2–4 lanes per wave, moderate parallelism |
| Full | All gates + rolling + scripts | All 4 lanes per wave, max parallelism |

### Self-Deactivation

SAGE should NOT be used for:
- Single-file changes or bug fixes
- Documentation-only changes
- Tasks with explicit line-by-line instructions

## Quality Gate Contract

### Confidence Score Formula

```
score = (0.20 * file_completeness)
      + (0.15 * lint_cleanliness)
      + (0.20 * type_safety)
      + (0.25 * test_passage)
      + (0.20 * integration_health)
```

### Decision Thresholds

| Score | Decision | Supervisor Action |
|-------|----------|-------------------|
| 90–100 | PASS (excellent) | Merge, proceed |
| 85–89 | PASS (good) | Merge, proceed |
| 70–84 | CONDITIONAL | Merge, document issues |
| 50–69 | RETRY | Re-deploy failing lanes (max 3) |
| 0–49 | ESCALATE | Present to user, await guidance |

### Retry Contract

| Property | Value |
|----------|-------|
| Max retries per lane per wave | 3 |
| Max wave-level retries | 2 |
| Retry scope | Only failing lanes, not entire wave |
| Retry strategy | Clarify instructions based on specific failure |
| Escalation trigger | Retries exhausted OR confidence < 50 |

## Fan-Out/Fan-In Contract

### Lane Types

| Lane | Responsibility | File Scope |
|------|---------------|------------|
| `contract_updates` | Schema, types, API contracts | `*.schema.*`, `types.*`, `*.d.ts` |
| `logic_updates` | Business logic, services | `src/**/*.{rs,py,ts}` (non-test) |
| `validation_and_tests` | Tests, fixtures, mocks | `tests/**/*`, `*.test.*` |
| `integration_and_references` | Wiring, docs, configs | `*.yaml`, `*.toml`, `docs/**` |

### Branch Contract

| Property | Value |
|----------|-------|
| Naming | `codex/p{PHASE}/w{WAVE}/lane-{CONCERN}` |
| Isolation | Each lane on its own branch |
| Merge cascade | Lane → Wave → Milestone → Phase → Main |
| Merge order | contract → logic → tests → integration |
| Conflict resolution | Auto for formatting, escalate for logic |
| File locking | File-level, until fan-in or 2-hour timeout |

### Parallelization Rules

| Rule | Enforcement |
|------|-------------|
| No two lanes modify same file in same wave | Pre-assigned file ownership |
| Hard dependencies block deployment | Dependent lanes wait |
| Soft dependencies use placeholders | Lanes proceed with mocks |
| Contract lane first when others depend on it | Wave ordering |

## Reference File Index

| File | Size | Loaded During | Content |
|------|------|---------------|---------|
| `skills/sage/SKILL.md` | ~450 lines | `/sage` invocation | Core orchestration protocol |
| `references/wave-orchestration.md` | ~220 lines | Phase 2 | Phase/wave/milestone/task model |
| `references/agent-coordination.md` | ~180 lines | Phase 3 | Fan-out/fan-in protocol |
| `references/quality-gates.md` | ~200 lines | Phase 3-4 | Tiered gate policy |
| `references/architecture-patterns.md` | ~330 lines | Phase 1-2 | Design patterns |
| `references/learning-system.md` | ~190 lines | Phase 5 | Pattern capture |
| `references/examples/domain-insurance.md` | ~205 lines | Phase 1 (if relevant) | Domain reference |

## Validation Scripts

| Script | Purpose | Profile |
|--------|---------|---------|
| `scripts/validate_generated_plan_contract.py` | Structural contract compliance | Full only |
| `scripts/validate_agent_native_wrappers.sh` | Document format validation | Full only |
| `scripts/validate_repo_redesign_contract.sh` | Repo structure validation | Full only |

## Composition Patterns

### SAGE + Domain Knowledge

```
# Load domain knowledge before invoking
Read domain reference → /sage "Build {domain-specific} system"
```

SAGE checks `skills/sage/references/examples/` for domain-specific references
and loads them during Phase 1 if relevant.

### SAGE + Existing Codebase

```
cd existing-project
/sage "Add user authentication with OAuth2 and role-based access"
```

sage-analyzer reads the existing codebase, and plan generation builds on top of
what exists rather than from scratch.

### SAGE + Manual Intervention

At any point, the user can:
- Modify the plan before approval
- Stop execution and redirect agents
- Skip phases/milestones if work is already done
- Override confidence thresholds
- Change scope profile mid-project

### SAGE + Other Skills

SAGE sub-agents can invoke other installed skills:
- `/commit` for standardized commit messages
- `/review-pr` for automated PR review
- Custom project skills for domain-specific validation

## Limitations

- SAGE generates source code and configuration — it does not execute servers
- Sub-agents communicate through the supervisor, not directly with each other
- Branch merging requires the supervisor or user to resolve non-trivial conflicts
- Quality gate scoring depends on configured linter, type checker, and test runner
- Learning system is per-project; cross-project sharing requires manual transfer
- Maximum parallelization depends on Claude Code plan and rate limits
- Full profile validation scripts require `rg` (ripgrep) to be installed
