import pytest

from cost_quality_router.freeze import freeze_hash
from cost_quality_router.models import (CaseEvaluation, CheckResult, QualityFloor, RouteDefinition,
                                         RouteEligibility, RouteExecutionAuthority, RouteType, VerificationInput, VerifierConfig,
                                         VerifiedEvaluationSet)
from cost_quality_router.routes import (R0, R1, R2, authorize_execution, build_verified_evaluation_set,
                                        combine_route_eligibility, economically_eligible, evaluate_held_out_quality,
                                        evaluate_measured_quality, verified_evidence_is_valid)


CONFIG = VerifierConfig(allowed_steps=frozenset({"assess", "review"}), required_steps=frozenset({"assess", "review"}),
                        forbidden_steps=frozenset(), required_human_authority=True,
                        supplied_policy_ids=frozenset({"P1"}), required_policy_citations=frozenset({"P1"}),
                        ordering_constraints=(("assess", "review"),))
VALID = {"steps": ["assess", "review"], "requires_human_authority": True, "policy_citations": ["P1"]}


def evidence(prefix, count, failing=0, hard_failure=False, config=CONFIG, route=R0):
    inputs = []
    for index in range(count):
        candidate = VALID if index >= failing else {**VALID, "steps": ["assess"]}
        if hard_failure and index == 0:
            candidate = {**VALID, "requires_human_authority": False}
        inputs.append(VerificationInput(case_id=f"{prefix}-{index}", candidate=candidate))
    return build_verified_evaluation_set(route, inputs, config)


def eligible_pair(route=R0, config=CONFIG, floor=QualityFloor()):
    measured_evidence = evidence("measured", 10, config=config, route=route)
    held_out_evidence = evidence("held", 12, failing=1, config=config, route=route)
    measured = evaluate_measured_quality(measured_evidence, floor, route, config)
    held_out = evaluate_held_out_quality(held_out_evidence, floor, route, config)
    return measured, held_out, combine_route_eligibility(measured, held_out, route, floor, config)


@pytest.mark.parametrize("route_id", ["R0", "another-deterministic-route"])
@pytest.mark.parametrize("forbidden", ["case_id", "expected_answer", "hidden_ground_truth", "verifier_result"])
def test_deterministic_routes_reject_forbidden_features_at_construction(route_id, forbidden):
    with pytest.raises(ValueError):
        RouteDefinition(route_id=route_id, route_version="v001", route_type=RouteType.DETERMINISTIC,
                        applicability_features=frozenset({forbidden}), telemetry_declaration=frozenset())


def test_route_definition_is_immutable_and_allowed_surface_works():
    assert R0.applicability_features == frozenset({"request_length", "required_step_count", "allowed_vocabulary_size"})
    with pytest.raises(Exception):
        R0.route_version = "v002"


@pytest.mark.parametrize(("passes", "count", "expected"), [(11, 11, False), (11, 12, True), (10, 12, False), (12, 12, True)])
def test_held_out_floor_enforces_exact_12_case_denominator(passes, count, expected):
    assessment = evaluate_held_out_quality(evidence("held", count, failing=count - passes), QualityFloor(), R0, CONFIG)
    assert assessment.passed is expected


def test_held_out_hard_gate_violation_and_duplicate_case_ids_fail_closed():
    assessment = evaluate_held_out_quality(evidence("held", 12, hard_failure=True), QualityFloor(), R0, CONFIG)
    assert not assessment.passed and assessment.hard_gate_violation_count == 1
    duplicated = [VerificationInput(case_id="same", candidate=VALID) for _ in range(12)]
    with pytest.raises(ValueError, match="distinct case IDs"):
        build_verified_evaluation_set(R0, duplicated, CONFIG)


def test_measured_and_held_out_are_conjunctive_at_economic_boundary():
    floor = QualityFloor()
    measured, held_out, complete = eligible_pair(floor=floor)
    assert economically_eligible(R0, complete, floor, CONFIG)
    measured_only = complete.model_copy(update={"held_out": held_out.model_copy(update={"passed": False})})
    held_out_only = complete.model_copy(update={"measured": measured.model_copy(update={"passed": False})})
    assert not economically_eligible(R0, measured_only, floor, CONFIG)
    assert not economically_eligible(R0, held_out_only, floor, CONFIG)


def test_measured_only_or_held_out_only_records_cannot_enter_economic_eligibility():
    floor = QualityFloor()
    _, _, complete = eligible_pair(floor=floor)
    payload = {field: getattr(complete, field) for field in RouteEligibility.model_fields}
    payload.pop("held_out")
    measured_only = RouteEligibility.model_construct(**payload)
    payload = {field: getattr(complete, field) for field in RouteEligibility.model_fields}
    payload.pop("measured")
    held_out_only = RouteEligibility.model_construct(**payload)
    assert not economically_eligible(R0, measured_only, floor, CONFIG)
    assert not economically_eligible(R0, held_out_only, floor, CONFIG)


def test_combining_assessments_requires_same_route_verifier_and_floor():
    floor = QualityFloor()
    measured, _, _ = eligible_pair(route=R0, floor=floor)
    held_out = evaluate_held_out_quality(evidence("held", 12, failing=1, route=R1), floor, R1, CONFIG)
    with pytest.raises(ValueError, match="same route"):
        combine_route_eligibility(measured, held_out, R0, floor, CONFIG)
    alternative = CONFIG.model_copy(update={"required_human_authority": False})
    held_out = evaluate_held_out_quality(evidence("other", 12, failing=1, config=alternative, route=R0), floor, R0, alternative)
    with pytest.raises(ValueError, match="same route"):
        combine_route_eligibility(measured, held_out, R0, floor, CONFIG)
    changed_floor = floor.model_copy(update={"minimum_measured_case_pass_rate": .95})
    held_out = evaluate_held_out_quality(evidence("floor", 12, failing=1, route=R0), changed_floor, R0, CONFIG)
    with pytest.raises(ValueError, match="same route"):
        combine_route_eligibility(measured, held_out, R0, floor, CONFIG)


