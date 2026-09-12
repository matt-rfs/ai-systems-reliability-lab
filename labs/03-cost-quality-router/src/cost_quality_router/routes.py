from __future__ import annotations

from .freeze import freeze_hash
from .models import (ALLOWED_DETERMINISTIC_FEATURES, BURDEN_DIMENSIONS, EvaluationScope, QualityAssessment,
                     QualityFloor, RouteDefinition, RouteEligibility, RouteExecutionAuthority, RouteType,
                     VerificationInput, VerifiedEvaluationSet, VerifierConfig)
from .verifier import verify_runbook


R0_ALLOWED_FEATURES = ALLOWED_DETERMINISTIC_FEATURES

R0 = RouteDefinition(route_id="R0", route_version="v001", route_type=RouteType.DETERMINISTIC,
                     applicability_features=R0_ALLOWED_FEATURES,
                     telemetry_declaration=frozenset(BURDEN_DIMENSIONS))
R1 = RouteDefinition(route_id="R1", route_version="v001", route_type=RouteType.SINGLE_PASS_MODEL,
                     applicability_features=frozenset({"request_length"}),
                     telemetry_declaration=frozenset(BURDEN_DIMENSIONS))
R2 = RouteDefinition(route_id="R2", route_version="v001", route_type=RouteType.DECOMPOSED_MODEL,
                     applicability_features=frozenset({"request_length"}),
                     telemetry_declaration=frozenset(BURDEN_DIMENSIONS))
V001_QUALITY_FLOOR = QualityFloor()


def validate_route_definition(route: RouteDefinition) -> None:
    RouteDefinition.model_validate(route)


def make_route_definition(**values: object) -> RouteDefinition:
    route = RouteDefinition(**values)
    validate_route_definition(route)
    return route


def _evidence_digest(route: RouteDefinition, inputs: tuple[VerificationInput, ...], evaluations: tuple,
                     config: VerifierConfig) -> str:
    return freeze_hash({"route_id": route.route_id, "route_definition_digest": freeze_hash(route),
                        "verifier_config_digest": freeze_hash(config), "verification_inputs": inputs,
                        "evaluations": evaluations})


def build_verified_evaluation_set(route: RouteDefinition, inputs: list[VerificationInput],
                                  config: VerifierConfig) -> VerifiedEvaluationSet:
    """Run the deterministic verifier and retain replayable inputs with its output."""
    if not inputs:
        raise ValueError("verified evidence requires at least one verifier input")
    case_ids = [item.case_id for item in inputs]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("verified evidence requires distinct case IDs")
    evaluations = tuple(verify_runbook(item.case_id, item.candidate, config) for item in inputs)
    return VerifiedEvaluationSet(
        verifier_config_digest=freeze_hash(config),
        route_id=route.route_id,
        route_definition_digest=freeze_hash(route),
        evidence_digest=_evidence_digest(route, tuple(inputs), evaluations, config),
        case_count=len(evaluations),
        distinct_case_ids_digest=freeze_hash(case_ids),
        verification_inputs=tuple(inputs),
        evaluations=evaluations,
    )


def verified_evidence_is_valid(evidence: VerifiedEvaluationSet, route: RouteDefinition,
                               config: VerifierConfig) -> bool:
    """Verify evidence provenance by replaying the frozen deterministic verifier."""
    inputs, evaluations = evidence.verification_inputs, evidence.evaluations
    case_ids = [item.case_id for item in inputs]
    if (evidence.verifier_config_digest != freeze_hash(config) or evidence.route_id != route.route_id
            or evidence.route_definition_digest != freeze_hash(route) or not inputs
            or len(inputs) != len(evaluations) or len(set(case_ids)) != len(case_ids)):
        return False
    replayed = tuple(verify_runbook(item.case_id, item.candidate, config) for item in inputs)
    return (tuple(item.case_id for item in evaluations) == tuple(case_ids)
            and replayed == evaluations
            and evidence.case_count == len(evaluations)
            and evidence.distinct_case_ids_digest == freeze_hash(case_ids)
            and evidence.evidence_digest == _evidence_digest(route, inputs, evaluations, config))


