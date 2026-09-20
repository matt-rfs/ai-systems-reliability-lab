from pathlib import Path
import sys

import pytest

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB / "src"))

from human_authority_gate.fixtures import FROZEN_FIXTURES
from human_authority_gate.gate import EVALUATION_TIME, canonical_json, evaluate_gate, payload_fingerprint, synthetic_execute, validate_action
from human_authority_gate.runner import run_frozen_experiment


def test_frozen_fingerprint_values_match_contract():
    expected = ("dcf1d00dac5e2fe5c6bba41ebbb210d92ef706ee8f9de48944346359fd9a86be",
                "9ca7c15786821eb9753748183e3bff2f07823e64bb377cf0c7ab9c32a086a9aa",
                "0777c11da436b56fa0ffdffd4fa77ec3a6f4e4331e4fc4af79c4c16bb0372b52",
                "4853682a488f87d2454ce363da7f2add8ddd23b3e9de5134544740383d1a510a",
                "ef020ad83cebf38ce4eebcbf79e9fa2762ca9e79c0916176d612e58e5943ac04")
    values = (payload_fingerprint(FROZEN_FIXTURES[0]["proposed_action"]["action_payload"]),
              payload_fingerprint(FROZEN_FIXTURES[1]["proposed_action"]["action_payload"]),
              payload_fingerprint(FROZEN_FIXTURES[2]["proposed_action"]["action_payload"]),
              "4853682a488f87d2454ce363da7f2add8ddd23b3e9de5134544740383d1a510a",
              payload_fingerprint(FROZEN_FIXTURES[11]["proposed_action"]["action_payload"]))
    assert values == expected
    assert canonical_json({"to": "alex@example.invalid", "body": "x", "subject": "s"}) == '{"body":"x","subject":"s","to":"alex@example.invalid"}'


@pytest.mark.parametrize("fixture", FROZEN_FIXTURES, ids=lambda item: item["fixture_id"])
def test_every_frozen_fixture_matches_all_expected_outputs(fixture):
    result = evaluate_gate(fixture["proposed_action"], fixture["authorization"], evaluation_time=EVALUATION_TIME)
    assert result.authority_requirement == fixture["expected_authority_requirement"]
    assert result.disposition == fixture["expected_disposition"]
    assert result.reason_code == fixture["expected_reason_code"]
    assert synthetic_execute(result, fixture["proposed_action"]) == fixture["expected_executor_state"]


def test_malformed_multiple_authorizations_fail_closed():
    fixture = FROZEN_FIXTURES[1]
    result = evaluate_gate(fixture["proposed_action"], [fixture["authorization"], fixture["authorization"]])
    assert (result.disposition, result.reason_code, synthetic_execute(result, fixture["proposed_action"])) == ("BLOCK", "AUTHORIZATION_MALFORMED", "ACTION_BLOCKED")


def test_action_schema_rejects_extra_fields_and_non_string_payload_values():
    action = {"action_type": "SEND_EXTERNAL_MESSAGE", "action_scope": "scope", "action_payload": {"body": "x", "subject": "s", "to": 1}}
    with pytest.raises(ValueError):
        validate_action(action)
    action["action_payload"] = {"body": "x", "subject": "s", "to": "a", "extra": "no"}
    with pytest.raises(ValueError):
        validate_action(action)


def test_frozen_experiment_has_zero_mismatches_and_no_falsification():
    report = run_frozen_experiment()
    assert report["fixture_count"] == 12
    assert report["final_disposition"] == "PASS"
    for key in ("unauthorized_execution_count", "authority_requirement_mismatch_count", "disposition_mismatch_count", "reason_code_mismatch_count", "executor_state_mismatch_count"):
        assert report[key] == 0
    assert report["safety_falsified"] is False and report["correctness_falsified"] is False
