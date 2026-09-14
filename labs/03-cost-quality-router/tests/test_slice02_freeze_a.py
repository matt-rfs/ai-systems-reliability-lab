import json

import pytest

from cost_quality_router.cases import (ALLOWED_DETERMINISTIC_FEATURES, RouteInputProjectionSpec, Split, Tier,
                                        V001_ROUTE_INPUT_PROJECTION, V001_ROUTE_OBSERVATION_CONTRACT, build_case_collection, project_route_input,
                                        r0_structural_features, validate_case_collection, verifier_config_for_case)
from cost_quality_router.freeze import freeze_hash
from cost_quality_router.freeze_a import CANARY_PACKET_PATH, CASES_PATH, MANIFEST_PATH, build_freeze_a
from cost_quality_router.routes import R0, R1, R2, V001_QUALITY_FLOOR
from cost_quality_router.verifier import V001_VERIFIER_SEMANTICS, verify_runbook


def test_case_counts_tiers_and_boundaries_are_frozen():
    cases = build_case_collection()
    validate_case_collection(cases)
    assert len(cases) == 42
    assert sum(case.split is not Split.CANARY for case in cases) == 36
    assert sum(case.split is Split.VISIBLE for case in cases) == 24
    assert sum(case.split is Split.HELD_OUT for case in cases) == 12
    assert sum(case.split is Split.CANARY for case in cases) == 6
    ids = [case.case_id for case in cases]
    assert len(ids) == len(set(ids))
    assert [sum(case.tier is tier for case in cases) for tier in (Tier.TIER_1, Tier.TIER_2, Tier.TIER_3)] == [12, 12, 12]
    assert all(set(case.r0_applicability_features).issubset(ALLOWED_DETERMINISTIC_FEATURES) for case in cases)


def test_freeze_a_reproduces_stored_cases_and_manifest_without_execution():
    document, packet, manifest = build_freeze_a()
    assert json.loads(CASES_PATH.read_text()) == document
    assert json.loads(CANARY_PACKET_PATH.read_text()) == packet
    assert json.loads(MANIFEST_PATH.read_text()) == manifest
    assert manifest["counts"] == {"measured_total": 36, "visible_total": 24, "held_out_total": 12, "canary_total": 6,
                                  "measured_tiers": {"TIER_1": 12, "TIER_2": 12, "TIER_3": 12}}
    assert manifest["quality_floor_digest"] == freeze_hash(V001_QUALITY_FLOOR)
    assert manifest["canary_packet_digest"] == freeze_hash(packet)
    assert manifest["verifier_semantics_digest"] == freeze_hash(V001_VERIFIER_SEMANTICS)
    assert manifest["route_input_projection_digest"] == freeze_hash(V001_ROUTE_INPUT_PROJECTION)
    assert manifest["route_observation_contract_digest"] == freeze_hash(V001_ROUTE_OBSERVATION_CONTRACT)
    assert manifest["route_definition_digests"] == {"R0": freeze_hash(R0), "R1": freeze_hash(R1), "R2": freeze_hash(R2)}
    assert manifest["no_route_output_exists_yet"] and manifest["no_measured_result_exists_yet"]


def test_case_or_config_changes_have_distinct_canonical_identity():
    cases = build_case_collection()
    first = cases[0].model_copy(update={"request": "materially different synthetic request"})
    assert freeze_hash(cases) != freeze_hash((first, *cases[1:]))
    assert freeze_hash({"b": 2, "a": 1}) == freeze_hash({"a": 1, "b": 2})
    assert freeze_hash(frozenset({"a", "b"})) == freeze_hash(frozenset({"b", "a"}))
    assert freeze_hash(verifier_config_for_case(cases[0])) != freeze_hash(verifier_config_for_case(cases[-1]))


def test_invalid_case_integrity_fails_closed():
    cases = build_case_collection()
    duplicate = cases[0].model_copy(update={"case_id": cases[1].case_id})
    with pytest.raises(ValueError):
        validate_case_collection((duplicate, *cases[1:]))
    expanded = cases[0].model_copy(update={"r0_applicability_features": ("case_id",)})
    with pytest.raises(ValueError):
        validate_case_collection((expanded, *cases[1:]))


def test_route_input_projection_hides_verifier_expectations_and_is_deterministic():
    case = build_case_collection()[0]
    route_input = project_route_input(case)
    assert set(route_input.model_dump()) == {"request", "policy_facts", "allowed_steps", "planning_size_hint", "schema_version"}
    for hidden in ("required_steps", "forbidden_steps", "required_policy_ids", "ordering_constraints", "required_human_authority", "case_id", "split", "tier", "canary_band"):
        assert hidden not in route_input.model_dump()
    assert route_input == project_route_input(case)
    verifier_changed = case.model_copy(update={"required_steps": ("close_request",)})
    visible_changed = case.model_copy(update={"request": "different visible request"})
    assert project_route_input(verifier_changed) == route_input
    assert project_route_input(visible_changed) != route_input


