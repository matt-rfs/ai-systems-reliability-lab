import json

from cost_quality_router.canary import execute_canary


def test_canary_executes_only_the_frozen_cases_and_preserves_unavailable_model_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr("cost_quality_router.canary.probe_ollama", lambda: (False, "test local runtime unavailable"))
    artifact = execute_canary(tmp_path / "canary")
    payload = json.loads(artifact.read_text())

    assert payload["case_ids"] == [f"L03-C-{index:03d}" for index in range(1, 7)]
    assert payload["scope"] == "eligibility canary only; excluded from measured statistics"
    assert payload["route_dispositions"] == {"R0": "ELIGIBLE", "R1": "RUNTIME_UNUSABLE", "R2": "RUNTIME_UNUSABLE"}
    assert all(record["case_pass"] and not record["hard_gate_failures"] for record in payload["records"]["R0"])
    assert all(record["burden"]["human_intervention"]["unit"] == "count" for records in payload["records"].values() for record in records)
    for route_id in ("R1", "R2"):
        assert all(record["execution_status"] == "RUNTIME_UNUSABLE" and record["candidate_output"] is None
                   for record in payload["records"][route_id])
