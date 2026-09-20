"""Frozen fixture runner and compact deterministic result report."""
from __future__ import annotations

from .fixtures import FROZEN_FIXTURES
from .gate import evaluate_gate, synthetic_execute


def run_frozen_experiment() -> dict[str, object]:
    records = []
    for fixture in FROZEN_FIXTURES:
        result = evaluate_gate(fixture["proposed_action"], fixture["authorization"])
        executor_state = synthetic_execute(result, fixture["proposed_action"])
        actual = {**result.as_dict(), "executor_state": executor_state}
        expected = {"authority_requirement": fixture["expected_authority_requirement"],
                    "disposition": fixture["expected_disposition"], "reason_code": fixture["expected_reason_code"],
                    "executor_state": fixture["expected_executor_state"]}
        records.append({"fixture_id": fixture["fixture_id"], "expected": expected, "actual": actual,
                        "passed": actual == expected})
    mismatch_counts = {field: sum(item["actual"][field] != item["expected"][field] for item in records)
                       for field in ("authority_requirement", "disposition", "reason_code", "executor_state")}
    unauthorized = sum(item["expected"]["disposition"] == "BLOCK" and item["actual"]["executor_state"] == "ACTION_EXECUTED" for item in records)
    return {"experiment_id": "HUMAN_AUTHORITY_GATE_FREEZE_A_V001", "fixture_count": len(records), "records": records,
            "unauthorized_execution_count": unauthorized,
            "authority_requirement_mismatch_count": mismatch_counts["authority_requirement"],
            "disposition_mismatch_count": mismatch_counts["disposition"],
            "reason_code_mismatch_count": mismatch_counts["reason_code"],
            "executor_state_mismatch_count": mismatch_counts["executor_state"],
            "safety_falsified": unauthorized > 0,
            "correctness_falsified": any(mismatch_counts.values()),
            "final_disposition": "PASS" if not unauthorized and not any(mismatch_counts.values()) else "FALSIFIED"}
