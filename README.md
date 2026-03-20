# SAGE System

**Supervisor Agent-Generated Engineering** — a Claude Code plugin that orchestrates
phased parallel software development using fan-out/fan-in lanes, tiered quality gates,
and dynamic planning contracts.

## What is SAGE?

SAGE is a multi-agent orchestration system for building software systematically.
Instead of writing code file-by-file, SAGE decomposes projects into phases, waves,
and milestones — then deploys specialized agents in parallel to build them.

- **Scope-adaptive planning** — Compact (< 10 files), Standard (10-50), or Full (50+)
- **Fan-out/fan-in execution** — parallel lanes for contracts, logic, tests, and integration
- **Tiered quality gates** — unit, integration, phase-E2E, and rolling cumulative checks
- **Continuous learning** — captures patterns and decisions for future projects

## Installation

### From GitHub

```bash
/plugin install gh:Luiz-Frias/sage-system
```

### Local development

```bash
claude --plugin-dir /path/to/sage-system
```

## Usage

```
/sage <project-description>
```

SAGE will analyze your codebase, recommend a scope profile, generate a phased plan,
and execute it with parallel agent lanes — pausing for your approval at key checkpoints.

## Architecture

### Plugin Components

```
.claude-plugin/
  plugin.json           # Plugin metadata

skills/sage/
  SKILL.md              # Supervisor orchestration protocol
  references/           # Loaded on-demand during execution
    wave-orchestration.md
    agent-coordination.md
    quality-gates.md
    architecture-patterns.md
    learning-system.md
  scripts/              # Validation scripts for Full profile
    validate_generated_plan_contract.py
    validate_agent_native_wrappers.sh
    validate_repo_redesign_contract.sh

agents/
  sage-analyzer.md      # Read-only codebase analysis + scope recommendation
  sage-builder.md       # Per-lane fan-out builder (branch-isolated)
  sage-validator.md     # Tiered gate enforcement
  sage-historian.md     # Pattern capture + decision documentation
```

### Execution Model

```
              SAGE Supervisor (/sage skill)
                      |
         Phase 1: Analysis (sage-analyzer)
                      |
         Phase 2: Plan Generation
                      |
         Phase 3: Execution Loop
            |                   |
      Fan-out (waves)     Fan-in (merge)
      sage-builder x N    sage-validator
            |                   |
         Phase 4: Gate Validation
                      |
         Phase 5: Learning (sage-historian)
                      |
         Phase 6: Completion
```

### Legacy Reference Directories

These directories predate the plugin architecture but are still used as optional
context when present in a target project:

| Directory | Purpose |
|-----------|---------|
| `core/` | Engine specs, communication protocol, agent registry |
| `domains/` | Domain-specific reference (e.g., insurance) |
| `languages/` | Language-specific patterns, guardrails, templates |
| `source_documents/` | Project requirements, roadmaps, architecture docs |
| `wave_contexts/` | Phase/wave execution state and templates |

## License

Dual-licensed under [MIT](LICENSE-MIT) and [Apache-2.0](LICENSE-APACHE) at your option.

Copyright (c) 2025-2026 Luiz Frias

## Contributing

Contributions welcome under the same dual license. Fork, branch, and submit a PR.

## Contact

- **GitHub Issues** for bugs and feature requests
- **Email:** contact.me@luizfrias.com
