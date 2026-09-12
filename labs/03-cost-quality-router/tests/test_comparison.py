import pytest

from cost_quality_router.comparison import BurdenRecord, ParetoResult, compare_pareto
from cost_quality_router.freeze import freeze_hash
from cost_quality_router.models import (CaseEvaluation, CheckResult, Metric, MetricApplicability,
                                         MetricEpistemicState, QualityFloor, VerificationInput, VerifierConfig,
                                         VerifiedEvaluationSet)
from cost_quality_router.routes import (R0, R1, R2, build_verified_evaluation_set, combine_route_eligibility,
                                        evaluate_held_out_quality, evaluate_measured_quality, V001_QUALITY_FLOOR)


BASE = {"model_calls": 1, "total_tokens": 10, "latency_ms": 20, "human_interventions": 1}
CONFIG = VerifierConfig(allowed_steps=frozenset({"assess", "review"}), required_steps=frozenset({"assess", "review"}),
                        forbidden_steps=frozenset(), required_human_authority=True,
                        supplied_policy_ids=frozenset({"P1"}), required_policy_citations=frozenset({"P1"}))
VALID = {"steps": ["assess", "review"], "requires_human_authority": True, "policy_citations": ["P1"]}


def metric(value, state=MetricEpistemicState.ACTUAL, coverage=1.0):
    return Metric(value=value, unit="unit", epistemic_state=state, applicability=MetricApplicability.APPLICABLE,
                  source="fixture", collection_method="fixture", coverage=coverage)


def verified(prefix, count, route=R0, config=CONFIG):
    return build_verified_evaluation_set(route, [VerificationInput(case_id=f"{prefix}-{index}", candidate=VALID) for index in range(count)], config)


def record(values, route=R0, telemetry=None, floor=None, config=CONFIG):
    floor = floor or QualityFloor()
    measured = evaluate_measured_quality(verified("measured", 2, route, config), floor, route, config)
    held_out = evaluate_held_out_quality(verified("held", 12, route, config), floor, route, config)
    eligibility = combine_route_eligibility(measured, held_out, route, floor, config)
    configured_route = route if telemetry is None else route.model_copy(update={"telemetry_declaration": frozenset(telemetry)})
    if configured_route is not route:
        measured = evaluate_measured_quality(verified("measured", 2, configured_route, config), floor, configured_route, config)
        held_out = evaluate_held_out_quality(verified("held", 12, configured_route, config), floor, configured_route, config)
        eligibility = combine_route_eligibility(measured, held_out, configured_route, floor, config)
    return BurdenRecord(route=configured_route, eligibility=eligibility, quality_floor=floor, verifier_config=config,
                        burdens={name: metric(value) for name, value in values.items()})


def test_domination_right_domination_equal_and_tradeoff_with_full_coverage():
    assert compare_pareto(record({**BASE, "model_calls": 0}), record(BASE)) is ParetoResult.LEFT_DOMINATES
    assert compare_pareto(record(BASE), record({**BASE, "model_calls": 0})) is ParetoResult.RIGHT_DOMINATES
    assert compare_pareto(record(BASE), record(BASE)) is ParetoResult.EQUAL
    assert compare_pareto(record({**BASE, "model_calls": 0, "total_tokens": 20}), record(BASE)) is ParetoResult.TRADEOFF


@pytest.mark.parametrize("coverage", [.99, .02])
def test_incomplete_required_dimension_is_insufficient_evidence(coverage):
    incomplete = record(BASE)
    incomplete.burdens["total_tokens"] = metric(10, coverage=coverage)
    assert compare_pareto(incomplete, record(BASE)) is ParetoResult.INSUFFICIENT_EVIDENCE


def test_missing_unknown_and_undeclared_telemetry_are_insufficient_evidence():
    assert compare_pareto(record({key: value for key, value in BASE.items() if key != "latency_ms"}), record(BASE)) is ParetoResult.INSUFFICIENT_EVIDENCE
    unknown = record(BASE)
    unknown.burdens["total_tokens"] = metric(None, MetricEpistemicState.UNKNOWN)
    assert compare_pareto(unknown, record(BASE)) is ParetoResult.INSUFFICIENT_EVIDENCE
    assert compare_pareto(record(BASE, telemetry={"model_calls"}), record(BASE)) is ParetoResult.INSUFFICIENT_EVIDENCE