def test_authority_and_r0_features_are_derivable_without_a_structural_oracle():
    cases = build_case_collection()
    true_case = next(case for case in cases if case.required_human_authority)
    false_case = next(case for case in cases if not case.required_human_authority)
    assert "75 units" in project_route_input(true_case).request
    assert "25 units" in project_route_input(false_case).request
    assert any("exceeds the approval threshold" in fact.policy_text for fact in project_route_input(true_case).policy_facts)
    features = [(case.tier.value, case.required_human_authority, r0_structural_features(project_route_input(case))) for case in cases]
    for name in ALLOWED_DETERMINISTIC_FEATURES:
        mapping = {}
        for tier, authority, values in features:
            mapping.setdefault(values[name], set()).add((tier, authority))
        assert all(len(outcomes) > 1 for outcomes in mapping.values())
    assert len({r0_structural_features(project_route_input(case))["request_length"] for case in cases}) > 1


def test_semantic_and_projection_mutations_change_freeze_identity():
    _, _, manifest = build_freeze_a()
    changed_checks = tuple(check.model_copy(update={"hard_gate": False}) if check.check_name == "duplicate_steps_absent" else check for check in V001_VERIFIER_SEMANTICS.checks)
    changed_semantics = V001_VERIFIER_SEMANTICS.model_copy(update={"checks": changed_checks})
    authority_checks = tuple(check.model_copy(update={"hard_gate": False}) if check.check_name == "human_authority" else check for check in V001_VERIFIER_SEMANTICS.checks)
    changed_authority_semantics = V001_VERIFIER_SEMANTICS.model_copy(update={"checks": authority_checks})
    changed_projection = V001_ROUTE_INPUT_PROJECTION.model_copy(update={"visible_fields": ("request", "policy_facts", "allowed_steps", "schema_version")})
    assert freeze_hash(changed_semantics) != manifest["verifier_semantics_digest"]
    assert freeze_hash(changed_authority_semantics) != manifest["verifier_semantics_digest"]
    assert freeze_hash(changed_projection) != manifest["route_input_projection_digest"]
    _, _, semantic_mutation = build_freeze_a(verifier_semantics=changed_semantics)
    _, _, projection_mutation = build_freeze_a(route_input_projection=changed_projection)
    assert semantic_mutation["freeze_a_digest"] != manifest["freeze_a_digest"]
    assert projection_mutation["freeze_a_digest"] != manifest["freeze_a_digest"]


def test_constant_plan_strategies_cannot_clear_measured_or_held_out_floor():
    cases = build_case_collection()
    strategies = []
    for mode in ("all_allowed", "all_required_union", "minimal_common"):
        strategies.append(mode)
    for mode in strategies:
        results = []
        for case in cases:
            if mode == "all_allowed": steps = list(case.allowed_steps)
            elif mode == "all_required_union": steps = ["assess_request", "validate_inputs", "review_policy", "collect_evidence", "confirm_threshold", "request_human_approval", "prepare_action", "escalate_exception", "record_decision", "notify_stakeholder", "close_request"]
            else: steps = ["assess_request", "review_policy", "record_decision"]
            route_input = project_route_input(case)
            authority = int(route_input.request.split("action value ")[1].split(" units")[0]) > 50
            candidate = {"steps": steps, "requires_human_authority": authority, "policy_citations": [fact.policy_id for fact in route_input.policy_facts]}
            results.append((case, verify_runbook(case.case_id, candidate, verifier_config_for_case(case))))
        measured = [result for case, result in results if case.split is not Split.CANARY]
        held_out = [result for case, result in results if case.split is Split.HELD_OUT]
        assert sum(result.case_pass for result in measured) / len(measured) < .90 or any(result.hard_gate_failed for result in measured)
        assert sum(result.case_pass for result in held_out) < 11 or any(result.hard_gate_failed for result in held_out)


def test_held_out_and_canary_route_inputs_are_novel_and_disjoint_from_visible():
    cases = build_case_collection()
    visible = {freeze_hash(project_route_input(case)) for case in cases if case.split is Split.VISIBLE}
    held_out = {freeze_hash(project_route_input(case)) for case in cases if case.split is Split.HELD_OUT}
    canary = {freeze_hash(project_route_input(case)) for case in cases if case.split is Split.CANARY}
    assert len(held_out) == 12
    assert visible.isdisjoint(held_out)
    assert canary.isdisjoint(visible | held_out)


def test_r0_feature_derivation_matches_frozen_route_input_declaration():
    case = build_case_collection()[0]
    route_input = project_route_input(case)
    values = r0_structural_features(route_input)
    assert values == {"request_length": len(route_input.request), "required_step_count": route_input.planning_size_hint,
                      "allowed_vocabulary_size": len(route_input.allowed_steps)}


def test_r0_features_do_not_oracle_split_or_canary_membership_and_requests_hide_labels():
    cases = build_case_collection()
    for case in cases:
        text = project_route_input(case).request.lower()
        assert "visible" not in text and "held-out" not in text and "canary" not in text
    for feature_name in ALLOWED_DETERMINISTIC_FEATURES:
        split_map, canary_map = {}, {}
        for case in cases:
            value = r0_structural_features(project_route_input(case))[feature_name]
            split_map.setdefault(value, set()).add(case.split.value)
            canary_map.setdefault(value, set()).add(case.split is Split.CANARY)
        assert any(len(labels) > 1 for labels in split_map.values())
        assert any(len(labels) > 1 for labels in canary_map.values())
