import json
from pathlib import Path
import pytest
from cost_quality_router.cases import build_case_collection, project_route_input
from cost_quality_router.freeze import freeze_hash
from cost_quality_router.v002 import (MODEL_BLOB_SHA256, MODEL_TAG, R1_PROMPT, S1_PROMPT, S2_PROMPT, S3_PROMPT, preflight, r1, r2, v002_contract, v002_freeze)

class Fake:
    def __init__(self, responses): self.responses, self.calls = list(responses), []
    def chat(self, **kwargs): self.calls.append(kwargs); return self.responses.pop(0)
PLAN={"steps":["assess_request"],"requires_human_authority":False,"policy_citations":["POL-VERIFY"]}
STAGE={"status":"STANDARD","action_value":1,"approval_threshold":50,"requires_human_authority":False}
def route_input(): return project_route_input(next(x for x in build_case_collection() if x.case_id == "L03-C-001"))
def test_v002_preserves_authority_and_contract_mutations_move_identity():
    f=v002_freeze(); assert f["v001_ancestor_digest"] == "c0b8eed27670f215a5ca42ee48ed1b9b45735f1c63910301816de8ff9d550cb1"; assert f["counts"]["canary_total"] == 6
    changed={**v002_contract(), "retry":"ONE"}; assert freeze_hash(changed) != freeze_hash(v002_contract())
def test_preflight_fails_closed_and_r1_is_one_visible_input_call():
    with pytest.raises(RuntimeError): preflight(runtime_version="x",model_tag=MODEL_TAG,ollama_list_id="65ec06548149",blob_sha256=MODEL_BLOB_SHA256)
    fake=Fake([PLAN]); r1(fake, route_input()); assert len(fake.calls)==1 and fake.calls[0]["system"]==R1_PROMPT and fake.calls[0]["model"]==MODEL_TAG
    assert "case_id" not in fake.calls[0]["user"] and fake.calls[0]["options"]=={"temperature":0,"seed":0,"num_predict":256,"stream":False}
def test_r2_has_three_bound_calls_and_stops_on_malformed_stage():
    fake=Fake([STAGE,PLAN,PLAN]); final,_=r2(fake,route_input()); assert final.steps==["assess_request"] and [x["system"] for x in fake.calls]==[S1_PROMPT,S2_PROMPT,S3_PROMPT]
    stage2=json.loads(fake.calls[1]["user"]); assert "policy_facts" in stage2 and "case_id" not in fake.calls[1]["user"]
    bad=Fake([{}]);
    with pytest.raises(Exception): r2(bad,route_input())
    assert len(bad.calls)==1

@pytest.mark.parametrize("changed", [
    {"steps": [], "requires_human_authority": False, "policy_citations": ["POL-VERIFY"]},
    {"steps": ["assess_request", "review_policy"], "requires_human_authority": False, "policy_citations": ["POL-VERIFY"]},
    {"steps": ["review_policy", "assess_request"], "requires_human_authority": False, "policy_citations": ["POL-VERIFY"]},
    {"steps": ["assess_request"], "requires_human_authority": True, "policy_citations": ["POL-VERIFY"]},
    {"steps": ["assess_request"], "requires_human_authority": False, "policy_citations": []},
])
def test_r2_stage3_schema_valid_mutation_fails_closed_without_extra_call(changed):
    fake = Fake([STAGE, PLAN, changed])
    with pytest.raises(ValueError, match="preserve"):
        r2(fake, route_input())
    assert len(fake.calls) == 3
