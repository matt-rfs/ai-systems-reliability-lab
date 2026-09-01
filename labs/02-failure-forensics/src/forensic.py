from __future__ import annotations

from models import Finding, StageTrace


def localize(traces: list[StageTrace]) -> Finding:
    ordered = sorted(traces, key=lambda item: item.stage_index)
    if [t.stage_index for t in ordered] != list(range(1, len(ordered) + 1)):
        raise ValueError("trace stage ordering is invalid")
    if len({t.run_id for t in ordered}) != 1:
        raise ValueError("trace run IDs are inconsistent")
    failed = [t for t in ordered if not t.validation_pass]
    if not failed:
        return Finding(case_id=ordered[0].case_id, first_failure_stage=None, failure_type=None,
                       clean_run=True)
    root = failed[0]
    propagated = [t.stage for t in ordered[ordered.index(root) + 1:]
                  if t.output.get("propagated_from") == root.stage and not t.validation_pass]
    contained = any(t.status == "blocked" for t in ordered[ordered.index(root) + 1:])
    return Finding(case_id=root.case_id, first_failure_stage=root.stage, failure_type=root.failure_type,
                   symptom_stages=propagated, propagation_detected=bool(propagated),
                   contained=contained, clean_run=False)
