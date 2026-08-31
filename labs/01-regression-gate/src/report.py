from __future__ import annotations
from .gate import summarize, release_decision
from .compare import classify_changes

def markdown_report(baseline, candidate) -> str:
    b=summarize(baseline); c=summarize(candidate); changes=classify_changes(baseline,candidate); ok,reasons=release_decision(baseline,candidate)
    lines=["# Model Regression Gate — Fixture Validation Report","",f"**Release decision: {'PASS' if ok else 'FAIL'}**","",f"- Cases: {b['total']}",f"- Baseline correctness: {b['correctness']:.1%}",f"- Candidate correctness: {c['correctness']:.1%}",f"- New regressions: {len(changes['regression'])}",f"- Fixed cases: {len(changes['fixed'])}",f"- Candidate hard-gate failures: {c['hard_gate_failures']}",""]
    if reasons: lines += ["## Gate reasons"]+[f"- {r}" for r in reasons]+[""]
    lines += ["## Regressed cases"]+[f"- {cid}" for cid in changes['regression']]
    return "\n".join(lines)+"\n"
