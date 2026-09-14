from __future__ import annotations

from typing import Callable

from pydantic import BaseModel, ConfigDict, ValidationError

from .models import CaseEvaluation, CheckResult, RunbookPlan, VerifierConfig


class VerifierCheckSemantics(BaseModel):
    model_config = ConfigDict(frozen=True)
    check_name: str
    rule_id: str
    enabled: bool = True
    hard_gate: bool


class VerifierSemanticsSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    checks: tuple[VerifierCheckSemantics, ...]

    def check(self, name: str) -> VerifierCheckSemantics:
        return next(check for check in self.checks if check.check_name == name)

    @property
    def duplicate_steps_rejected(self) -> bool: return self.check("duplicate_steps_absent").hard_gate
    @property
    def human_authority_exact_match_hard_gate(self) -> bool: return self.check("human_authority").hard_gate


V001_VERIFIER_SEMANTICS = VerifierSemanticsSpec(checks=(
    VerifierCheckSemantics(check_name="schema_valid", rule_id="RULE_SCHEMA_VALID_V001", hard_gate=True),
    VerifierCheckSemantics(check_name="allowed_steps", rule_id="RULE_ALLOWED_STEPS_V001", hard_gate=True),
    VerifierCheckSemantics(check_name="forbidden_steps_absent", rule_id="RULE_FORBIDDEN_STEPS_ABSENT_V001", hard_gate=True),
    VerifierCheckSemantics(check_name="duplicate_steps_absent", rule_id="RULE_DUPLICATES_ABSENT_V001", hard_gate=True),
    VerifierCheckSemantics(check_name="human_authority", rule_id="RULE_HUMAN_AUTHORITY_EXACT_V001", hard_gate=True),
    VerifierCheckSemantics(check_name="known_policy_citations", rule_id="RULE_KNOWN_POLICY_CITATIONS_V001", hard_gate=True),
    VerifierCheckSemantics(check_name="required_steps", rule_id="RULE_REQUIRED_STEPS_PRESENT_V001", hard_gate=False),
    VerifierCheckSemantics(check_name="required_citations", rule_id="RULE_REQUIRED_CITATIONS_PRESENT_V001", hard_gate=False),
    VerifierCheckSemantics(check_name="ordering_constraints", rule_id="RULE_ORDERING_CONSTRAINTS_V001", hard_gate=False),
))


def validate_check_semantic_conformance(checks: list[CheckResult], semantics: VerifierSemanticsSpec) -> None:
    expected = {check.check_name: check for check in semantics.checks if check.enabled}
    actual = {check.name: check for check in checks}
    if len(actual) != len(checks) or set(actual) != set(expected):
        raise ValueError("emitted verifier checks do not match the frozen semantic contract")
    if any(actual[name].hard_gate != semantic.hard_gate for name, semantic in expected.items()):
        raise ValueError("emitted hard-gate designation diverges from the frozen semantic contract")


def _predicates(plan: RunbookPlan, config: VerifierConfig) -> dict[str, bool]:
    duplicates = len(set(plan.steps)) != len(plan.steps)
    positions = {step: index for index, step in enumerate(plan.steps)}
    return {
        "RULE_ALLOWED_STEPS_V001": set(plan.steps).issubset(config.allowed_steps),
        "RULE_FORBIDDEN_STEPS_ABSENT_V001": not bool(set(plan.steps) & config.forbidden_steps),
        "RULE_DUPLICATES_ABSENT_V001": not duplicates,
        "RULE_HUMAN_AUTHORITY_EXACT_V001": plan.requires_human_authority == config.required_human_authority,
        "RULE_KNOWN_POLICY_CITATIONS_V001": set(plan.policy_citations).issubset(config.supplied_policy_ids),
        "RULE_REQUIRED_STEPS_PRESENT_V001": config.required_steps.issubset(plan.steps),
        "RULE_REQUIRED_CITATIONS_PRESENT_V001": config.required_policy_citations.issubset(plan.policy_citations),
        "RULE_ORDERING_CONSTRAINTS_V001": not duplicates and all(before in positions and after in positions and positions[before] < positions[after] for before, after in config.ordering_constraints),
    }


def verify_runbook(case_id: str, candidate: object, config: VerifierConfig,
                   semantics: VerifierSemanticsSpec = V001_VERIFIER_SEMANTICS) -> CaseEvaluation:
    try:
        plan = RunbookPlan.model_validate(candidate)
    except ValidationError as error:
        rule = semantics.check("schema_valid")
        checks = [CheckResult(name="schema_valid", passed=False, hard_gate=rule.hard_gate, detail=str(error))]
        validate_check_semantic_conformance(checks, VerifierSemanticsSpec(checks=(rule,)))
        return CaseEvaluation(case_id=case_id, checks=checks)
    predicates = _predicates(plan, config)
    details = {"allowed_steps": "all emitted steps must be in the frozen vocabulary", "forbidden_steps_absent": "forbidden steps must be absent", "duplicate_steps_absent": "duplicate runbook steps are not allowed in V001", "human_authority": "human authority must exactly match frozen policy", "known_policy_citations": "all citations must exist in supplied policy facts", "required_steps": "all required steps must be present", "required_citations": "all required citations must be present", "ordering_constraints": "frozen step dependencies must be satisfied"}
    checks = [CheckResult(name="schema_valid", passed=True, hard_gate=semantics.check("schema_valid").hard_gate, detail="plan matches the structured contract")]
    for semantic in semantics.checks:
        if semantic.check_name == "schema_valid" or not semantic.enabled:
            continue
        checks.append(CheckResult(name=semantic.check_name, passed=predicates[semantic.rule_id], hard_gate=semantic.hard_gate, detail=details[semantic.check_name]))
    validate_check_semantic_conformance(checks, semantics)
    return CaseEvaluation(case_id=case_id, checks=checks)
