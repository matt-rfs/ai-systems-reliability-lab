from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MetricEpistemicState(str, Enum):
    ACTUAL = "ACTUAL"
    ESTIMATED = "ESTIMATED"
    UNPRICED = "UNPRICED"
    UNKNOWN = "UNKNOWN"


class MetricApplicability(str, Enum):
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Metric(BaseModel):
    value: float | int | None
    unit: str
    epistemic_state: MetricEpistemicState
    applicability: MetricApplicability
    source: str
    collection_method: str
    coverage: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_value_semantics(self) -> "Metric":
        if self.applicability is MetricApplicability.NOT_APPLICABLE:
            if self.value is not None or self.epistemic_state is not MetricEpistemicState.UNPRICED:
                raise ValueError("not-applicable metrics must be value-less and explicitly UNPRICED")
        if self.applicability is MetricApplicability.APPLICABLE:
            if self.epistemic_state in {MetricEpistemicState.ACTUAL, MetricEpistemicState.ESTIMATED} and self.value is None:
                raise ValueError("actual or estimated applicable metrics require a value")
            if self.epistemic_state in {MetricEpistemicState.UNKNOWN, MetricEpistemicState.UNPRICED} and self.value is not None:
                raise ValueError("unknown or unpriced metrics cannot be fabricated as numeric values")
        return self


class CheckResult(BaseModel):
    name: str
    passed: bool
    hard_gate: bool
    detail: str


class CaseEvaluation(BaseModel):
    case_id: str
    checks: list[CheckResult]

    @property
    def hard_gate_failed(self) -> bool:
        return any(check.hard_gate and not check.passed for check in self.checks)

    @property
    def case_pass(self) -> bool:
        return all(check.passed for check in self.checks)


class RouteType(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    SINGLE_PASS_MODEL = "SINGLE_PASS_MODEL"
    DECOMPOSED_MODEL = "DECOMPOSED_MODEL"


FORBIDDEN_DETERMINISTIC_FEATURES = frozenset({"case_id", "expected_answer", "hidden_ground_truth", "verifier_result"})
ALLOWED_DETERMINISTIC_FEATURES = frozenset({"request_length", "required_step_count", "allowed_vocabulary_size"})


class RouteDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)
    route_id: str
    route_version: str
    route_type: RouteType
    applicability_features: frozenset[str]
    telemetry_declaration: frozenset[str]

    @model_validator(mode="after")
    def validate_deterministic_applicability(self) -> "RouteDefinition":
        if self.route_type is RouteType.DETERMINISTIC:
            if self.applicability_features & FORBIDDEN_DETERMINISTIC_FEATURES:
                raise ValueError("deterministic-route applicability cannot use lookup or verifier features")
            if not self.applicability_features.issubset(ALLOWED_DETERMINISTIC_FEATURES):
                raise ValueError("deterministic-route applicability exceeds the frozen structural feature surface")
        return self


class QualityEvidenceReference(BaseModel):
    model_config = ConfigDict(frozen=True)
    evidence_id: str
    content_digest: str


class EvaluationScope(str, Enum):
    MEASURED = "MEASURED"
    HELD_OUT = "HELD_OUT"


class VerificationInput(BaseModel):
    """The deterministic verifier input retained to make evaluation evidence replayable."""
    model_config = ConfigDict(frozen=True)
    case_id: str
    candidate: dict[str, Any]


class VerifiedEvaluationSet(BaseModel):
    """Verifier-bound output; its checks are re-run at the economic boundary."""
    model_config = ConfigDict(frozen=True)
    verifier_config_digest: str
    route_id: str
    route_definition_digest: str
    evidence_digest: str
    case_count: int = Field(ge=1)
    distinct_case_ids_digest: str
    verification_inputs: tuple[VerificationInput, ...]
    evaluations: tuple[CaseEvaluation, ...]


class QualityAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)
    route_id: str
    route_definition_digest: str
    quality_floor_digest: str
    verifier_config_digest: str
    scope: EvaluationScope
    verified_evidence: VerifiedEvaluationSet
    evaluated_case_count: int = Field(ge=1)
    distinct_case_ids_digest: str
    pass_count: int = Field(ge=0)
    pass_rate: float = Field(ge=0, le=1)
    hard_gate_violation_count: int = Field(ge=0)
    passed: bool
    reasons: tuple[str, ...]
    decision_digest: str


class RouteEligibility(BaseModel):
    model_config = ConfigDict(frozen=True)
    route_id: str
    route_definition_digest: str
    quality_floor_digest: str
    verifier_config_digest: str
    measured: QualityAssessment
    held_out: QualityAssessment
    eligible: bool
    decision_digest: str


class AttemptTrace(BaseModel):
    experiment_id: str
    run_id: str
    case_id: str
    route_id: str
    route_version: str
    attempt_index: int
    runtime: str
    provider: str
    model: str | None
    model_digest: str | None
    input_tokens: Metric
    output_tokens: Metric
    latency_ms: Metric
    model_calls: Metric
    human_interventions: Metric
    verifier_result: CaseEvaluation | None
    status: str


class QualityFloor(BaseModel):
    model_config = ConfigDict(frozen=True)

    zero_hard_gate_violations: bool = True
    minimum_measured_case_pass_rate: float = Field(default=0.90, ge=0, le=1)
    held_out_minimum_passes: int = 11
    held_out_case_count: int = 12
    held_out_zero_hard_gate_violations: bool = True


class RunbookPlan(BaseModel):
    steps: list[str]
    requires_human_authority: bool
    policy_citations: list[str]


class VerifierConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    allowed_steps: frozenset[str]
    required_steps: frozenset[str]
    forbidden_steps: frozenset[str]
    required_human_authority: bool
    supplied_policy_ids: frozenset[str]
    required_policy_citations: frozenset[str]
    ordering_constraints: tuple[tuple[str, str], ...] = ()


class RouteExecutionAuthority(BaseModel):
    model_config = ConfigDict(frozen=True)
    allowed_providers: frozenset[str] = frozenset({"local"})
    allow_billable_routes: bool = False


BURDEN_DIMENSIONS = ("model_calls", "total_tokens", "latency_ms", "human_interventions")
