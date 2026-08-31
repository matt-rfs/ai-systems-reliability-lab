from pathlib import Path
from src.runner import load_cases, run_fixture
from src.gate import summarize, release_decision
from src.compare import classify_changes
from src.models import ModelOutput
from src.gateway import OpenAICompatibleLocalGateway
from pydantic import ValidationError
import pytest

LAB=Path(__file__).parents[1]

def test_dataset_has_30_unique_cases():
    cases=load_cases(LAB/'data/golden_cases.jsonl')
    assert len(cases)==30
    assert len({c.case_id for c in cases})==30

def test_dataset_policy_references_exist():
    for c in load_cases(LAB/'data/golden_cases.jsonl'):
        assert set(c.required_evidence_ids).issubset(set(c.policy_facts))

def test_schema_rejects_missing_fields():
    with pytest.raises(ValidationError): ModelOutput.model_validate({'request_type':'billing'})

def test_baseline_passes_all_cases():
    r=run_fixture(LAB/'data/golden_cases.jsonl',LAB/'data/baseline_outputs.jsonl')
    s=summarize(r)
    assert s['passed']==30 and s['hard_gate_failures']==0 and s['schema_violations']==0

def test_candidate_regressions_are_detected():
    b=run_fixture(LAB/'data/golden_cases.jsonl',LAB/'data/baseline_outputs.jsonl')
    c=run_fixture(LAB/'data/golden_cases.jsonl',LAB/'data/candidate_outputs.jsonl')
    changes=classify_changes(b,c)
    assert set(changes['regression'])=={'C01','C12','C16','C30'}

def test_candidate_release_is_blocked():
    b=run_fixture(LAB/'data/golden_cases.jsonl',LAB/'data/baseline_outputs.jsonl')
    c=run_fixture(LAB/'data/golden_cases.jsonl',LAB/'data/candidate_outputs.jsonl')
    ok,reasons=release_decision(b,c)
    assert not ok
    assert 'new hard-gate failure' in reasons
    assert 'new schema violation' in reasons

def test_known_bad_mutation_fails_gate():
    b=run_fixture(LAB/'data/golden_cases.jsonl',LAB/'data/baseline_outputs.jsonl')
    k=run_fixture(LAB/'data/golden_cases.jsonl',LAB/'data/known_bad_outputs.jsonl')
    ok,reasons=release_decision(b,k)
    assert not ok
    assert 'new hard-gate failure' in reasons

def test_local_gateway_rejects_non_local_endpoint():
    with pytest.raises(ValueError):
        OpenAICompatibleLocalGateway(base_url='https://example.com/v1', model='not-used')

def test_factual_support_gate_blocks_material_decline():
    b=run_fixture(LAB/'data/golden_cases.jsonl',LAB/'data/baseline_outputs.jsonl')
    c=run_fixture(LAB/'data/golden_cases.jsonl',LAB/'data/baseline_outputs.jsonl')
    ok,reasons=release_decision(b,c,baseline_factual=1.0,candidate_factual=.90)
    assert not ok
    assert 'factual support declined by more than one case' in reasons
