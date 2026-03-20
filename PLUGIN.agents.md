# PLUGIN.agents.md — SAGE Orchestration System

> Agent quick-path: use this doc for the compact invocation flow, agent deployment
> patterns, gate decisions, and recovery playbook.
>
> For the full orchestration protocol (all cardinality rules, reference file contents,
> plan structure schemas): see `skills/sage/SKILL.md`.
>
> For the formal state machine and spec: see `AGENTS.spec.md`.

## Happy Path (Scope → Ship)

```
/sage <project-description>
        │
   Phase 0: Scope Detection ──── Compact | Standard | Full
        │
   Phase 1: Analysis ──────────── sage-analyzer (read-only)
        │                          output: structured report + profile recommendation
        │                          ⏸ WAIT for user approval
        │
   Phase 2: Plan Generation ───── supervisor builds phase/wave/milestone/task plan
        │                          Full profile: validate with scripts/validate_generated_plan_contract.py
        │                          ⏸ WAIT for user approval
        │
   Phase 3: Execution Loop ────── per phase, per wave:
        │   Fan-out ──── sage-builder × N lanes (branch-isolated)
        │   Fan-in ───── merge lane branches
        │   Gate ─────── sage-validator (milestone or phase boundary)
        │   Loop ─────── next wave/milestone/phase
        │
   Phase 5: Learning ──────────── sage-historian (pattern capture)
        │
   Phase 6: Completion ────────── final E2E, summary, branch cleanup
```

Two user-approval checkpoints: after analysis (Phase 1) and after plan generation (Phase 2).
Everything after Phase 2 is autonomous unless a gate escalates.

## Self-Deactivation

Do NOT use the SAGE protocol for:
- Single-file changes or bug fixes within one module
- Documentation-only changes
- Tasks with explicit line-by-line instructions from the user

If invoked for a trivial task, inform the user and execute directly.

## Scope Detection (Phase 0)

Determine profile from the project description before deploying any agents.

| Profile | Phases | Waves/Phase | Milestones/Phase | Tasks/Milestone | Trigger |
|---------|--------|-------------|------------------|-----------------|---------|
| Compact | 1–3 | 1–3 | 2 | 5–8 | < 10 files, single concern |
| Standard | 3–6 | 3–5 | 3–4 | 8–12 | 10–50 files, multi-component |
| Full | 7–12+ | 5–10+ | 4 | 15 | 50+ files, enterprise, regulatory |

When in doubt, prefer Standard over Compact.

## Agent Deployment

### Invocation Table

| Agent | When | Task() Call | Expected Output | If It Fails |
|-------|------|-------------|-----------------|-------------|
| sage-analyzer | Phase 1 | `subagent_type: "sage:sage-analyzer"`, model: `sonnet`, prompt: `"Analyze: {description}. Recommend scope profile."` | Structured analysis report with profile recommendation | Review prompt clarity; ensure `source_documents/` is readable if present |
| sage-builder | Phase 3 (per lane) | `subagent_type: "sage:sage-builder"`, mode: `bypassPermissions`, prompt: `"Phase {P}, Wave {W}, Lane: {LANE}. Files: {file_list}."` | Completed lane deliverables on branch `codex/p{P}/w{W}/lane-{LANE}` | Check lane assignment scope; verify no file conflicts across lanes |
| sage-validator | Phase 3–4 (per gate) | `subagent_type: "sage:sage-validator"`, mode: `bypassPermissions`, prompt: `"Gate: {gate_type}. Phase: {P}, Milestone: {M}."` | Gate report with numeric score and pass/fail per check | If score is 0 or validator crashes, check that expected files exist |
| sage-historian | Phase 5 | `subagent_type: "sage:sage-historian"`, model: `haiku`, prompt: `"Capture learnings for completed phases. Profile: {PROFILE}."` | Learnings doc with patterns, decisions, gate history | Non-blocking — log the failure and proceed to completion |

### Lane Types

Each wave fans out into up to 4 concern-separated lanes:

