import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB / "src"))

from forensic import localize
from models import StageTrace
from pipeline import run_case
from report import load_jsonl


CASES = {row["case_id"]: row for row in load_jsonl(LAB / "data/cases.jsonl")}


def traces(case_id, correction=False):
    return run_case(CASES[case_id], correction=correction, run_id=f"test-{case_id}")


def finding(case_id, correction=False):
    return localize(traces(case_id, correction))


def trace_for(case_id, stage):
    return next(trace for trace in traces(case_id) if trace.stage == stage)


def test_trace_integrity_ordering_and_input_state():
    run = traces("clean-01")
    assert len(run) == 5
    assert [trace.stage_index for trace in run] == [1, 2, 3, 4, 5]
    assert {trace.run_id for trace in run} == {"test-clean-01"}
    assert all(trace.input_hash and trace.input_reference for trace in run)
    assert all(trace.latency_ms >= 0 and trace.api_service_cost_usd == 0 for trace in run)
    assert run[1].input_state["normalize"]["scenario"] == CASES["clean-01"]["scenario"]
    assert run[2].input_state["classify"]["issue_type"] == CASES["clean-01"]["issue_type"]
    assert run[3].input_state["select_evidence"]["evidence_id"] == CASES["clean-01"]["evidence_id"]
    assert run[4].input_state["recommend"]["action"] == "route_to_reviewer"


def test_classification_defect_changes_downstream_outputs_and_is_propagated():
    run = traces("classify-01")
    assert trace_for("classify-01", "classify").validation_pass is False
    for stage in ("select_evidence", "recommend", "generate_final_brief"):
        trace = next(item for item in run if item.stage == stage)
        assert trace.validation_pass is False
        assert trace.failure_type == "PROPAGATION_FAILURE"
        assert trace.output["propagated_from"] == "classify"
    assert finding("classify-01").symptom_stages == ["select_evidence", "recommend", "generate_final_brief"]


def test_contained_evidence_failure_does_not_claim_propagation():
    run = traces("evidence-01")
    recommend = next(item for item in run if item.stage == "recommend")
    final = next(item for item in run if item.stage == "generate_final_brief")
    assert recommend.status == "blocked" and final.status == "blocked"
    assert "propagated_from" not in recommend.output and "propagated_from" not in final.output
    result = finding("evidence-01")
    assert result.propagation_detected is False and result.symptom_stages == [] and result.contained is True


def test_valid_downstream_stage_after_root_failure_is_not_propagated():
    """Sequence alone cannot turn a valid downstream result into a symptom."""
    base = {
        "run_id": "canned-independent-downstream", "case_id": "canned-01",
        "input_hash": "fixture-hash", "input_reference": "canned-reference",
        "provider": "local", "runtime": "Python deterministic fixture", "model": None,
        "latency_ms": 0.0, "input_tokens": None, "output_tokens": None,
        "api_service_cost_usd": 0.0,
    }
    trace_set = [
        StageTrace(**base, stage="normalize", stage_index=1, input_state={}, output={"normalized": True},
                   validation_pass=True, validation_errors=[]),
        StageTrace(**base, stage="classify", stage_index=2, input_state={"normalize": {"normalized": True}},
                   output={"issue_type": "wrong"}, validation_pass=False,
                   validation_errors=["issue type differs from expected"], failure_type="CLASSIFICATION_FAILURE"),
        StageTrace(**base, stage="select_evidence", stage_index=3,
                   input_state={"classify": {"issue_type": "wrong"}}, output={"evidence_id": "correct"},
                   validation_pass=True, validation_errors=[], status="completed"),
        StageTrace(**base, stage="recommend", stage_index=4, input_state={}, output={"action": "route_to_reviewer"},
                   validation_pass=True, validation_errors=[]),
        StageTrace(**base, stage="generate_final_brief", stage_index=5, input_state={},
                   output={"human_review_required": True}, validation_pass=True, validation_errors=[]),
    ]
    result = localize(trace_set)
    downstream = trace_set[2]
    assert downstream.status == "completed" and downstream.validation_pass is True
    assert "propagated_from" not in downstream.output
    assert result.first_failure_stage == "classify"
    assert result.failure_type == "CLASSIFICATION_FAILURE"
    assert result.propagation_detected is False
    assert downstream.stage not in result.symptom_stages


def test_normalization_and_execution_failures_are_contained():
    for case_id in ("normalize-01", "normalize-02", "execution-01"):
        result = finding(case_id)
        assert result.contained is True
        assert result.propagation_detected is False


def test_authority_failure_propagates_to_observed_final_brief():
    result = finding("authority-01")
    final = trace_for("authority-01", "generate_final_brief")
    assert (result.first_failure_stage, result.failure_type) == ("recommend", "POLICY_AUTHORITY_FAILURE")
    assert result.symptom_stages == ["generate_final_brief"]
    assert final.output["human_review_required"] is False and final.validation_pass is False


def test_final_synthesis_failure_has_no_downstream_symptom():
    result = finding("synthesis-01")
    assert result.first_failure_stage == "generate_final_brief"
    assert result.symptom_stages == [] and result.propagation_detected is False and result.contained is False


def test_clean_run_has_no_failure_or_propagation():
    result = finding("clean-02")
    assert result.clean_run is True and result.propagation_detected is False


def test_regression_fixture_fails_before_fix_and_passes_after_fix():
    before, after = finding("evidence-01"), finding("evidence-01", correction=True)
    assert (before.first_failure_stage, before.failure_type) == ("select_evidence", "EVIDENCE_FAILURE")
    assert before.contained is True and after.clean_run is True


def test_measured_artifacts_are_complete_and_causally_scoped():
    summary = json.loads((LAB / "results/measured_results.json").read_text())
    assert summary["trace_completeness"] == "70/70"
    assert summary["origin_vs_propagation_accuracy"] == "14/14"
    assert summary["propagation_case_count"] == 4
    assert summary["contained_case_count"] == 5
    assert summary["regression_fixture"]["verified"] is True
