import pytest

from cost_quality_router.models import CheckResult, VerifierConfig
from cost_quality_router.verifier import V001_VERIFIER_SEMANTICS, validate_check_semantic_conformance, verify_runbook


CONFIG = VerifierConfig(allowed_steps=frozenset({"assess", "contain", "review"}),
                        required_steps=frozenset({"assess", "review"}), forbidden_steps=frozenset({"auto_resolve"}),
                        required_human_authority=True, supplied_policy_ids=frozenset({"POL-1", "POL-2"}),
                        required_policy_citations=frozenset({"POL-1"}), ordering_constraints=(("assess", "review"),))
VALID = {"steps": ["assess", "contain", "review"], "requires_human_authority": True, "policy_citations": ["POL-1"]}


def checks(candidate):
    return {item.name: item for item in verify_runbook("case-1", candidate, CONFIG).checks}


def test_valid_unique_fixture_passes():
    evaluation = verify_runbook("case-1", VALID, CONFIG)
    assert evaluation.case_pass and not evaluation.hard_gate_failed


def test_schema_fabricated_forbidden_authority_and_policy_hard_gates():
    assert not verify_runbook("case-1", {"steps": ["assess"]}, CONFIG).checks[0].passed
    assert not checks({**VALID, "steps": ["assess", "invent", "review"]})["allowed_steps"].passed
    assert not checks({**VALID, "steps": ["assess", "auto_resolve", "review"]})["forbidden_steps_absent"].passed
    assert not checks({**VALID, "requires_human_authority": False})["human_authority"].passed
    assert not checks({**VALID, "policy_citations": ["POL-X"]})["known_policy_citations"].passed


def test_missing_quality_requirements_and_order_fail():
    assert not checks({**VALID, "steps": ["contain"]})["required_steps"].passed
    assert not checks({**VALID, "policy_citations": ["POL-2"]})["required_citations"].passed
    assert not checks({**VALID, "steps": ["review", "assess"]})["ordering_constraints"].passed


def test_duplicates_are_rejected_and_cannot_game_ordering_or_padding():
    repaired_order = checks({**VALID, "steps": ["review", "assess", "review"]})
    padded = checks({**VALID, "steps": ["assess", "assess", "contain", "review", "review"]})
    assert not repaired_order["duplicate_steps_absent"].passed and not repaired_order["ordering_constraints"].passed
    assert not padded["duplicate_steps_absent"].passed


def test_current_verifier_behavior_conforms_to_frozen_semantic_specification():
    result = checks({**VALID, "requires_human_authority": False, "steps": ["assess", "assess", "review"]})
    assert result["human_authority"].hard_gate is V001_VERIFIER_SEMANTICS.human_authority_exact_match_hard_gate
    assert result["duplicate_steps_absent"].hard_gate is V001_VERIFIER_SEMANTICS.duplicate_steps_rejected
    assert result["ordering_constraints"].hard_gate is V001_VERIFIER_SEMANTICS.check("ordering_constraints").hard_gate


def test_all_nine_frozen_check_rules_drive_failure_and_hard_gate_designation():
    candidates = {"schema_valid": {"steps": ["assess"]}, "allowed_steps": {**VALID, "steps": ["assess", "invent", "review"]}, "forbidden_steps_absent": {**VALID, "steps": ["assess", "auto_resolve", "review"]}, "duplicate_steps_absent": {**VALID, "steps": ["assess", "assess", "review"]}, "human_authority": {**VALID, "requires_human_authority": False}, "known_policy_citations": {**VALID, "policy_citations": ["POL-X"]}, "required_steps": {**VALID, "steps": ["assess"]}, "required_citations": {**VALID, "policy_citations": ["POL-2"]}, "ordering_constraints": {**VALID, "steps": ["review", "assess"]}}
    for semantic in V001_VERIFIER_SEMANTICS.checks:
        emitted = checks(candidates[semantic.check_name])[semantic.check_name]
        assert not emitted.passed and emitted.hard_gate is semantic.hard_gate


def test_runtime_conformance_rejects_every_gate_demotion_or_promotion():
    for semantic in V001_VERIFIER_SEMANTICS.checks:
        mismatched = [CheckResult(name=check.check_name, passed=True, hard_gate=(not check.hard_gate if check.check_name == semantic.check_name else check.hard_gate), detail="fixture") for check in V001_VERIFIER_SEMANTICS.checks]
        with pytest.raises(ValueError, match="hard-gate"):
            validate_check_semantic_conformance(mismatched, V001_VERIFIER_SEMANTICS)
