import json
from pathlib import Path
import pytest
import cost_quality_router.live_v002 as live
from cost_quality_router.live_v002 import OllamaTransport
from cost_quality_router.v002 import MODEL_TAG, PLAN_SCHEMA, R1_PROMPT, generation
class Response:
 def __init__(self,p): self.p=p
 def read(self): return json.dumps(self.p).encode()
 def __enter__(self): return self
 def __exit__(self,*x): return False
def test_transport_binds_local_contract_without_network():
 seen=[]
 def opener(req,timeout): seen.append((req,timeout)); return Response({"message":{"content":json.dumps({"steps":[],"requires_human_authority":False,"policy_citations":[]})}})
 t=OllamaTransport(opener); assert t.chat(model=MODEL_TAG,system=R1_PROMPT,user="{}",schema=PLAN_SCHEMA,options=generation())["steps"]==[]
 body=json.loads(seen[0][0].data); assert seen[0][0].full_url.endswith("/api/chat") and body["stream"] is False and body["model"]==MODEL_TAG and body["format"]==PLAN_SCHEMA
 assert body["messages"] == [{"role":"system","content":R1_PROMPT},{"role":"user","content":"{}"}] and body["options"] == {"temperature":0,"seed":0,"num_predict":256}

def test_transport_counts_attempted_http_call_and_never_retries():
 def failing(req,timeout): raise OSError("offline fake")
 t=OllamaTransport(failing)
 import pytest
 with pytest.raises(RuntimeError): t.chat(model=MODEL_TAG,system="s",user="u",schema=PLAN_SCHEMA,options=generation())
 assert t.calls == 1 and t.raw == []

def test_malformed_content_retains_outer_raw_response():
 t=OllamaTransport(lambda req,timeout: Response({"message":{"content":"not-json"}}))
 with pytest.raises(RuntimeError): t.chat(model=MODEL_TAG,system="s",user="u",schema=PLAN_SCHEMA,options=generation())
 assert t.calls == 1 and len(t.raw) == 1

class Scripted:
 def __init__(self, fail_at): self.calls=0; self.raw=[]; self.fail_at=fail_at
 def chat(self, **kwargs):
  self.calls+=1
  if self.calls == self.fail_at: raise RuntimeError("scripted")
  self.raw.append({"call":self.calls})
  phase=(self.calls-1)%4
  if phase == 1: return {"status":"STANDARD","action_value":1,"approval_threshold":50,"requires_human_authority":False}
  return {"steps":["assess_request"],"requires_human_authority":False,"policy_citations":["POL-VERIFY"]}

@pytest.mark.parametrize("fail_at,route,expected", [(1,"R1",1),(2,"R2",1),(3,"R2",2),(4,"R2",3)])
def test_runner_reports_actual_failed_route_call_delta(tmp_path, monkeypatch, fail_at, route, expected):
 monkeypatch.setattr(live, "prepare_v002_attempt", lambda p: p.mkdir(parents=True))
 artifact=live.run_canary(attempt=tmp_path/"attempt-test",transport=Scripted(fail_at),identity={"runtime_version":"0.33.0","model_tag":MODEL_TAG,"ollama_list_id":"65ec06548149","blob_sha256":"183715c435899236895da3869489cc30ac241476b4971a20285b1a462818a5b4"})
 record=json.loads(artifact.read_text())["records"][0][route]
 assert record["status"] == "EXECUTION_FAILURE" and record["call_count"] == {"value":expected,"unit":"count"}
 assert "candidate" not in record and "verifier" not in record
