"""Run Lab 01 against a local model and produce an auditable result package."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from .compare import classify_changes
from .gateway import LocalInferenceUnavailable, OpenAICompatibleLocalGateway
from .gate import release_decision, summarize
from .runner import load_cases, run_live
from .semantic import evaluate_factual_support
from .models import CaseEvaluation


LAB = Path(__file__).parents[1]
RESULTS = LAB / "results" / "v0.3"

def _write_svg(path: Path, status: str, rows: list[tuple[str, str]], decision: str) -> None:
    height = 170 + 32 * len(rows)
    rendered = "".join(f'<text x="52" y="{130 + i * 32}" font-family="Arial" font-size="18" fill="#182230">{label}</text><text x="665" y="{130 + i * 32}" text-anchor="end" font-family="Arial" font-size="18" font-weight="700" fill="#182230">{value}</text>' for i, (label, value) in enumerate(rows))
    color = "#087f5b" if decision == "PASS" else "#c92a2a"
    path.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" viewBox="0 0 720 {height}"><rect width="720" height="{height}" fill="#f8f9fa"/><rect x="24" y="24" width="672" height="{height - 48}" rx="16" fill="white" stroke="#d9e1e8"/><text x="52" y="66" font-family="Arial" font-size="15" font-weight="700" fill="#52606d">AI SYSTEMS RELIABILITY LAB · LAB 01</text><text x="52" y="98" font-family="Arial" font-size="26" font-weight="700" fill="#182230">MODEL REGRESSION GATE</text>{rendered}<rect x="52" y="{height - 92}" width="616" height="44" rx="8" fill="{color}"/><text x="360" y="{height - 63}" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700" fill="white">{status}: {decision}</text></svg>''')

def _write_markdown(path: Path, payload: dict) -> None:
    if payload["status"] != "completed":
        path.write_text("# Lab 01 V0.2 — Experiment Execution Record\n\n## Status\n\n**BLOCKED — no local/free inference route was available.**\n\nNo real model outputs, quality metrics, regressions, or release decision were produced. This is not a failed model release; it is an incomplete experiment. The V0.1 fixture validation remains an evaluator self-test only.\n\n## Evidence\n\n- Checked local OpenAI-compatible endpoint: `" + payload["endpoint"] + "`\n- Result: `" + payload["reason"] + "`\n- Spend: **$0.00**\n- No cloud, paid API, subscription, or external publication was used.\n")
        return
    b, c = payload["baseline"], payload["candidate"]
    path.write_text(f"# Lab 01 V0.2 — Real Model Experiment\n\n**Release decision: {payload['release']['decision']}**\n\n- Provider/model: `{payload['provider']}` / `{payload['model']}`\n- Cases: 30 per configuration\n- Spend: **${payload['total_cost_usd']:.2f}**\n- Baseline deterministic correctness: **{b['summary']['correctness']:.1%}**\n- Candidate deterministic correctness: **{c['summary']['correctness']:.1%}**\n- Baseline factual support: **{b['factual_support_rate']:.1%}**\n- Candidate factual support: **{c['factual_support_rate']:.1%}**\n- New regressions: **{len(payload['changes']['regression'])}**\n- Fixed cases: **{len(payload['changes']['fixed'])}**\n\n## Gate reasons\n\n" + "\n".join(f"- {reason}" for reason in payload["release"]["reasons"]) + "\n")

def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    gateway = OpenAICompatibleLocalGateway()
    payload = {"lab_version": "0.2", "executed_at": datetime.now(timezone.utc).isoformat(), "provider": gateway.provider, "endpoint": gateway.base_url, "model": gateway.model or None, "cost_policy": "local-only; $0.00", "status": "blocked_no_local_inference"}
    if not gateway.available():
        payload["reason"] = "No reachable local OpenAI-compatible model server."
        (RESULTS / "real_experiment_results.json").write_text(json.dumps(payload, indent=2) + "\n")
        _write_markdown(RESULTS / "decision_record.md", payload)
        _write_svg(RESULTS / "result_card.svg", "EXPERIMENT", [("Real model result", "NOT AVAILABLE"), ("Local endpoint", gateway.base_url), ("Spend", "$0.00"), ("Fixture claims", "SELF-TEST ONLY")], "BLOCKED")
        return 2
    try:
        configurations = {}
        for name in ("baseline", "candidate"):
            config = json.loads((LAB / "configs" / f"{name}.json").read_text())
            evaluations, traces = run_live(LAB / "data" / "golden_cases.jsonl", LAB / config["prompt"], gateway, temperature=config["temperature"], max_tokens=config["max_tokens"])
            factual, semantic_results = [], []
            for case, trace in zip(load_cases(LAB / "data" / "golden_cases.jsonl"), traces):
                from .models import ModelOutput
                if trace["validation_result"] != "valid":
                    semantic_results.append({"case_id": case.case_id, "available": False, "reason": "structured output failed schema validation"})
                    continue
                judgment = evaluate_factual_support(case, ModelOutput.model_validate(trace["parsed_structured_output"]), gateway)
                factual.append(judgment.supported)
                semantic_results.append({"case_id": case.case_id, "available": True, "supported": judgment.supported, "unsupported_claims": judgment.unsupported_claims, "judge_provider": gateway.provider, "judge_model": judgment.judge_model, "latency_ms": judgment.latency_ms, "input_tokens": judgment.input_tokens, "output_tokens": judgment.output_tokens, "cost_usd": 0.0, "raw_judge_output": judgment.raw_judge_output})
            configurations[name] = {"config": config, "summary": summarize(evaluations), "factual_support_rate": sum(factual) / len(factual) if factual else None, "factual_support_evaluated_cases": len(factual), "evaluations": [item.model_dump() for item in evaluations], "traces": traces, "semantic_factual_support": semantic_results}
    except LocalInferenceUnavailable as exc:
        payload["reason"] = str(exc)
        (RESULTS / "real_experiment_results.json").write_text(json.dumps(payload, indent=2) + "\n")
        _write_markdown(RESULTS / "decision_record.md", payload)
        _write_svg(RESULTS / "result_card.svg", "EXPERIMENT", [("Real model result", "INTERRUPTED"), ("Reason", "LOCAL INFERENCE UNAVAILABLE"), ("Spend", "$0.00"), ("Fixture claims", "SELF-TEST ONLY")], "BLOCKED")
        return 2
    baseline_evaluations = [CaseEvaluation.model_validate(x) for x in configurations["baseline"]["evaluations"]]
    candidate_evaluations = [CaseEvaluation.model_validate(x) for x in configurations["candidate"]["evaluations"]]
    changes = classify_changes(baseline_evaluations, candidate_evaluations)
    ok, reasons = release_decision(baseline_evaluations, candidate_evaluations, baseline_factual=configurations["baseline"]["factual_support_rate"], candidate_factual=configurations["candidate"]["factual_support_rate"])
    payload.update({"status": "completed", "experiment_id": "lab01-v0.3-qwen2.5-1.5b-2026-08-29", "baseline": configurations["baseline"], "candidate": configurations["candidate"], "changes": changes, "total_cost_usd": sum(t["cost_usd"] for configuration in configurations.values() for t in configuration["traces"]), "release": {"decision": "PASS" if ok else "FAIL", "reasons": reasons}})
    (RESULTS / "real_experiment_results.json").write_text(json.dumps(payload, indent=2) + "\n")
    _write_markdown(RESULTS / "decision_record.md", payload)
    _write_svg(RESULTS / "result_card.svg", "RELEASE DECISION", [("Cases evaluated", "30 × 2"), ("Baseline correctness", f"{payload['baseline']['summary']['correctness']:.1%}"), ("Candidate correctness", f"{payload['candidate']['summary']['correctness']:.1%}"), ("New regressions", str(len(changes['regression']))), ("Spend", "$0.00")], payload["release"]["decision"])
    return 0

if __name__ == "__main__":
    sys.exit(main())
