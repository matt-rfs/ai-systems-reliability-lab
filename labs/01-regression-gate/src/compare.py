from __future__ import annotations
from .models import CaseEvaluation

def classify_changes(baseline: list[CaseEvaluation], candidate: list[CaseEvaluation]) -> dict[str,list[str]]:
    b={x.case_id:x.deterministic_pass for x in baseline}; c={x.case_id:x.deterministic_pass for x in candidate}
    out={"unchanged_pass":[],"unchanged_fail":[],"fixed":[],"regression":[]}
    for cid in sorted(b):
        if b[cid] and c[cid]: out["unchanged_pass"].append(cid)
        elif (not b[cid]) and (not c[cid]): out["unchanged_fail"].append(cid)
        elif (not b[cid]) and c[cid]: out["fixed"].append(cid)
        else: out["regression"].append(cid)
    return out
