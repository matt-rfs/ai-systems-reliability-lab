"""Explicit, deterministic Freeze A generation; importing this module performs no writes."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .cases import (CASE_SCHEMA_VERSION, POLICIES, VOCABULARY, Split, V001_ROUTE_INPUT_PROJECTION, V001_ROUTE_OBSERVATION_CONTRACT,
                    build_case_collection, validate_case_collection, verifier_config_for_case)
from .freeze import freeze_hash
from .models import BURDEN_DIMENSIONS, MetricEpistemicState
from .routes import R0, R1, R2, R0_ALLOWED_FEATURES, V001_QUALITY_FLOOR
from .verifier import V001_VERIFIER_SEMANTICS


LAB_ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = LAB_ROOT / "config" / "cases-v001.json"
MANIFEST_PATH = LAB_ROOT / "config" / "freeze-a-v001.json"
CANARY_PACKET_PATH = LAB_ROOT / "config" / "eligibility-canary-v001.json"


def _records(cases):
    return [case.model_dump(mode="json") for case in cases]


def build_freeze_a(verifier_semantics=V001_VERIFIER_SEMANTICS,
                   route_input_projection=V001_ROUTE_INPUT_PROJECTION,
                   route_observation_contract=V001_ROUTE_OBSERVATION_CONTRACT) -> tuple[dict, dict, dict]:
    cases = build_case_collection()
    validate_case_collection(cases)
    records = _records(cases)
    visible = [record for record in records if record["split"] == Split.VISIBLE.value]
    held_out = [record for record in records if record["split"] == Split.HELD_OUT.value]
    canary = [record for record in records if record["split"] == Split.CANARY.value]
    case_document = {"schema_version": CASE_SCHEMA_VERSION, "policy_universe": POLICIES,
                     "allowed_step_vocabulary": list(VOCABULARY), "cases": records}
    canary_packet = {"packet_version": "L03-CANARY-V001", "case_ids": [record["case_id"] for record in canary],
                     "route_ids": ["R0", "R1", "R2"], "execution_authority": "NOT_AUTHORIZED_IN_SLICE_02",
                     "dispositions": ["ELIGIBLE", "INELIGIBLE", "RUNTIME_UNUSABLE", "CAPABILITY_GRADIENT_ABSENT", "NO_ROUTER_NEEDED"],
                     "excluded_from_measured_statistics": True, "cannot_change_freeze_a": True}
    verifier_surface = {case.case_id: verifier_config_for_case(case) for case in cases}
    payload = {
        "freeze_version": "FREEZE-A-V001", "lab_id": "LAB-03", "schema_version": CASE_SCHEMA_VERSION,
        "case_collection_digest": freeze_hash(case_document), "visible_case_digest": freeze_hash(visible),
        "held_out_case_digest": freeze_hash(held_out), "canary_case_digest": freeze_hash(canary),
        "policy_universe_digest": freeze_hash(POLICIES), "allowed_step_vocabulary_digest": freeze_hash(VOCABULARY),
        "verifier_config_digest": freeze_hash(verifier_surface), "quality_floor_digest": freeze_hash(V001_QUALITY_FLOOR),
        "verifier_semantics_digest": freeze_hash(verifier_semantics),
        "route_input_projection_digest": freeze_hash(route_input_projection),
        "route_observation_contract_digest": freeze_hash(route_observation_contract),
        "verifier_config_digest_meaning": "canonical aggregate digest of case-derived VerifierConfig objects keyed by case ID",
        "route_definition_digests": {"R0": freeze_hash(R0), "R1": freeze_hash(R1), "R2": freeze_hash(R2)},
        "r0_applicability_surface_digest": freeze_hash(R0_ALLOWED_FEATURES),
        "burden_dimensions_digest": freeze_hash(BURDEN_DIMENSIONS),
        "metric_epistemic_states": [state.value for state in MetricEpistemicState],
        "counts": {"measured_total": 36, "visible_total": 24, "held_out_total": 12, "canary_total": 6,
                   "measured_tiers": {"TIER_1": 12, "TIER_2": 12, "TIER_3": 12}},
        "eligibility_semantics": "measured-and-held-out-conjunction; disjoint populations required",
        "canary_semantics": "pre-execution eligibility/runtime/capability check only; excluded from measured statistics",
        "canary_packet_digest": freeze_hash(canary_packet),
        "ordering_rule": "canonical case_id order; no runtime randomization",
        "freeze_a_precedes_canary_execution": True, "canary_cannot_change_frozen_task_difficulty": True,
        "no_route_output_exists_yet": True, "no_measured_result_exists_yet": True,
    }
    manifest = {**payload, "freeze_a_digest": freeze_hash(payload)}
    return case_document, canary_packet, manifest


def write_freeze_a() -> dict:
    case_document, canary_packet, manifest = build_freeze_a()
    CASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    CASES_PATH.write_text(json.dumps(case_document, indent=2, sort_keys=True) + "\n")
    CANARY_PACKET_PATH.write_text(json.dumps(canary_packet, indent=2, sort_keys=True) + "\n")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


if __name__ == "__main__":
    write_freeze_a()
