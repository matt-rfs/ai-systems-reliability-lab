from __future__ import annotations
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from pydantic import ValidationError
from .models import GoldenCase, ModelOutput, CaseEvaluation
from .evaluators import evaluate_case
from .gateway import OpenAICompatibleLocalGateway, ModelCall

def load_cases(path: str|Path) -> list[GoldenCase]:
    return [GoldenCase.model_validate_json(line) for line in Path(path).read_text().splitlines() if line.strip()]

def load_outputs(path: str|Path) -> dict[str, dict]:
    rows={}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            row=json.loads(line); rows[row["case_id"]]=row["output"]
    return rows

def run_fixture(cases_path: str|Path, outputs_path: str|Path) -> list[CaseEvaluation]:
    cases=load_cases(cases_path); outputs=load_outputs(outputs_path); results=[]
    for case in cases:
        raw=outputs.get(case.case_id)
        if raw is None:
            results.append(CaseEvaluation(case_id=case.case_id, schema_valid=False, checks=[])); continue
        try:
            out=ModelOutput.model_validate(raw)
            results.append(evaluate_case(case,out))
        except ValidationError:
            results.append(CaseEvaluation(case_id=case.case_id, schema_valid=False, checks=[]))
    return results

def run_live(cases_path: str|Path, prompt_path: str|Path, gateway: OpenAICompatibleLocalGateway, *, temperature: float, max_tokens: int) -> tuple[list[CaseEvaluation], list[dict]]:
    """Run a configuration and retain enough trace data to reproduce its measured result."""
    prompt = Path(prompt_path).read_text()
    prompt_sha256 = hashlib.sha256(prompt.encode()).hexdigest()
    evaluations, traces = [], []
    for case in load_cases(cases_path):
        call: ModelCall = gateway.complete_json(prompt, case.model_dump(mode="json"), temperature=temperature, max_tokens=max_tokens)
        try:
            output = ModelOutput.model_validate(call.output)
            evaluation = evaluate_case(case, output)
            output_json = output.model_dump(mode="json")
        except ValidationError:
            evaluation = CaseEvaluation(case_id=case.case_id, schema_valid=False, checks=[])
            output_json = call.output
        evaluations.append(evaluation)
        traces.append({"case_id": case.case_id, "timestamp": datetime.now(timezone.utc).isoformat(), "raw_model_output": call.output, "parsed_structured_output": output_json if evaluation.schema_valid else None, "validation_result": "valid" if evaluation.schema_valid else "schema_invalid", "provider": call.provider, "model": call.model, "prompt_sha256": prompt_sha256, "temperature": temperature, "input_tokens": call.input_tokens, "output_tokens": call.output_tokens, "total_tokens": (call.input_tokens or 0) + (call.output_tokens or 0) if call.input_tokens is not None and call.output_tokens is not None else None, "cost_usd": call.cost_usd, "latency_ms": call.latency_ms})
    return evaluations, traces
