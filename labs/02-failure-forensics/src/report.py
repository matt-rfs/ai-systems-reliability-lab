from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from forensic import localize
from pipeline import run_case


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def execute(lab_root: Path) -> dict[str, Any]:
    cases = load_jsonl(lab_root / "data/cases.jsonl")
    expected = {row["case_id"]: row for row in load_jsonl(lab_root / "data/expected_failures.jsonl")}
    all_traces = []
    findings = []
    for case in cases:
        traces = run_case(case, run_id=f"frozen-{case['case_id']}")
        finding = localize(traces)
        all_traces.extend([trace.model_dump() for trace in traces])
        findings.append(finding.model_dump())
    localization_correct = sum(f["first_failure_stage"] == expected[f["case_id"]]["expected_first_failure_stage"] for f in findings)
    type_correct = sum(f["failure_type"] == expected[f["case_id"]]["expected_failure_type"] for f in findings)
    origin_symptom_correct = sum(
        f["propagation_detected"] == expected[f["case_id"]]["expected_propagation"]
        and f["symptom_stages"] == expected[f["case_id"]]["expected_symptom_stages"]
        and f["contained"] == expected[f["case_id"]]["expected_execution_stop"]
        for f in findings
    )
    regression_case = next(case for case in cases if case["case_id"] == "evidence-01")
    before = localize(run_case(regression_case, correction=False, run_id="regression-before"))
    after = localize(run_case(regression_case, correction=True, run_id="regression-after"))
    latency_ms = sum(t["latency_ms"] for t in all_traces)
    summary = {
        "case_count": len(cases), "trace_count": len(all_traces), "stage_count": 5,
        "failure_localization_accuracy": f"{localization_correct}/{len(cases)}",
        "failure_type_accuracy": f"{type_correct}/{len(cases)}",
        "origin_vs_propagation_accuracy": f"{origin_symptom_correct}/{len(cases)}",
        "trace_completeness": f"{len(all_traces)}/{len(cases) * 5}",
        "regression_fixture": {"case_id": "evidence-01", "before_fix": before.model_dump(), "after_fix": after.model_dump(), "verified": not before.clean_run and after.clean_run},
        "propagation_case_count": sum(f["propagation_detected"] for f in findings),
        "contained_case_count": sum(f["contained"] for f in findings),
        "no_downstream_propagation_case_count": sum(
            not f["propagation_detected"] and not f["contained"] for f in findings
        ),
        "runtime": "Python deterministic fixture", "model": None, "token_counts": "unavailable; no model invoked",
        "api_service_cost_usd": 0.0, "total_measured_stage_latency_ms": round(latency_ms, 3),
        "real_inference": "not used; deterministic forensics core is the measured result",
        "findings": findings,
    }
    results = lab_root / "results"
    results.mkdir(exist_ok=True)
    (results / "stage_traces.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in all_traces))
    (results / "measured_results.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
