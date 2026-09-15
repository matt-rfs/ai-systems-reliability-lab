"""Bounded executor for the frozen Lab 03 V001 eligibility canary.

This module deliberately knows only how to execute the six CANARY records.  It
does not select routes, assess measured quality, or modify any frozen surface.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from .cases import RouteInput, Split, build_case_collection, project_route_input, verifier_config_for_case
from .freeze import freeze_hash
from .routes import R0, R1, R2
from .verifier import verify_runbook


LAB_ROOT = Path(__file__).resolve().parents[2]
CANARY_PACKET_PATH = LAB_ROOT / "config" / "eligibility-canary-v001.json"
FREEZE_A_PATH = LAB_ROOT / "config" / "freeze-a-v001.json"
DEFAULT_MODEL = "qwen2.5:1.5b"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"


def _metric(value, state, *, unit, applicability="APPLICABLE", source, collection_method, coverage=1.0):
    return {"value": value, "unit": unit,
            "epistemic_state": state, "applicability": applicability, "source": source,
            "collection_method": collection_method, "coverage": coverage}


def _token_metric(state, *, source):
    return {"value": None, "unit": "tokens", "epistemic_state": state,
            "applicability": "APPLICABLE", "source": source,
            "collection_method": "runtime telemetry", "coverage": 1.0}


def build_r0_candidate(route_input: RouteInput) -> dict[str, object]:
    """Construct a plan from the shared, route-visible request and policy facts only."""
    policy_ids = {fact.policy_id for fact in route_input.policy_facts}
    request = route_input.request
    value_match = re.search(r"action value (\d+) units", request)
    action_value = int(value_match.group(1)) if value_match else 0
    threshold_match = next((re.search(r"threshold is (\d+) units", fact.policy_text)
                            for fact in route_input.policy_facts
                            if fact.policy_id == "POL-APPROVAL-THRESHOLD"), None)
    threshold = int(threshold_match.group(1)) if threshold_match else None
    requires_authority = threshold is not None and action_value > threshold

    steps = ["assess_request", "validate_inputs", "review_policy", "collect_evidence"]
    if threshold is not None:
        steps.append("confirm_threshold")
    if requires_authority:
        steps.append("request_human_approval")
    if "status EXCEPTION" in request:
        steps.append("escalate_exception")
    else:
        steps.append("prepare_action")
    steps.append("record_decision")
    if "POL-NOTIFY" in policy_ids:
        steps.append("notify_stakeholder")
    if "POL-CLOSE" in policy_ids:
        steps.append("close_request")
    return {"steps": steps, "requires_human_authority": requires_authority,
            "policy_citations": sorted(policy_ids)}


def probe_ollama() -> tuple[bool, str]:
    """Return availability only; never starts, changes, or repairs the runtime."""
    try:
        with urlopen(OLLAMA_TAGS_URL, timeout=2) as response:
            payload = json.load(response)
    except (OSError, URLError, json.JSONDecodeError) as error:
        return False, f"local Ollama runtime unavailable: {error}"
    available = {model.get("name") for model in payload.get("models", [])}
    if DEFAULT_MODEL not in available:
        return False, f"local Ollama runtime reachable but frozen model {DEFAULT_MODEL} is unavailable"
    return True, "local Ollama runtime and frozen model available"


def _r0_record(case):
    started = time.perf_counter()
    candidate = build_r0_candidate(project_route_input(case))
    evaluation = verify_runbook(case.case_id, candidate, verifier_config_for_case(case))
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    return {"case_id": case.case_id, "route_id": R0.route_id, "route_definition_digest": freeze_hash(R0),
            "candidate_output": candidate, "verifier_result": evaluation.model_dump(mode="json"),
            "case_pass": evaluation.case_pass, "hard_gate_failures": [check.name for check in evaluation.checks if check.hard_gate and not check.passed],
            "execution_status": "COMPLETED", "runtime": "Python local deterministic executor", "provider": "local",
            "model": None, "burden": {"call_count": _metric(0, "ACTUAL", unit="count", source="R0 execution trace", collection_method="call accounting"),
                                       "latency": _metric(latency_ms, "ACTUAL", unit="ms", source="R0 execution trace", collection_method="wall-clock timing"),
                                       "token_usage": {"value": None, "unit": "tokens", "epistemic_state": "UNPRICED", "applicability": "NOT_APPLICABLE", "source": "R0 has no model call", "collection_method": "not applicable", "coverage": 1.0},
                                       "api_service_cost": {"value": 0.0, "unit": "USD", "epistemic_state": "ACTUAL", "applicability": "APPLICABLE", "source": "local deterministic execution", "collection_method": "execution authority", "coverage": 1.0},
                                       "human_intervention": _metric(0, "ACTUAL", unit="count", source="R0 execution trace", collection_method="human-intervention log")}}


def _unavailable_record(case, route, reason):
    return {"case_id": case.case_id, "route_id": route.route_id, "route_definition_digest": freeze_hash(route),
            "candidate_output": None, "verifier_result": None, "case_pass": None, "hard_gate_failures": [],
            "execution_status": "RUNTIME_UNUSABLE", "runtime": "Ollama local runtime", "provider": "local",
            "model": DEFAULT_MODEL, "runtime_failure": reason,
            "burden": {"call_count": _metric(0, "ACTUAL", unit="count", source="failed runtime preflight", collection_method="call accounting"),
                       "latency": {"value": None, "unit": "ms", "epistemic_state": "UNKNOWN", "applicability": "APPLICABLE", "source": "no inference call completed", "collection_method": "runtime telemetry", "coverage": 1.0},
                       "token_usage": _token_metric("UNKNOWN", source="no inference call completed"),
                       "api_service_cost": {"value": 0.0, "unit": "USD", "epistemic_state": "ACTUAL", "applicability": "APPLICABLE", "source": "failed local runtime preflight", "collection_method": "execution authority", "coverage": 1.0},
                       "human_intervention": _metric(0, "ACTUAL", unit="count", source="canary execution log", collection_method="human-intervention log")}}


def execute_canary(output_dir: Path) -> Path:
    packet = json.loads(CANARY_PACKET_PATH.read_text())
    manifest = json.loads(FREEZE_A_PATH.read_text())
    if not packet["excluded_from_measured_statistics"] or not packet["cannot_change_freeze_a"]:
        raise ValueError("canary packet authority flags are not intact")
    cases = tuple(case for case in build_case_collection() if case.split is Split.CANARY)
    if [case.case_id for case in cases] != packet["case_ids"] or len(cases) != 6:
        raise ValueError("canary cases do not match the frozen packet")
    output_dir.mkdir(parents=True, exist_ok=False)
    r0_records = [_r0_record(case) for case in cases]
    runtime_available, runtime_note = probe_ollama()
    if runtime_available:
        raise RuntimeError("model execution adapter is not implemented; do not execute model routes without explicit authority")
    r1_records = [_unavailable_record(case, R1, runtime_note) for case in cases]
    r2_records = [_unavailable_record(case, R2, runtime_note) for case in cases]
    payload = {"artifact_version": "L03-CANARY-RESULT-V001", "executed_at": datetime.now(timezone.utc).isoformat(),
               "scope": "eligibility canary only; excluded from measured statistics", "freeze_a_digest": manifest["freeze_a_digest"],
               "canary_packet_version": packet["packet_version"], "canary_packet_digest": freeze_hash(packet),
               "case_ids": packet["case_ids"], "route_order": packet["route_ids"],
               "runtime_preflight": {"available": runtime_available, "note": runtime_note, "runtime": "Ollama local runtime", "model": DEFAULT_MODEL},
               "route_dispositions": {"R0": "ELIGIBLE" if all(record["case_pass"] for record in r0_records) else "INELIGIBLE",
                                      "R1": "RUNTIME_UNUSABLE", "R2": "RUNTIME_UNUSABLE"},
               "capability_gradient": "INCONCLUSIVE", "no_router_needed": "INCONCLUSIVE",
               "records": {"R0": r0_records, "R1": r1_records, "R2": r2_records},
               "execution_trace_binding": "Each record binds case ID, frozen route digest, candidate or runtime failure, verifier output when generated, Freeze A digest, and canary packet digest."}
    path = output_dir / "canary_execution.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(execute_canary(args.output_dir))


if __name__ == "__main__":
    main()
