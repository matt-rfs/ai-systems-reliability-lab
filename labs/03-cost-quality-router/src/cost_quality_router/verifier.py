from __future__ import annotations

from pydantic import ValidationError

from .models import CaseEvaluation, CheckResult, RunbookPlan, VerifierConfig


def verify_runbook(case_id: str, candidate: object, config: VerifierConfig) -> CaseEvaluation:
    try:
        plan = RunbookPlan.model_validate(candidate)
    except ValidationError as error:
        return CaseEvaluation(case_id=case_id, checks=[CheckResult(
            name="schema_valid", passed=False, hard_gate=True, detail=str(error)
        )])

    duplicates = len(set(plan.steps)) != len(plan.steps)
    positions = {step: index for index, step in enumerate(plan.steps)}
    checks = [
        CheckResult(name="schema_valid", passed=True, hard_gate=True, detail="plan matches the structured contract"),
        CheckResult(name="allowed_steps", passed=set(plan.steps).issubset(config.allowed_steps), hard_gate=True,
                    detail="all emitted steps must be in the frozen vocabulary"),
        CheckResult(name="forbidden_steps_absent", passed=not bool(set(plan.steps) & config.forbidden_steps), hard_gate=True,
                    detail="forbidden steps must be absent"),
        CheckResult(name="duplicate_steps_absent", passed=not duplicates, hard_gate=True,
                    detail="duplicate runbook steps are not allowed in V001"),
        CheckResult(name="human_authority", passed=plan.requires_human_authority == config.required_human_authority, hard_gate=True,
                    detail="human authority must exactly match frozen policy"),
        CheckResult(name="known_policy_citations", passed=set(plan.policy_citations).issubset(config.supplied_policy_ids), hard_gate=True,
                    detail="all citations must exist in supplied policy facts"),
        CheckResult(name="required_steps", passed=config.required_steps.issubset(plan.steps), hard_gate=False,
                    detail="all required steps must be present"),
        CheckResult(name="required_citations", passed=config.required_policy_citations.issubset(plan.policy_citations), hard_gate=False,
                    detail="all required citations must be present"),
        CheckResult(name="ordering_constraints", passed=not duplicates and all(
            before in positions and after in positions and positions[before] < positions[after]
            for before, after in config.ordering_constraints
        ), hard_gate=False, detail="frozen step dependencies must be satisfied"),
    ]
    return CaseEvaluation(case_id=case_id, checks=checks)
