from __future__ import annotations
import json,time
from pathlib import Path
from urllib.request import Request,urlopen
from .gateway import ModelCall,LocalInferenceUnavailable

class OllamaConstrainedGateway:
    provider="ollama_native_constrained"
    def __init__(self, model="qwen2.5:1.5b", schema_path: str|Path|None=None):
        self.model=model; self.schema=json.loads(Path(schema_path or Path(__file__).parents[1]/"configs/model_output_schema_flat.json").read_text())
    def complete_json(self, system_prompt, user_payload, *, temperature, max_tokens):
        body={"model":self.model,"stream":False,"format":self.schema,"options":{"temperature":temperature,"num_predict":max_tokens},"messages":[{"role":"system","content":system_prompt},{"role":"user","content":json.dumps(user_payload,sort_keys=True)}]}
        started=time.perf_counter()
        try:
            req=Request("http://127.0.0.1:11434/api/chat",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
            raw=json.loads(urlopen(req,timeout=120).read()); output=json.loads(raw["message"]["content"])
        except Exception as exc: raise LocalInferenceUnavailable(str(exc)) from exc
        return ModelCall(output=output,provider=self.provider,model=self.model,input_tokens=raw.get("prompt_eval_count"),output_tokens=raw.get("eval_count"),cost_usd=0.0,latency_ms=round((time.perf_counter()-started)*1000))
