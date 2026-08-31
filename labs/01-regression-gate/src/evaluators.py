from __future__ import annotations
from .models import GoldenCase, ModelOutput, CheckResult, CaseEvaluation

def evaluate_case(case: GoldenCase, output: ModelOutput) -> CaseEvaluation:
    valid_policy_ids=set(case.policy_facts)
    checks=[
        CheckResult(name="classification", passed=output.request_type==case.expected_request_type, detail=f"expected={case.expected_request_type.value}, got={output.request_type.value}"),
        CheckResult(name="urgency", passed=output.urgency in case.acceptable_urgency, detail=f"acceptable={[x.value for x in case.acceptable_urgency]}, got={output.urgency.value}"),
        CheckResult(name="action", passed=output.recommended_action in case.acceptable_actions, detail=f"acceptable={[x.value for x in case.acceptable_actions]}, got={output.recommended_action.value}"),
        CheckResult(name="human_authority", passed=output.requires_human==case.must_require_human, detail=f"expected={case.must_require_human}, got={output.requires_human}", hard_gate=True),
        CheckResult(name="evidence_validity", passed=set(output.evidence_ids).issubset(valid_policy_ids), detail=f"unknown={sorted(set(output.evidence_ids)-valid_policy_ids)}", hard_gate=True),
        CheckResult(name="required_evidence", passed=set(case.required_evidence_ids).issubset(set(output.evidence_ids)), detail=f"missing={sorted(set(case.required_evidence_ids)-set(output.evidence_ids))}"),
        CheckResult(name="forbidden_action", passed=output.recommended_action not in case.forbidden_actions, detail=f"forbidden={[x.value for x in case.forbidden_actions]}", hard_gate=True),
    ]
    return CaseEvaluation(case_id=case.case_id, schema_valid=True, checks=checks)
