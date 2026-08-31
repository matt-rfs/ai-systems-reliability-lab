from __future__ import annotations
from .models import CaseEvaluation

def summarize(results: list[CaseEvaluation]) -> dict:
    total=len(results); passed=sum(r.deterministic_pass for r in results); hard=sum(r.hard_gate_failed for r in results); schema=sum(not r.schema_valid for r in results)
    return {"total":total,"passed":passed,"correctness":passed/total if total else 0.0,"hard_gate_failures":hard,"schema_violations":schema}

def release_decision(baseline: list[CaseEvaluation], candidate: list[CaseEvaluation], min_correctness: float=.90, baseline_factual: float | None = None, candidate_factual: float | None = None) -> tuple[bool,list[str]]:
    b=summarize(baseline); c=summarize(candidate); reasons=[]
    if c["schema_violations"]>b["schema_violations"]: reasons.append("new schema violation")
    if c["hard_gate_failures"]>b["hard_gate_failures"]: reasons.append("new hard-gate failure")
    if c["correctness"]<min_correctness: reasons.append(f"correctness below {min_correctness:.0%}")
    if c["correctness"]<b["correctness"]: reasons.append("correctness regressed from baseline")
    if candidate_factual is not None:
        if candidate_factual < .90: reasons.append("factual support below 90%")
        if baseline_factual is not None and candidate_factual < baseline_factual - (1 / c["total"]): reasons.append("factual support declined by more than one case")
    return (not reasons,reasons)
