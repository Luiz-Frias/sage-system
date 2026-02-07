#!/usr/bin/env python3
"""Validate SAGE generated implementation plan contract.

Input format: JSON object with top-level key "phases".
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PHASE_MIN = 7
WAVE_MIN = 5
MILESTONE_EXACT = 4
TASK_EXACT = 15


def _err(errors: list[str], message: str) -> None:
    errors.append(message)


def _extract_index(value: str, marker: str) -> int | None:
    # Supports IDs like P01-M3-T12, M3, T12.
    m = re.search(rf"{re.escape(marker)}(\d+)", value)
    if not m:
        return None
    return int(m.group(1))


def validate(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    phases = plan.get("phases")
    if not isinstance(phases, list):
        _err(errors, "Missing required array: phases")
        return errors

    if len(phases) < PHASE_MIN:
        _err(errors, f"phase_count={len(phases)} < {PHASE_MIN}")

    for phase_idx, phase in enumerate(phases, start=1):
        pid = phase.get("phase_id", f"phase[{phase_idx}]")

        waves = phase.get("waves")
        if not isinstance(waves, list):
            _err(errors, f"{pid}: missing waves[]")
        elif len(waves) < WAVE_MIN:
            _err(errors, f"{pid}: wave_count={len(waves)} < {WAVE_MIN}")

        milestones = phase.get("milestones")
        if not isinstance(milestones, list):
            _err(errors, f"{pid}: missing milestones[]")
            continue

        if len(milestones) != MILESTONE_EXACT:
            _err(
                errors,
                f"{pid}: milestone_count={len(milestones)} != {MILESTONE_EXACT}",
            )

        prev_m_index = 0
        for milestone in milestones:
            mid = milestone.get("milestone_id", f"{pid}:milestone")

            m_index = _extract_index(str(mid), "M")
            if m_index is None:
                _err(errors, f"{pid}: {mid}: missing milestone sequence marker")
            elif m_index <= prev_m_index:
                _err(errors, f"{pid}: {mid}: milestone sequence is not strict")
            else:
                prev_m_index = m_index

            tasks = milestone.get("tasks")
            if not isinstance(tasks, list):
                _err(errors, f"{pid}: {mid}: missing tasks[]")
                continue

            if len(tasks) != TASK_EXACT:
                _err(
                    errors,
                    f"{pid}: {mid}: task_count={len(tasks)} != {TASK_EXACT}",
                )

            prev_t_index = 0
            for task in tasks:
                tid = str(task.get("task_id", ""))
                t_index = _extract_index(tid, "T")
                if t_index is None:
                    _err(errors, f"{pid}: {mid}: task missing sequence marker: {tid}")
                elif t_index <= prev_t_index:
                    _err(errors, f"{pid}: {mid}: task sequence is not strict")
                else:
                    prev_t_index = t_index

                if "done_criteria" not in task:
                    _err(errors, f"{pid}: {mid}: {tid}: missing done_criteria")

            if "unit_gate" not in milestone:
                _err(errors, f"{pid}: {mid}: missing unit_gate")
            if "integration_gate" not in milestone:
                _err(errors, f"{pid}: {mid}: missing integration_gate")

        phase_gates = phase.get("phase_gates", {})
        if not isinstance(phase_gates, dict):
            _err(errors, f"{pid}: phase_gates must be an object")
            continue

        if "phase_end_e2e" not in phase_gates:
            _err(errors, f"{pid}: missing phase_gates.phase_end_e2e")

        if phase_idx > 1:
            if "rolling_inter_phase_integration" not in phase_gates:
                _err(errors, f"{pid}: missing rolling_inter_phase_integration")
            if "rolling_cumulative_e2e" not in phase_gates:
                _err(errors, f"{pid}: missing rolling_cumulative_e2e")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_generated_plan_contract.py <plan.json>")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"error: file not found: {path}")
        return 2

    try:
        plan = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"error: invalid json: {exc}")
        return 2

    errors = validate(plan)
    if errors:
        print("contract validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