| Lane | Builds | Branch |
|------|--------|--------|
| `contract_updates` | Schema, types, API contracts, interfaces | `codex/p{P}/w{W}/lane-contract_updates` |
| `logic_updates` | Business logic, services, algorithms | `codex/p{P}/w{W}/lane-logic_updates` |
| `validation_and_tests` | Unit tests, integration tests, fixtures | `codex/p{P}/w{W}/lane-validation_and_tests` |
| `integration_and_references` | Cross-component wiring, configs, docs | `codex/p{P}/w{W}/lane-integration_and_references` |

Not all lanes are needed in every wave — assign based on wave focus.

## Gate Decision Loop

After each milestone or phase boundary, the validator returns a score.

| Score | Decision | Action |
|-------|----------|--------|
| >= 85 | PASS | Proceed to next milestone/wave/phase |
| 70–84 | CONDITIONAL | Proceed with issues documented in gate report |
| 50–69 | RETRY | Re-deploy failing lanes (max 3 retries per lane) |
| < 50 | ESCALATE | Stop. Present gate report to user. Await guidance |

### Gate Types by Boundary

| Boundary | Gate | Applies To |
|----------|------|------------|
| Milestone complete | `unit` | All profiles |
| Post-init milestone | `integration` | Standard + Full |
| Phase complete | `phase_e2e` | Standard + Full |
| Phase > P01 complete | `rolling_integration` + `rolling_cumulative_e2e` | Full only |

## Recovery Playbook

| Failure | Diagnosis | Recovery |
|---------|-----------|----------|
| Analyzer returns no profile recommendation | Prompt too vague or no codebase context | Clarify project description; check if `source_documents/` exists |
| Plan validation fails (Full profile) | Cardinality violation (wrong milestone/task counts) | Regenerate the violating plan section; rerun `validate_generated_plan_contract.py` |
| Builder lane produces no output | File assignment was empty or ambiguous | Check plan artifact for the lane's assigned files; reassign and redeploy |
| Fan-in merge conflict (textual) | Two lanes edited overlapping files | Git merge resolution; if logic conflict, escalate to user |
| Gate score is 0 | Expected files missing entirely | Verify builder lanes completed; check branch existence |
| Gate keeps failing after 3 retries | Structural issue in plan or dependencies | Escalate to user with gate report + retry history |
| Historian fails | Non-critical | Log the error; proceed to Phase 6 completion |
| Rolling gate blocks next phase | Cross-phase integration regression | Emit remediation tasks; fix; rerun rolling gate before proceeding |

## ID Scheme

All IDs are deterministic and hierarchical:

```
P01              ← Phase
P01-W01          ← Wave within phase
P01-M1           ← Milestone within phase (1-indexed)
P01-M1-T01       ← Task within milestone (01-indexed)
```

## Full Profile Validation Scripts

For Full profile only — run these via sage-validator or directly:

| Script | Validates |
|--------|-----------|
| `scripts/validate_generated_plan_contract.py <plan.json>` | Plan structure, cardinality, ID scheme |
| `scripts/validate_agent_native_wrappers.sh` | Agent frontmatter and objective alignment |
| `scripts/validate_repo_redesign_contract.sh` | Output repo structure compliance |

## Reference Loading Schedule

Load references on-demand, not upfront. Each reference is in `skills/sage/references/`.

| Reference | Load When | Why |
|-----------|-----------|-----|
| `wave-orchestration.md` | Phase 2 (planning) | Cardinality rules, fan-out lane model |
| `agent-coordination.md` | Phase 3 (execution) | Fan-out/fan-in protocol, branch isolation |
| `quality-gates.md` | Phase 3–4 (gates) | Gate taxonomy, decision matrix |
| `architecture-patterns.md` | Phase 1–2 | API layering, microservices patterns |
| `learning-system.md` | Phase 5 | Pattern recording protocol |
| `examples/domain-insurance.md` | Phase 1 (if relevant) | Insurance domain mapping |

## Escalate to Full Contract

Use `skills/sage/SKILL.md` when you need:
- Full plan structure schema and cardinality rules per profile
- Dependency category definitions (hard/soft/runtime)
- Dynamic expansion rules
- Legacy reference integration details

Use `AGENTS.spec.md` when you need:
- Formal state machine with all transitions
- Agent capability matrix
- Spec-level constraints and invariants