def test_fabricated_case_evaluations_are_not_verified_evidence():
    inputs = tuple(VerificationInput(case_id=f"fabricated-{index}", candidate=VALID) for index in range(12))
    fabricated_evaluations = tuple(CaseEvaluation(case_id=item.case_id, checks=[
        CheckResult(name="whatever", passed=True, hard_gate=False, detail="never ran a verifier")
    ]) for item in inputs)
    fabricated = VerifiedEvaluationSet(verifier_config_digest=freeze_hash(CONFIG), route_id=R0.route_id,
                                      route_definition_digest=freeze_hash(R0),
                                      evidence_digest=freeze_hash({"route_id": R0.route_id, "route_definition_digest": freeze_hash(R0),
                                                                   "verifier_config_digest": freeze_hash(CONFIG), "verification_inputs": inputs,
                                                                   "evaluations": fabricated_evaluations}),
                                      case_count=12, distinct_case_ids_digest=freeze_hash([item.case_id for item in inputs]),
                                      verification_inputs=inputs, evaluations=fabricated_evaluations)
    assert not verified_evidence_is_valid(fabricated, R0, CONFIG)
    with pytest.raises(ValueError, match="route-bound, verifier-bound evidence"):
        evaluate_held_out_quality(fabricated, QualityFloor(), R0, CONFIG)


def test_route_identity_binding_rejects_borrowed_or_changed_route_proof():
    floor = QualityFloor()
    _, _, proof = eligible_pair(route=R1, floor=floor)
    assert not economically_eligible(R2, proof, floor, CONFIG)
    changed_r1 = R1.model_copy(update={"route_version": "v002"})
    assert not economically_eligible(changed_r1, proof, floor, CONFIG)
    assert economically_eligible(R1, proof, floor, CONFIG)


@pytest.mark.parametrize(("producer", "claimant"), [(R2, R0), (R1, R2)])
def test_raw_verified_evidence_cannot_be_reassessed_for_another_route(producer, claimant):
    raw_evidence = evidence("producer", 12, route=producer)
    with pytest.raises(ValueError, match="route-bound"):
        evaluate_held_out_quality(raw_evidence, QualityFloor(), claimant, CONFIG)


def test_raw_verified_evidence_rejects_materially_changed_same_route_definition():
    raw_evidence = evidence("producer", 12, route=R1)
    changed_r1 = R1.model_copy(update={"route_version": "v002"})
    with pytest.raises(ValueError, match="route-bound"):
        evaluate_held_out_quality(raw_evidence, QualityFloor(), changed_r1, CONFIG)
    assert evaluate_held_out_quality(raw_evidence, QualityFloor(), R1, CONFIG).passed


def test_measured_and_held_out_populations_must_be_separate_and_disjoint():
    floor = QualityFloor()
    same = evidence("same", 12, failing=1)
    measured = evaluate_measured_quality(same, floor, R0, CONFIG)
    held_out = evaluate_held_out_quality(same, floor, R0, CONFIG)
    with pytest.raises(ValueError, match="separate populations"):
        combine_route_eligibility(measured, held_out, R0, floor, CONFIG)
    copied = evidence("same", 12, failing=1)
    with pytest.raises(ValueError, match="separate populations"):
        combine_route_eligibility(measured, evaluate_held_out_quality(copied, floor, R0, CONFIG), R0, floor, CONFIG)
    overlapping = build_verified_evaluation_set(R0, [VerificationInput(case_id="same-0", candidate=VALID)] +
                                                [VerificationInput(case_id=f"other-{index}", candidate=VALID) for index in range(11)], CONFIG)
    with pytest.raises(ValueError, match="disjoint"):
        combine_route_eligibility(measured, evaluate_held_out_quality(overlapping, floor, R0, CONFIG), R0, floor, CONFIG)


def test_disjoint_measured_and_held_out_evidence_can_qualify():
    floor = QualityFloor()
    measured = evaluate_measured_quality(evidence("measured", 2), floor, R0, CONFIG)
    held_out = evaluate_held_out_quality(evidence("held", 12, failing=1), floor, R0, CONFIG)
    eligibility = combine_route_eligibility(measured, held_out, R0, floor, CONFIG)
    assert eligibility.eligible and economically_eligible(R0, eligibility, floor, CONFIG)


def test_execution_authority_is_immutable_and_identity_changes_with_configuration():
    authority = RouteExecutionAuthority()
    with pytest.raises(Exception):
        authority.allow_billable_routes = True
    changed_provider = authority.model_copy(update={"allowed_providers": frozenset({"local", "other"})})
    changed_billable = authority.model_copy(update={"allow_billable_routes": True})
    assert freeze_hash(authority) != freeze_hash(changed_provider)
    assert freeze_hash(authority) != freeze_hash(changed_billable)
    assert freeze_hash(changed_provider) != freeze_hash(changed_billable)


def test_nonlocal_or_billable_execution_is_rejected():
    authority = RouteExecutionAuthority()
    assert authorize_execution("local", False, authority)
    assert not authorize_execution("remote", False, authority)
    assert not authorize_execution("local", True, authority)
