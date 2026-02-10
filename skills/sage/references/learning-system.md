# Learning System Reference

This document defines how the SAGE system captures, stores, and applies patterns
from successful and failed executions. Load this reference during pattern recording
and before plan generation (to check for applicable learnings).

## Pattern Recording

### When to Record

Capture patterns at these points:
- **After each milestone**: What worked, what didn't at the milestone level
- **After each phase**: Cross-milestone patterns and phase-level observations
- **After conflict resolution**: How was it resolved, could it have been prevented?
- **After retry/rollback**: What caused the failure, what fixed it?
- **After gate results**: What gates passed/failed and why
- **After project completion**: Cross-phase patterns and systemic observations

### Pattern Schema

```yaml
pattern:
  id: "{category}-{number}"        # e.g., "arch-001", "workflow-015"
  type: success | failure
  category: architecture | code | workflow | integration | testing | gate
  phase_id: "P{NN}"                # Phase where pattern was observed
  wave_id: "P{NN}-W{NN}"           # Wave where pattern was observed (optional)
  milestone_id: "P{NN}-M{N}"       # Milestone where pattern was observed (optional)
  description: "Concise description of what happened"
  context:
    project_type: "REST API | full-stack | CLI | library | ..."
    tech_stack: ["Python", "FastAPI", "PostgreSQL"]
    complexity: low | medium | high
    scope_profile: compact | standard | full
    team_size: {number of agents}
  impact: high | medium | low
  success_rate: 0.0 - 1.0           # Updated over time
  application_count: {number}        # How many times this was used
  details: "Specific details about execution"
  remedy: "For failures: what should be done differently"
  reuse_conditions: "When this pattern applies"
  last_updated: "ISO-8601"
```

### Success Pattern Examples

```yaml
- id: "workflow-001"
  type: success
  phase_id: "P01"
  description: "Parallel schema and API development with interface contracts"
  context: { project_type: "REST API", complexity: medium, scope_profile: standard }
  impact: high
  details: |
    When database schema and API routes are developed in parallel lanes,
    pre-defining shared type interfaces in the contract_updates lane
    prevents integration issues at fan-in.
  reuse_conditions: "Any CRUD-heavy API project with separate schema and API lanes"

- id: "arch-003"
  type: success
  phase_id: "P01"
  milestone_id: "P01-M1"
  description: "Centralized type definitions before any consumer development"
  context: { project_type: "full-stack", complexity: high, scope_profile: full }
  impact: high
  details: |
    Creating a shared types package/module in the contract_updates lane
    of the first wave eliminates 90% of integration type mismatches
    at milestone gates.
  reuse_conditions: "Any project with multiple consuming services"
```

### Failure Pattern Examples

```yaml
- id: "workflow-010"
  type: failure
  phase_id: "P02"
  wave_id: "P02-W01"
  description: "Frontend development without shared type definitions"
  context: { project_type: "full-stack", complexity: medium, scope_profile: standard }
  impact: high
  details: |
    Starting frontend logic_updates lane before contract_updates lane
    completes leads to widespread 'any' types and significant rework
    at fan-in.
  remedy: "Always complete contract_updates lane before deploying logic_updates consumers"

- id: "gate-002"
  type: failure
  phase_id: "P03"
  milestone_id: "P03-M2"
  description: "Integration gate failure due to stale contract references"
  context: { project_type: "microservices", complexity: high, scope_profile: full }
  impact: high
  details: |
    Phase 3 milestone 2 integration gate failed because services referenced
    Phase 1 contract versions instead of the updated Phase 2 contracts.
    Rolling gate would have caught this earlier.
  remedy: "Enforce contract version pinning and update checks in integration lanes"
```

## Pattern Application Protocol

### Before Plan Generation (Phase 2)

1. **Load relevant patterns**: Filter by project type, tech stack, and scope profile
2. **Check failure patterns first**: Ensure known pitfalls are avoided
3. **Apply success patterns**: Incorporate proven strategies into phase plan
4. **Adapt to context**: Patterns are guidelines, not rigid rules

### Before Each Phase

1. **Load phase-specific patterns**: Filter by phase position (early/middle/late)
2. **Check gate failure patterns**: Avoid known gate failure modes
3. **Apply lane coordination patterns**: Use proven fan-out/fan-in strategies

### Pattern Matching Criteria

When checking if a pattern applies:

| Factor | Weight | Method |
|--------|--------|--------|
| Project type match | 25% | Exact or similar project type |
| Tech stack overlap | 20% | At least 50% stack overlap |
| Scope profile match | 20% | Same profile or adjacent |
| Complexity match | 15% | Same or adjacent complexity level |
| Phase alignment | 10% | Same phase position (early/mid/late) |
| Historical success rate | 10% | > 0.7 success rate |

### Conflict Resolution Between Patterns

When patterns contradict each other:
1. Higher success rate wins
2. More recent pattern wins (if rates are similar)
3. Higher impact pattern wins (if recency is similar)
4. Same scope profile wins over cross-profile patterns
5. Escalate to human if still ambiguous

## Continuous Improvement Cycle

```
Plan Phase
  → Check applicable patterns
  → Incorporate learnings into lane assignments
  → Execute phase (fan-out/fan-in)
  → Validate at gates
  → Record new patterns (with phase/milestone/wave context)
  → Update existing pattern success rates
  → Feed back into next phase plan
```

### Learning Rate Configuration

| Category | Speed | Activation Threshold | Use Case |
|----------|-------|---------------------|----------|
| Critical failures | Fast | 1 occurrence | Security issues, data loss, gate failures |
| Gate patterns | Fast | 2 occurrences | Gate failure modes, remediation strategies |
| Code patterns | Moderate | 3 occurrences | Design patterns, conventions |
| Workflow patterns | Moderate | 3 occurrences | Lane coordination, fan-out strategies |
| Style preferences | Slow | 10 occurrences | Naming, formatting, structure |

### Pattern Lifecycle

```
Discovery → Validation → Adoption → Optimization → Deprecation

Discovery:    First observation (success_rate unknown)
Validation:   2-3 more observations confirm the pattern
Adoption:     Pattern actively applied in phase planning
Optimization: Pattern refined based on continued observation
Deprecation:  Pattern no longer applies (tech change, model evolution, etc.)
```

## Storage Format

Patterns are stored as a JSON file in the project's context:

```json
{
  "version": "1.0.0",
  "scope_profile": "standard",
  "last_updated": "2026-02-10T12:00:00Z",
  "successful_patterns": [
    {
      "id": "workflow-001",
      "phase_id": "P01",
      "milestone_id": "P01-M2",
      "description": "...",
      "success_rate": 0.92,
      "application_count": 12,
      "last_updated": "2026-02-10T12:00:00Z"
    }
  ],
  "failure_patterns": [
    {
      "id": "gate-002",
      "phase_id": "P03",
      "milestone_id": "P03-M2",
      "description": "...",
      "failure_rate": 0.78,
      "observation_count": 9,
      "remedy": "...",
      "last_updated": "2026-02-10T12:00:00Z"
    }
  ],
  "gate_history": [
    {
      "gate_type": "integration",
      "phase_id": "P02",
      "milestone_id": "P02-M3",
      "result": "CONDITIONAL",
      "score": 78,
      "issues": ["..."],
      "timestamp": "2026-02-10T12:00:00Z"
    }
  ]
}
```

## Cross-Project Learning

When patterns prove reliable across multiple projects:
1. Promote them to the SAGE plugin's core pattern library
2. Include them in agent default instructions
3. Increase their weight in pattern matching
4. Document them as best practices in reference files