def _assessment(route: RouteDefinition, evidence: VerifiedEvaluationSet, floor: QualityFloor,
                config: VerifierConfig, scope: EvaluationScope) -> QualityAssessment:
    if not verified_evidence_is_valid(evidence, route, config):
        raise ValueError("eligibility requires route-bound, verifier-bound evidence replayable under the accepted config")
    evaluations = evidence.evaluations
    hard_failures = sum(evaluation.hard_gate_failed for evaluation in evaluations)
    passes = sum(evaluation.case_pass for evaluation in evaluations)
    rate = passes / len(evaluations)
    reasons: list[str] = []
    if hard_failures:
        reasons.append(f"{hard_failures} hard-gate violations")
    if scope is EvaluationScope.MEASURED and rate < floor.minimum_measured_case_pass_rate:
        reasons.append(f"measured case-pass rate {rate:.3f} below floor")
    if scope is EvaluationScope.HELD_OUT:
        if len(evaluations) != floor.held_out_case_count:
            reasons.append(f"held-out evaluated case count {len(evaluations)} does not equal {floor.held_out_case_count}")
        if passes < floor.held_out_minimum_passes:
            reasons.append(f"held-out passes {passes}/{len(evaluations)} below floor")
        if floor.held_out_zero_hard_gate_violations and hard_failures:
            reasons.append("held-out hard-gate violation")
    details = {
        "route_id": route.route_id,
        "route_definition_digest": freeze_hash(route),
        "quality_floor_digest": freeze_hash(floor),
        "verifier_config_digest": freeze_hash(config),
        "scope": scope,
        "verified_evidence": evidence,
        "evaluated_case_count": len(evaluations),
        "distinct_case_ids_digest": evidence.distinct_case_ids_digest,
        "pass_count": passes,
        "pass_rate": rate,
        "hard_gate_violation_count": hard_failures,
        "passed": not reasons,
        "reasons": tuple(reasons),
    }
    return QualityAssessment(**details, decision_digest=freeze_hash(details))


def evaluate_measured_quality(evidence: VerifiedEvaluationSet, floor: QualityFloor, route: RouteDefinition,
                              config: VerifierConfig) -> QualityAssessment:
    return _assessment(route, evidence, floor, config, EvaluationScope.MEASURED)


def evaluate_held_out_quality(evidence: VerifiedEvaluationSet, floor: QualityFloor, route: RouteDefinition,
                              config: VerifierConfig) -> QualityAssessment:
    return _assessment(route, evidence, floor, config, EvaluationScope.HELD_OUT)


def combine_route_eligibility(measured: QualityAssessment, held_out: QualityAssessment,
                              route: RouteDefinition, floor: QualityFloor,
                              config: VerifierConfig) -> RouteEligibility:
    expected = (route.route_id, freeze_hash(route), freeze_hash(floor), freeze_hash(config))
    measured_identity = (measured.route_id, measured.route_definition_digest, measured.quality_floor_digest,
                         measured.verifier_config_digest)
    held_out_identity = (held_out.route_id, held_out.route_definition_digest, held_out.quality_floor_digest,
                         held_out.verifier_config_digest)
    if measured.scope is not EvaluationScope.MEASURED or held_out.scope is not EvaluationScope.HELD_OUT:
        raise ValueError("eligibility requires separate measured and held-out assessments")
    if measured_identity != expected or held_out_identity != expected:
        raise ValueError("quality assessments must bind the same route, floor, and verifier")
    measured_cases = {item.case_id for item in measured.verified_evidence.verification_inputs}
    held_out_cases = {item.case_id for item in held_out.verified_evidence.verification_inputs}
    if measured.verified_evidence.evidence_digest == held_out.verified_evidence.evidence_digest:
        raise ValueError("measured and held-out evidence must be separate populations")
    if measured_cases & held_out_cases:
        raise ValueError("measured and held-out case IDs must be disjoint")
    details = {
        "route_id": route.route_id,
        "route_definition_digest": freeze_hash(route),
        "quality_floor_digest": freeze_hash(floor),
        "verifier_config_digest": freeze_hash(config),
        "measured": measured,
        "held_out": held_out,
        "eligible": measured.passed and held_out.passed,
    }
    return RouteEligibility(**details, decision_digest=freeze_hash(details))


def economically_eligible(route: RouteDefinition, eligibility: RouteEligibility, floor: QualityFloor,
                          config: VerifierConfig) -> bool:
    if (eligibility.route_id, eligibility.route_definition_digest, eligibility.quality_floor_digest,
            eligibility.verifier_config_digest) != (route.route_id, freeze_hash(route), freeze_hash(floor), freeze_hash(config)):
        return False
    try:
        measured = evaluate_measured_quality(eligibility.measured.verified_evidence, floor, route, config)
        held_out = evaluate_held_out_quality(eligibility.held_out.verified_evidence, floor, route, config)
        derived = combine_route_eligibility(measured, held_out, route, floor, config)
    except (AttributeError, ValueError):
        return False
    return derived.eligible and freeze_hash(derived) == freeze_hash(eligibility)


def authorize_execution(provider: str, billable: bool, authority: RouteExecutionAuthority) -> bool:
    return provider in authority.allowed_providers and (authority.allow_billable_routes or not billable)