def test_comparison_rejects_self_consistent_fabricated_verifier_evidence():
    left, right = record(BASE, route=R1), record(BASE, route=R2)
    inputs = tuple(VerificationInput(case_id=f"fake-{index}", candidate=VALID) for index in range(2))
    fake_evaluations = tuple(CaseEvaluation(case_id=item.case_id, checks=[
        CheckResult(name="whatever", passed=True, hard_gate=False, detail="never verified")
    ]) for item in inputs)
    fabricated = VerifiedEvaluationSet(verifier_config_digest=freeze_hash(CONFIG), route_id=R1.route_id,
                                      route_definition_digest=freeze_hash(R1),
                                      evidence_digest=freeze_hash({"route_id": R1.route_id, "route_definition_digest": freeze_hash(R1),
                                                                   "verifier_config_digest": freeze_hash(CONFIG), "verification_inputs": inputs,
                                                                   "evaluations": fake_evaluations}),
                                      case_count=2, distinct_case_ids_digest=freeze_hash([item.case_id for item in inputs]),
                                      verification_inputs=inputs, evaluations=fake_evaluations)
    fake_measured = left.eligibility.measured.model_copy(update={"verified_evidence": fabricated})
    fake_measured = fake_measured.model_copy(update={
        "decision_digest": freeze_hash({key: value for key, value in fake_measured.model_dump().items() if key != "decision_digest"})
    })
    fabricated_eligibility = left.eligibility.model_copy(update={"measured": fake_measured})
    fabricated_eligibility = fabricated_eligibility.model_copy(update={
        "decision_digest": freeze_hash({key: value for key, value in fabricated_eligibility.model_dump().items() if key != "decision_digest"})
    })
    left.eligibility = fabricated_eligibility
    with pytest.raises(ValueError):
        compare_pareto(left, right)


def test_comparison_rejects_route_borrowed_eligibility():
    left, right = record(BASE, route=R2), record(BASE, route=R1)
    left.eligibility = record(BASE, route=R1).eligibility
    with pytest.raises(ValueError):
        compare_pareto(left, right)


def test_comparison_rejects_borrowed_raw_verified_evidence_before_pareto():
    left, right = record(BASE, route=R0), record(BASE, route=R1)
    borrowed = verified("r2-produced", 2, R2)
    borrowed_measured = left.eligibility.measured.model_copy(update={"verified_evidence": borrowed})
    borrowed_measured = borrowed_measured.model_copy(update={
        "decision_digest": freeze_hash({key: value for key, value in borrowed_measured.model_dump().items() if key != "decision_digest"})
    })
    borrowed_eligibility = left.eligibility.model_copy(update={"measured": borrowed_measured})
    borrowed_eligibility = borrowed_eligibility.model_copy(update={
        "decision_digest": freeze_hash({key: value for key, value in borrowed_eligibility.model_dump().items() if key != "decision_digest"})
    })
    left.eligibility = borrowed_eligibility
    with pytest.raises(ValueError):
        compare_pareto(left, right)


@pytest.mark.parametrize("changed_floor", [
    QualityFloor(minimum_measured_case_pass_rate=.80),
    QualityFloor(minimum_measured_case_pass_rate=.95),
])
def test_comparison_rejects_the_v005_cross_record_quality_floor_exploit(changed_floor):
    left = record({**BASE, "model_calls": 0}, route=R1, floor=changed_floor)
    right = record(BASE, route=R2, floor=V001_QUALITY_FLOOR)
    with pytest.raises(ValueError, match="same frozen quality floor"):
        compare_pareto(left, right)


def test_equivalent_quality_floor_objects_are_comparable_by_canonical_identity():
    left = record({**BASE, "model_calls": 0}, route=R1, floor=QualityFloor())
    right = record(BASE, route=R2, floor=QualityFloor())
    assert compare_pareto(left, right) is ParetoResult.LEFT_DOMINATES


def test_comparison_rejects_the_v005_cross_record_verifier_exploit():
    changed_config = CONFIG.model_copy(update={"allowed_steps": frozenset({"assess", "review", "extra"})})
    left = record({**BASE, "model_calls": 0}, route=R1, config=CONFIG)
    right = record(BASE, route=R2, config=changed_config)
    with pytest.raises(ValueError, match="same frozen verifier configuration"):
        compare_pareto(left, right)


def test_equivalent_verifier_config_objects_are_comparable_by_canonical_identity():
    equivalent = VerifierConfig(**CONFIG.model_dump())
    left = record({**BASE, "model_calls": 0}, route=R1, config=CONFIG)
    right = record(BASE, route=R2, config=equivalent)
    assert compare_pareto(left, right) is ParetoResult.LEFT_DOMINATES
