"""Static, synthetic Lab 03 inputs.  Building these records never executes a route."""
from __future__ import annotations

from collections import Counter
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .models import ALLOWED_DETERMINISTIC_FEATURES, VerifierConfig


CASE_SCHEMA_VERSION = "L03-CASE-V001"
POLICIES = {
    "POL-VERIFY": "Validate request inputs before preparing an action.",
    "POL-DOC": "Record the decision before closing a request.",
    "POL-APPROVAL": "Human approval is required when synthetic action value exceeds the approval threshold.",
    "POL-APPROVAL-THRESHOLD": "The synthetic approval threshold is 50 units.",
    "POL-ESCALATE": "Escalate an exception instead of executing an action.",
    "POL-NOTIFY": "Notify the stakeholder before closure when notification is required.",
    "POL-CLOSE": "Close only after required documentation is recorded.",
    "POL-STANDARD": "For status STANDARD, prepare an action and do not escalate an exception.",
    "POL-EXCEPTION": "For status EXCEPTION, escalate the exception and do not prepare an action.",
}
VOCABULARY = ("assess_request", "validate_inputs", "review_policy", "collect_evidence", "confirm_threshold",
              "request_human_approval", "prepare_action", "execute_allowed_action", "record_decision",
              "notify_stakeholder", "close_request", "escalate_exception")


class Split(str, Enum):
    VISIBLE = "VISIBLE"
    HELD_OUT = "HELD_OUT"
    CANARY = "CANARY"


