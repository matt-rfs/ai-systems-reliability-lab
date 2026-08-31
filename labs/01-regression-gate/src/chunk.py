"""Resumable local execution chunks; keeps the frozen experiment intact under host time limits."""
from __future__ import annotations
import json, sys, os
from pathlib import Path
from .constrained_gateway import OllamaConstrainedGateway
from .gateway import OpenAICompatibleLocalGateway
from .runner import load_cases, run_live
from .semantic import evaluate_factual_support
from .models import ModelOutput

LAB=Path(__file__).parents[1]
OUT=Path(os.getenv('LAB01_EXECUTION_DIR', str(LAB/'results'/'v0.3'/'runs')))

def append(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as file:
        for row in rows: file.write(json.dumps(row)+"\n")

def generate(name: str, start: int, end: int) -> None:
    config=json.loads((LAB/'configs'/f'{name}.json').read_text())
    cases=load_cases(LAB/'data'/'golden_cases.jsonl')[start:end]
    temporary=OUT/f'.{name}-{start}-{end}.jsonl'
    # A small temporary case file avoids changing the frozen golden dataset.
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(''.join(case.model_dump_json()+"\n" for case in cases))
    evaluations,traces=run_live(temporary, LAB/config['prompt'], OllamaConstrainedGateway(), temperature=config['temperature'], max_tokens=200)
    for trace,evaluation in zip(traces,evaluations):
        trace.update({'experiment_id':'lab01-v0.3-qwen2.5-1.5b-2026-08-29','configuration':name,'evaluation':evaluation.model_dump()})
    append(OUT/f'{name}_generation.jsonl',traces)
    temporary.unlink()

def semantic(name: str, start: int, end: int) -> None:
    rows=[json.loads(line) for line in (OUT/f'{name}_generation.jsonl').read_text().splitlines()]
    rows=sorted(rows,key=lambda r:r['case_id'])[start:end]
    cases={case.case_id:case for case in load_cases(LAB/'data'/'golden_cases.jsonl')}
    gateway=OpenAICompatibleLocalGateway(); output=[]
    for row in rows:
        if row['validation_result']!='valid': output.append({'case_id':row['case_id'],'available':False,'reason':'structured output failed schema validation'}); continue
        try:
            judge=evaluate_factual_support(cases[row['case_id']],ModelOutput.model_validate(row['parsed_structured_output']),gateway)
            output.append({'case_id':row['case_id'],'available':True,'supported':judge.supported,'unsupported_claims':judge.unsupported_claims,'judge_provider':gateway.provider,'judge_model':judge.judge_model,'latency_ms':judge.latency_ms,'input_tokens':judge.input_tokens,'output_tokens':judge.output_tokens,'cost_usd':0.0,'raw_judge_output':judge.raw_judge_output})
        except Exception as exc:
            output.append({'case_id':row['case_id'],'available':False,'reason':f'local judge response unavailable: {exc}'})
    append(OUT/f'{name}_semantic.jsonl',output)

if __name__=='__main__':
    mode,name,start,end=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
    {'generate':generate,'semantic':semantic}[mode](name,start,end)
