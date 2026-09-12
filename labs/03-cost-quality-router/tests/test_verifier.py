from cost_quality_router.models import VerifierConfig
from cost_quality_router.verifier import verify_runbook


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