class Tier(str, Enum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"
    CANARY = "CANARY"


class PolicyFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    policy_id: str
    policy_text: str


class RunbookCase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    case_id: str
    split: Split
    tier: Tier
    request: str
    policy_facts: tuple[PolicyFact, ...]
    allowed_steps: tuple[str, ...]
    required_steps: tuple[str, ...]
    forbidden_steps: tuple[str, ...]
    required_policy_ids: tuple[str, ...]
    ordering_constraints: tuple[tuple[str, str], ...]
    required_human_authority: bool
    r0_applicability_features: tuple[str, ...]
    planning_size_hint: int = Field(ge=3, le=5)
    schema_version: str
    canary_band: str | None = None


class RouteInput(BaseModel):
    """The only pre-execution task surface shared by R0, R1, and R2."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    request: str
    policy_facts: tuple[PolicyFact, ...]
    allowed_steps: tuple[str, ...]
    planning_size_hint: int
    schema_version: str


class RouteInputProjectionSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CASE_SCHEMA_VERSION
    visible_fields: tuple[str, ...] = ("request", "policy_facts", "allowed_steps", "planning_size_hint", "schema_version")
    excluded_fields: tuple[str, ...] = ("case_id", "split", "tier", "required_steps", "forbidden_steps", "required_policy_ids", "ordering_constraints", "required_human_authority", "r0_applicability_features", "canary_band")
    r0_feature_derivation: tuple[tuple[str, str], ...] = (("request_length", "len(RouteInput.request)"), ("required_step_count", "RouteInput.planning_size_hint"), ("allowed_vocabulary_size", "len(RouteInput.allowed_steps)"))


V001_ROUTE_INPUT_PROJECTION = RouteInputProjectionSpec()


class RouteObservationContract(BaseModel):
    model_config = ConfigDict(frozen=True)
    candidate_construction_input: tuple[tuple[str, tuple[str, ...]], ...] = (("R0", V001_ROUTE_INPUT_PROJECTION.visible_fields), ("R1", V001_ROUTE_INPUT_PROJECTION.visible_fields), ("R2", V001_ROUTE_INPUT_PROJECTION.visible_fields))
    r0_applicability_input: tuple[str, ...] = tuple(sorted(ALLOWED_DETERMINISTIC_FEATURES))


V001_ROUTE_OBSERVATION_CONTRACT = RouteObservationContract()


def _case(case_id: str, split: Split, tier: Tier, index: int, canary_band: str | None = None) -> RunbookCase:
    if split is Split.HELD_OUT:
        action_value = 85 if index % 2 == 0 else 35
    elif split is Split.CANARY:
        action_value = 95 if index % 2 == 0 else 45
    else:
        action_value = 75 if index % 2 == 0 else 25
    authority = action_value > 50
    planning_size_hint = 3 + (index % 3)
    request_variant = ("brief", "standard", "extended")[index % 3]
    scenario_value = f" with synthetic scenario value {index:03d}"
    status = "EXCEPTION" if index % 3 == 0 else "STANDARD"
    if tier is Tier.TIER_1 or (tier is Tier.CANARY and canary_band == "EASY"):
        required = ("assess_request", "review_policy", "record_decision")
        policy_ids, forbidden = ("POL-VERIFY", "POL-DOC", "POL-APPROVAL", "POL-APPROVAL-THRESHOLD"), ()
        ordering = (("assess_request", "review_policy"), ("review_policy", "record_decision"))
    elif tier is Tier.TIER_2 or (tier is Tier.CANARY and canary_band == "MEDIUM"):
        required = ("assess_request", "validate_inputs", "review_policy", "collect_evidence", "record_decision")
        policy_ids, forbidden = ("POL-VERIFY", "POL-DOC", "POL-APPROVAL", "POL-APPROVAL-THRESHOLD"), ("execute_allowed_action",)
        ordering = (("assess_request", "validate_inputs"), ("validate_inputs", "collect_evidence"),
                    ("review_policy", "record_decision"))
    else:
        authority_step = ("request_human_approval",) if authority else ()
        required = ("assess_request", "validate_inputs", "review_policy", "collect_evidence", "confirm_threshold",
                    *authority_step, "record_decision", "notify_stakeholder", "close_request")
        policy_ids, forbidden = ("POL-VERIFY", "POL-DOC", "POL-APPROVAL", "POL-APPROVAL-THRESHOLD", "POL-NOTIFY", "POL-CLOSE"), ("execute_allowed_action",)
        ordering = (("assess_request", "validate_inputs"), ("validate_inputs", "collect_evidence"),
                    ("collect_evidence", "confirm_threshold"), ("record_decision", "notify_stakeholder"),
                    ("notify_stakeholder", "close_request"))
    if status == "STANDARD":
        required = (*required, "prepare_action")
        forbidden = (*forbidden, "escalate_exception")
        policy_ids = (*policy_ids, "POL-STANDARD")
        ordering = (*ordering, ("review_policy", "prepare_action"), ("prepare_action", "record_decision"))
    else:
        required = (*required, "escalate_exception")
        forbidden = (*forbidden, "prepare_action", "execute_allowed_action")
        policy_ids = (*policy_ids, "POL-EXCEPTION")
        ordering = (*ordering, ("review_policy", "escalate_exception"), ("escalate_exception", "record_decision"))
    return RunbookCase(case_id=case_id, split=split, tier=tier,
                       request=f"Prepare a {request_variant} synthetic operational runbook for status {status} and action value {action_value} units with planning hint {planning_size_hint}{scenario_value}; follow the supplied policy facts.",
                       policy_facts=tuple(PolicyFact(policy_id=policy_id, policy_text=POLICIES[policy_id]) for policy_id in policy_ids),
                       allowed_steps=VOCABULARY, required_steps=required, forbidden_steps=forbidden,
                       required_policy_ids=policy_ids, ordering_constraints=ordering,
                       required_human_authority=authority,
                       r0_applicability_features=tuple(sorted(ALLOWED_DETERMINISTIC_FEATURES)),
                       planning_size_hint=planning_size_hint,
                       schema_version=CASE_SCHEMA_VERSION, canary_band=canary_band)


def build_case_collection() -> tuple[RunbookCase, ...]:
    cases: list[RunbookCase] = []
    for split, prefix, per_tier in ((Split.VISIBLE, "V", 8), (Split.HELD_OUT, "H", 4)):
        for tier_number, tier in enumerate((Tier.TIER_1, Tier.TIER_2, Tier.TIER_3), start=1):
            for index in range(1, per_tier + 1):
                cases.append(_case(f"L03-{prefix}-T{tier_number}-{index:03d}", split, tier, index + tier_number * 100))
    for index, band in enumerate(("EASY", "EASY", "MEDIUM", "MEDIUM", "HARD", "HARD"), start=1):
        cases.append(_case(f"L03-C-{index:03d}", Split.CANARY, Tier.CANARY, index + 900, band))
    return tuple(cases)


def project_route_input(case: RunbookCase) -> RouteInput:
    return RouteInput(request=case.request, policy_facts=case.policy_facts, allowed_steps=case.allowed_steps,
                      planning_size_hint=case.planning_size_hint, schema_version=case.schema_version)


def r0_structural_features(route_input: RouteInput) -> dict[str, int]:
    return {"request_length": len(route_input.request), "required_step_count": route_input.planning_size_hint,
            "allowed_vocabulary_size": len(route_input.allowed_steps)}


def verifier_config_for_case(case: RunbookCase) -> VerifierConfig:
    return VerifierConfig(allowed_steps=frozenset(case.allowed_steps), required_steps=frozenset(case.required_steps),
                          forbidden_steps=frozenset(case.forbidden_steps),
                          required_human_authority=case.required_human_authority,
                          supplied_policy_ids=frozenset(fact.policy_id for fact in case.policy_facts),
                          required_policy_citations=frozenset(case.required_policy_ids),
                          ordering_constraints=case.ordering_constraints)


def validate_case_collection(cases: tuple[RunbookCase, ...]) -> None:
    if len(cases) != 42 or len({case.case_id for case in cases}) != 42:
        raise ValueError("case collection must contain 42 unique cases")
    splits = Counter(case.split for case in cases)
    if splits != Counter({Split.VISIBLE: 24, Split.HELD_OUT: 12, Split.CANARY: 6}):
        raise ValueError("case split counts are frozen")
    measured = [case for case in cases if case.split is not Split.CANARY]
    if Counter(case.tier for case in measured) != Counter({Tier.TIER_1: 12, Tier.TIER_2: 12, Tier.TIER_3: 12}):
        raise ValueError("measured tier counts are frozen")
    for split, expected in ((Split.VISIBLE, 8), (Split.HELD_OUT, 4)):
        if Counter(case.tier for case in cases if case.split is split) != Counter({Tier.TIER_1: expected, Tier.TIER_2: expected, Tier.TIER_3: expected}):
            raise ValueError("visible and held-out tier balance is frozen")
    for case in cases:
        allowed, required, forbidden = set(case.allowed_steps), set(case.required_steps), set(case.forbidden_steps)
        if not set(case.r0_applicability_features).issubset(ALLOWED_DETERMINISTIC_FEATURES):
            raise ValueError("case cannot expand R0 applicability")
        if not required.issubset(allowed) or not forbidden.issubset(allowed) or required & forbidden:
            raise ValueError("case step requirements are inconsistent")
        if not set(case.required_policy_ids).issubset({fact.policy_id for fact in case.policy_facts}):
            raise ValueError("case citation requirements lack policy facts")
        if any(step not in allowed for pair in case.ordering_constraints for step in pair):
            raise ValueError("ordering constraint references an unknown step")
        graph = {step: set() for step in allowed}
        for before, after in case.ordering_constraints: graph[before].add(after)
        visiting, visited = set(), set()
        def visit(step: str) -> None:
            if step in visiting: raise ValueError("ordering constraints are cyclic")
            if step not in visited:
                visiting.add(step)
                for next_step in graph[step]: visit(next_step)
                visiting.remove(step); visited.add(step)
        for step in graph: visit(step)
