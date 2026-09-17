"""Local-only V002 canary plumbing; callers must explicitly invoke it."""
from __future__ import annotations
import json, time
from pathlib import Path
from urllib.request import Request, urlopen
from .canary import _r0_record
from .cases import Split, build_case_collection, project_route_input, verifier_config_for_case
from .verifier import verify_runbook
from .v002 import MODEL_TAG, PLAN_SCHEMA, preflight, prepare_v002_attempt, r1, r2

class OllamaTransport:
    endpoint = "http://127.0.0.1:11434/api/chat"
    def __init__(self, opener=urlopen): self.opener=opener; self.raw=[]; self.calls=0
    def chat(self, *, model, system, user, schema, options):
        if model != MODEL_TAG: raise RuntimeError("frozen model tag required")
        body={"model":model,"stream":False,"format":schema,"options":{k:v for k,v in options.items() if k!="stream"},"messages":[{"role":"system","content":system},{"role":"user","content":user}]}
        try:
            req=Request(self.endpoint, data=json.dumps(body).encode(), headers={"Content-Type":"application/json"})
            self.calls += 1
            with self.opener(req, timeout=120) as response: raw=json.loads(response.read())
            self.raw.append(raw)
            value=json.loads(raw["message"]["content"])
        except Exception as error: raise RuntimeError("local Ollama execution failure") from error
        return value

def run_canary(*, attempt: Path, transport, identity: dict) -> Path:
    """Execute only the six V002 canaries; no retry or fallback exists."""
    preflight(runtime_version=identity["runtime_version"],model_tag=identity["model_tag"],ollama_list_id=identity["ollama_list_id"],blob_sha256=identity["blob_sha256"])
    cases=[x for x in build_case_collection() if x.split is Split.CANARY]
    if [x.case_id for x in cases] != [f"L03-C-{i:03d}" for i in range(1,7)]: raise ValueError("frozen canary set required")
    prepare_v002_attempt(attempt)
    records=[]
    for case in cases:
        row={"case_id":case.case_id,"R0":_r0_record(case)}
        for route, fn in (("R1",r1),("R2",r2)):
            started=time.perf_counter()
            calls_before = getattr(transport, "calls", None)
            try:
                outcome=fn(transport,project_route_input(case)); plan=outcome[0] if route=="R2" else outcome
                evaluation=verify_runbook(case.case_id,plan.model_dump(),verifier_config_for_case(case))
                count = getattr(transport, "calls", 0) - calls_before if calls_before is not None else None
                row[route]={"status":"COMPLETED","candidate":plan.model_dump(),"verifier":evaluation.model_dump(),"call_count":{"value":count,"unit":"count"},"latency_ms":round((time.perf_counter()-started)*1000,3)}
            except Exception as error:
                count = getattr(transport, "calls", 0) - calls_before if calls_before is not None else None
                row[route]={"status":"EXECUTION_FAILURE","error":str(error),"call_count":{"value":count,"unit":"count"}}
        records.append(row)
    path=attempt/"canary_execution.json"; path.write_text(json.dumps({"version":"L03-CANARY-V002","records":records,"raw_model_responses":getattr(transport,"raw",[])},indent=2)+"\n"); return path
