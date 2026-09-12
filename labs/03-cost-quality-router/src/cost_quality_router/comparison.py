from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from .freeze import freeze_hash
from .models import (BURDEN_DIMENSIONS, Metric, MetricApplicability, MetricEpistemicState, QualityFloor,
                     RouteDefinition, RouteEligibility, VerifierConfig)
from .routes import economically_eligible


class BurdenRecord(BaseModel):
    route: RouteDefinition
    eligibility: RouteEligibility
    quality_floor: QualityFloor
    verifier_config: VerifierConfig
    burdens: dict[str, Metric]


class ParetoResult(str, Enum):
    LEFT_DOMINATES = "LEFT_DOMINATES"
    RIGHT_DOMINATES = "RIGHT_DOMINATES"
    TRADEOFF = "TRADEOFF"
    EQUAL = "EQUAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


def compare_pareto(left: BurdenRecord, right: BurdenRecord) -> ParetoResult:
    if freeze_hash(left.quality_floor) != freeze_hash(right.quality_floor):
        raise ValueError("Pareto comparison requires the same frozen quality floor")
    if freeze_hash(left.verifier_config) != freeze_hash(right.verifier_config):
        raise ValueError("Pareto comparison requires the same frozen verifier configuration")
    if not economically_eligible(left.route, left.eligibility, left.quality_floor, left.verifier_config) or not economically_eligible(
            right.route, right.eligibility, right.quality_floor, right.verifier_config):
        raise ValueError("quality-ineligible routes cannot enter economic comparison")
    left_values, right_values = [], []
    for dimension in BURDEN_DIMENSIONS:
        if dimension not in left.route.telemetry_declaration or dimension not in right.route.telemetry_declaration:
            return ParetoResult.INSUFFICIENT_EVIDENCE
        left_metric, right_metric = left.burdens.get(dimension), right.burdens.get(dimension)
        if left_metric is None or right_metric is None:
            return ParetoResult.INSUFFICIENT_EVIDENCE
        if any(metric.applicability is not MetricApplicability.APPLICABLE or metric.value is None
               or metric.epistemic_state in {MetricEpistemicState.UNKNOWN, MetricEpistemicState.UNPRICED}
               or metric.coverage != 1.0
               for metric in (left_metric, right_metric)):
            return ParetoResult.INSUFFICIENT_EVIDENCE
        left_values.append(left_metric.value)
        right_values.append(right_metric.value)
    if all(a <= b for a, b in zip(left_values, right_values)) and any(a < b for a, b in zip(left_values, right_values)):
        return ParetoResult.LEFT_DOMINATES
    if all(a >= b for a, b in zip(left_values, right_values)) and any(a > b for a, b in zip(left_values, right_values)):
        return ParetoResult.RIGHT_DOMINATES
    if left_values == right_values:
        return ParetoResult.EQUAL
    return ParetoResult.TRADEOFF
