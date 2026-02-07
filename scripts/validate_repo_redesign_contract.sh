#!/usr/bin/env bash
set -euo pipefail

# Check required contract fields in core files.
rg -n "planning_output_contract:" core/engine/wave-orchestrator.yaml >/dev/null
rg -n "phase_count:" core/engine/wave-orchestrator.yaml >/dev/null
rg -n "supervisor_plan_policy:" core/config/sage.config.yaml >/dev/null
rg -n "generate_implementation_plan:" core/interfaces/IAgent.yaml >/dev/null
rg -n "phases >= 7|phase_count >= 7|phase_count" MASTER_INSTRUCTION_SET.md >/dev/null

# Check stale references removed from master instructions.
if rg -n "parallelization-rules\.yaml|learning-system\.yaml|language-capabilities\.json|tool-registry\.json|\.sage/" MASTER_INSTRUCTION_SET.md >/dev/null; then
  echo "error: stale references still present in MASTER_INSTRUCTION_SET.md"
  exit 1
fi

# Check key templates include cardinality constraints.
rg -n "phases >= 7|waves_per_phase >= 5|milestones_per_phase = 4|tasks_per_milestone = 15" wave_contexts/current/WAVE_TEMPLATE.md >/dev/null

echo "repo redesign contract checks passed"
