"""Freeze A V002 execution authority.  Adapters require an injected transport."""
from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, ValidationError

from .cases import RouteInput
from .freeze import freeze_hash
from .models import RunbookPlan

LAB_ROOT = Path(__file__).resolve().parents[2]
V001 = json.loads((LAB_ROOT / "config" / "freeze-a-v001.json").read_text())
RUNTIME_VERSION, MODEL_TAG, OLLAMA_LIST_ID = "0.33.0", "qwen2.5:1.5b", "65ec06548149"
MODEL_BLOB_SHA256 = "183715c435899236895da3869489cc30ac241476b4971a20285b1a462818a5b4"
R1_PROMPT = "Produce one operational runbook from the supplied synthetic request and policy facts. Use only supplied policy IDs and allowed steps. Return JSON only, conforming exactly to the requested schema. Do not invent policy facts, steps, or human-authority requirements."
S1_PROMPT = "Interpret the supplied synthetic request and policy facts. Return JSON only. Extract the status, action value, approval threshold when stated, and required human authority. Do not add facts not present in the input."
S2_PROMPT = "Create a runbook draft using only the supplied request interpretation, policy facts, and allowed steps. Return JSON only. Ground every policy citation in the supplied policy facts. Do not invent steps, policies, or authority requirements."
S3_PROMPT = "Return the supplied runbook draft as one final JSON runbook plan. Preserve its steps, human-authority flag, and policy citations. Do not add, remove, reorder, or invent content."
PLAN_SCHEMA = {"type":"object", "additionalProperties":False, "required":["steps","requires_human_authority","policy_citations"], "properties":{"steps":{"type":"array","items":{"type":"string"}}, "requires_human_authority":{"type":"boolean"}, "policy_citations":{"type":"array","items":{"type":"string"}}}}

class Stage1(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    action_value: int
    approval_threshold: int | None
    requires_human_authority: bool

class Transport(Protocol):
    def chat(self, *, model: str, system: str, user: str, schema: dict, options: dict) -> object: ...

def canonical(value: object) -> str: return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
def generation() -> dict: return {"temperature": 0, "seed": 0, "num_predict": 256, "stream": False}
def route_input_payload(value: RouteInput) -> dict: return value.model_dump(mode="json")
def preflight(*, runtime_version: str, model_tag: str, ollama_list_id: str, blob_sha256: str) -> None:
    if (runtime_version, model_tag, ollama_list_id, blob_sha256) != (RUNTIME_VERSION, MODEL_TAG, OLLAMA_LIST_ID, MODEL_BLOB_SHA256):
        raise RuntimeError("frozen local runtime/model identity mismatch")
def parse_plan(value: object) -> RunbookPlan: return RunbookPlan.model_validate(value)
def _call(transport: Transport, prompt: str, payload: dict, schema: dict) -> object:
    return transport.chat(model=MODEL_TAG, system=prompt, user=canonical(payload), schema=schema, options=generation())

def r1(transport: Transport, value: RouteInput) -> RunbookPlan:
    return parse_plan(_call(transport, R1_PROMPT, route_input_payload(value), PLAN_SCHEMA))

def r2(transport: Transport, value: RouteInput) -> tuple[RunbookPlan, tuple[object, object, object]]:
    raw1 = _call(transport, S1_PROMPT, route_input_payload(value), Stage1.model_json_schema())
    stage1 = Stage1.model_validate(raw1)
    stage2_input = {"stage_1": stage1.model_dump(mode="json"), "policy_facts": [x.model_dump(mode="json") for x in value.policy_facts], "allowed_steps": list(value.allowed_steps), "schema_version": value.schema_version}
    raw2 = _call(transport, S2_PROMPT, stage2_input, PLAN_SCHEMA)
    draft = parse_plan(raw2)
    raw3 = _call(transport, S3_PROMPT, draft.model_dump(mode="json"), PLAN_SCHEMA)
    final = parse_plan(raw3)
    if final != draft:
        raise ValueError("R2 Stage 3 must preserve the Stage 2 draft exactly")
    return final, (raw1, raw2, raw3)

def v002_contract() -> dict:
    return {"version":"ROUTE-EXECUTION-CONTRACT-V002", "runtime":{"endpoint":"local Ollama /api/chat only","version":RUNTIME_VERSION,"model_tag":MODEL_TAG,"ollama_list_id":OLLAMA_LIST_ID,"model_blob_sha256":MODEL_BLOB_SHA256}, "generation":generation(), "retry":"NONE", "fallback":"NONE", "r1":{"prompt":R1_PROMPT,"inputs":["RouteInput"],"schema":PLAN_SCHEMA,"calls":1}, "r2":{"stages":[{"id":"interpret_route_input","prompt":S1_PROMPT,"inputs":["RouteInput"],"schema":Stage1.model_json_schema()},{"id":"draft_runbook","prompt":S2_PROMPT,"inputs":["stage_1","RouteInput.policy_facts","RouteInput.allowed_steps","RouteInput.schema_version"],"schema":PLAN_SCHEMA},{"id":"finalize_runbook_plan","prompt":S3_PROMPT,"inputs":["stage_2"],"schema":PLAN_SCHEMA}]}}
def v002_freeze() -> dict:
    return {"freeze_version":"FREEZE-A-V002", "v001_ancestor_digest":V001["freeze_a_digest"], "supersession_reason":"V001 lacked reproducible R1/R2 execution authority", "v001_historical":True, "attempt_01_historical":True, "no_r1_r2_output_before_v002":True, "restarts_canary_authority":True, "preserved_v001_identities":{k:V001[k] for k in ("case_collection_digest","policy_universe_digest","verifier_semantics_digest","verifier_config_digest","quality_floor_digest","route_input_projection_digest","r0_applicability_surface_digest")}, "r0_route_digest":V001["route_definition_digests"]["R0"], "counts":V001["counts"], "canary":{"restart_required":True,"case_reuse":True,"r0_rerun":True,"case_ids":[f"L03-C-{i:03d}" for i in range(1,7)],"result_namespace":"results/canary-v002/"}, "route_execution_contract_digest":freeze_hash(v002_contract())}

def prepare_v002_attempt(path: Path) -> None:
    """Create one new V002 attempt directory; historical V001 paths are rejected."""
    root = (LAB_ROOT / "results" / "canary-v002").resolve()
    target = path.resolve()
    if target.parent != root or not target.name.startswith("attempt-") or target.exists():
        raise ValueError("V002 attempts must be new, isolated canary-v002/attempt-* directories")
    target.mkdir(parents=True)
