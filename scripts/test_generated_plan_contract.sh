#!/usr/bin/env bash
set -euo pipefail

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

python3 - <<'PY' > "$tmp_file"
import json

phases = []
for p in range(1, 8):
    waves = [
        {
            "wave_id": f"P{p:02d}-W{w:02d}",
            "focus": "contract-test",
            "fan_out_lanes": ["a", "b", "c", "d"],
            "fan_in_gate": {"id": f"gate-p{p:02d}w{w:02d}"},
        }
        for w in range(1, 6)
    ]

    milestones = []
    for m in range(1, 5):
        tasks = [
            {
                "task_id": f"P{p:02d}-M{m}-T{t:02d}",
                "description": "task",
                "owner": "agent",
                "dependencies": [],
                "done_criteria": ["done"],
            }
            for t in range(1, 16)
        ]
        milestones.append(
            {
                "milestone_id": f"P{p:02d}-M{m}",
                "objective": "test",
                "tasks": tasks,
                "unit_gate": {"required": True},
                "integration_gate": {"required": True},
            }
        )

    phase_gates = {"phase_end_e2e": {"required": True}}
    if p > 1:
        phase_gates["rolling_inter_phase_integration"] = {"required": True}
        phase_gates["rolling_cumulative_e2e"] = {"required": True}

    phases.append(
        {
            "phase_id": f"P{p:02d}",
            "phase_name": "contract-test",
            "objective": "test",
            "waves": waves,
            "milestones": milestones,
            "phase_gates": phase_gates,
        }
    )

print(json.dumps({"phases": phases}))
PY

scripts/validate_generated_plan_contract.py "$tmp_file"
