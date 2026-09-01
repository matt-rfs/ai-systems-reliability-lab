from __future__ import annotations

import uuid
from typing import Any

from models import STAGES, StageTrace
from tracing import make_trace
from validators import validate


EVIDENCE_BY_TYPE = {"billing": "invoice-duplicate", "access": "access-log", "refund": "refund-ledger"}


def stage_output(stage: str, case: dict[str, Any], state: dict[str, Any], correction: bool) -> tuple[dict[str, Any], str]:
    injection = case.get("injection")
    if stage == "normalize":
        output = {"case_id": case["case_id"], "normalized": True, "scenario": case["scenario"]}
        if injection == "normalize_malformed": output = {"normalized": False}
        if injection == "normalize_missing_case": output.pop("case_id")
    elif stage == "classify":
        normalized = state["normalize"]
        if (normalized.get("status") == "blocked_due_to_upstream_failure" or normalized.get("normalized") is not True
                or not normalized.get("case_id")):
            return {"status": "blocked_due_to_upstream_failure", "blocked_by": "normalize"}, "blocked"
        output = {"issue_type": case["issue_type"], "normalized_case_id": normalized.get("case_id")}
        if injection == "classify_wrong_type": output["issue_type"] = "access" if case["issue_type"] != "access" else "billing"
        if injection == "classify_runtime_error": return {"error": "synthetic local runtime timeout"}, "execution_error"
    elif stage == "select_evidence":
        classification = state["classify"]
        if classification.get("status") == "blocked_due_to_upstream_failure" or "error" in classification:
            return {"status": "blocked_due_to_upstream_failure", "blocked_by": "classify"}, "blocked"
        output = {"evidence_id": EVIDENCE_BY_TYPE[classification["issue_type"]], "selected_for_issue_type": classification["issue_type"]}
        if injection == "evidence_missing" and not correction: output["evidence_id"] = None
        if injection == "evidence_wrong_source": output["evidence_id"] = "unrelated-record"
    elif stage == "recommend":
        evidence = state["select_evidence"]
        classification = state["classify"]
        if evidence.get("status") == "blocked_due_to_upstream_failure" or (
            evidence.get("evidence_id") != case["evidence_id"] and classification["issue_type"] == case["issue_type"]
        ):
            return {"status": "blocked_due_to_upstream_failure", "blocked_by": "select_evidence"}, "blocked"
        output = {"action": "route_to_reviewer", "evidence_id": evidence["evidence_id"], "issue_type": classification["issue_type"]}
        if classification["issue_type"] != case["issue_type"]:
            output["action"] = f"route_to_{classification['issue_type']}_review"
        if injection == "recommend_auto_action": output["action"] = "auto_resolve"
    else:
        recommendation = state["recommend"]
        if recommendation.get("status") == "blocked_due_to_upstream_failure":
            return {"status": "blocked_due_to_upstream_failure", "blocked_by": "recommend"}, "blocked"
        output = {"issue_type": recommendation["issue_type"], "human_review_required": recommendation["action"] == "route_to_reviewer", "brief": f"Synthetic brief for {recommendation['action']}."}
        if injection == "brief_omits_authority": output["human_review_required"] = False
        if injection == "brief_wrong_issue": output["issue_type"] = "access" if case["issue_type"] != "access" else "billing"
    return output, "completed"


def run_case(case: dict[str, Any], correction: bool = False, run_id: str | None = None) -> list[StageTrace]:
    run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
    traces: list[StageTrace] = []
    state: dict[str, Any] = {}
    root: StageTrace | None = None
    for index, stage in enumerate(STAGES, start=1):
        import time
        started = time.perf_counter()
        input_state = {name: state[name] for name in state}
        output, status = stage_output(stage, case, state, correction)
        if status == "execution_error":
            valid, errors, failure_type = False, [output["error"]], "EXECUTION_FAILURE"
        else:
            valid, errors, failure_type = validate(stage, output, case)
        propagated = root is not None and not valid and status != "blocked"
        if propagated:
            output = {**output, "propagated_from": root.stage}
            failure_type = "PROPAGATION_FAILURE"
        trace = make_trace(run_id, case["case_id"], stage, index, input_state, output, valid, errors, started, status, failure_type)
        trace.first_failure = root is None and not valid
        if trace.first_failure:
            root = trace
        traces.append(trace)
        state[stage] = output
    return traces
