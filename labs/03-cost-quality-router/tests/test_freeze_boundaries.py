import os
import subprocess
import sys

import pytest

from cost_quality_router.freeze import canonical_json, freeze_hash
from cost_quality_router.models import QualityFloor, RouteExecutionAuthority, VerifierConfig
from cost_quality_router.routes import R0, V001_QUALITY_FLOOR


def verifier():
    return VerifierConfig(allowed_steps=frozenset({"assess", "review"}), required_steps=frozenset({"assess"}),
                          forbidden_steps=frozenset(), required_human_authority=True,
                          supplied_policy_ids=frozenset({"P1"}), required_policy_citations=frozenset({"P1"}))


def test_cross_process_frozenset_hash_is_stable_under_hash_seed_changes():
    program = "from cost_quality_router.freeze import freeze_hash; from cost_quality_router.routes import R0; print(freeze_hash(R0))"
    source_root = str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src")
    digests = set()
    for seed in ("1", "99", "random"):
        environment = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": source_root}
        digests.add(subprocess.check_output([sys.executable, "-c", program], env=environment, text=True).strip())
    assert len(digests) == 1


def test_nested_models_sets_and_lists_are_canonical_but_list_order_is_preserved():
    left = {"nested": [R0, {"set": frozenset({"b", "a"})}]}
    right = {"nested": [R0, {"set": frozenset({"a", "b"})}]}
    assert freeze_hash(left) == freeze_hash(right)
    assert canonical_json(["a", "b"]) != canonical_json(["b", "a"])


def test_frozen_configs_reject_mutation_and_expose_modified_replacement():
    floor, config = QualityFloor(), verifier()
    with pytest.raises(Exception): floor.minimum_measured_case_pass_rate = 0.0
    with pytest.raises(Exception): config.required_human_authority = False
    changed_floor = floor.model_copy(update={"minimum_measured_case_pass_rate": .95})
    bypassed = QualityFloor.model_construct(minimum_measured_case_pass_rate=.1)
    assert freeze_hash(floor) != freeze_hash(changed_floor)
    assert freeze_hash(floor) != freeze_hash(bypassed)
    assert freeze_hash(changed_floor) != freeze_hash(bypassed)
    assert freeze_hash(floor) != freeze_hash(config)
    assert freeze_hash(floor) != freeze_hash(R0)
    assert freeze_hash(config) != freeze_hash(R0)


def test_execution_authority_is_frozen_and_hashes_each_material_change():
    authority = RouteExecutionAuthority()
    with pytest.raises(Exception):
        authority.allowed_providers = frozenset({"remote"})
    provider_changed = authority.model_copy(update={"allowed_providers": frozenset({"local", "remote"})})
    billable_changed = authority.model_copy(update={"allow_billable_routes": True})
    assert freeze_hash(authority) != freeze_hash(provider_changed)
    assert freeze_hash(authority) != freeze_hash(billable_changed)
    assert freeze_hash(provider_changed) != freeze_hash(billable_changed)


def test_v001_quality_floor_anchor_is_immutable_and_canonically_default():
    assert freeze_hash(V001_QUALITY_FLOOR) == freeze_hash(QualityFloor())
    with pytest.raises(Exception):
        V001_QUALITY_FLOOR.held_out_case_count = 11
