from __future__ import annotations

from typing import Any


def validate(stage: str, output: dict[str, Any], case: dict[str, Any]) -> tuple[bool, list[str], str | None]:
    if output.get("status") == "blocked_due_to_upstream_failure":
        return True, [], None
    if stage == "normalize":
        if output.get("case_id") != case["case_id"]:
            return False, ["normalized case_id does not match source case"], "CONTRACT_FAILURE"
        if output.get("normalized") is not True:
            return False, ["normalized flag missing"], "CONTRACT_FAILURE"
    elif stage == "classify":
        if output.get("issue_type") != case["issue_type"]:
            return False, ["issue type differs from frozen expected type"], "CLASSIFICATION_FAILURE"
    elif stage == "select_evidence":
        if output.get("evidence_id") != case["evidence_id"]:
            return False, ["evidence does not match frozen case evidence"], "EVIDENCE_FAILURE"
    elif stage == "recommend":
        if output.get("action") != "route_to_reviewer":
            return False, ["recommendation bypasses required human authority"], "POLICY_AUTHORITY_FAILURE"
    elif stage == "generate_final_brief":
        if output.get("issue_type") != case["issue_type"]:
            return False, ["brief reports the wrong issue type"], "FINAL_SYNTHESIS_FAILURE"
        if output.get("human_review_required") is not True:
            return False, ["brief omits required human-review boundary"], "FINAL_SYNTHESIS_FAILURE"
    return True, [], None
