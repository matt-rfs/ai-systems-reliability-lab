"""Behavioral coverage of the frozen Slice 2 gate and worker clarification."""

from dataclasses import FrozenInstanceError, replace
import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from assignment_ledger import (
    Assignment, AssignmentLedger, Authorization, AuthorizationDenied,
    EvidenceRef, Verification, VerificationDenied, VerificationMethod,
    VerificationResult, VerificationSubject,
)


CRITERIA = ("fixture output satisfies frozen checks", "no policy violations")
SUBJECT = VerificationSubject("SHA256", "a" * 64)
EVIDENCE = EvidenceRef("test-results/frozen-checks.json", "b" * 64)


def ledger_with_attempt(tmp_path, *, worker_id="worker-1", requirements=CRITERIA):
    ledger = AssignmentLedger(tmp_path)
    ledger.create_assignment(Assignment("assignment-1", "inspect fixture", frozenset({"read:fixture"}),
                                        ("local only",), ("report",), requirements))
    ledger.create_authorization(Authorization("authorization-1", "approved fixture", "GOV-001",
                                              frozenset({"read:fixture"}), ("local only",),
                                              "2026-09-14T00:00:00+00:00", "governance"))
    assert ledger.execute("assignment-1", "authorization-1", lambda request: "completed",
                          attempt_id="attempt-1", worker_id=worker_id) == "completed"
    return ledger


def verification(**changes):
    values = dict(verification_id="verification-1", assignment_id="assignment-1", attempt_id="attempt-1",
                  subject=SUBJECT, verifier="verifier-1", criteria=CRITERIA, evidence_refs=(EVIDENCE,),
                  method=VerificationMethod.DETERMINISTIC, result=VerificationResult.PASS,
                  created_at="2026-10-03T12:00:00+00:00")
    return Verification(**{**values, **changes})


def assert_no_verification(ledger):
    assert list((ledger.root / "verifications").iterdir()) == []
    with pytest.raises(FileNotFoundError):
        ledger.verification("verification-1")


def test_gate_01_completed_attempt_is_not_verified(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    assert_no_verification(AssignmentLedger(tmp_path))
    assert "result" not in ledger.attempt("attempt-1")


def test_gate_02_valid_relationships_are_durable(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    proposed = verification()
    ledger.create_verification(proposed)
    persisted = AssignmentLedger(tmp_path).verification("verification-1")
    assert persisted == proposed
    assert (persisted.assignment_id, persisted.attempt_id) == ("assignment-1", "attempt-1")
    assert persisted.created_at == "2026-10-03T12:00:00+00:00"


@pytest.mark.parametrize("changes", [{"assignment_id": "missing"}, {"attempt_id": "missing"}])
def test_relationships_must_exist_before_creation(tmp_path, changes):
    ledger = ledger_with_attempt(tmp_path)
    with pytest.raises(FileNotFoundError):
        ledger.create_verification(verification(**changes))
    assert_no_verification(ledger)


def test_attempt_cannot_be_borrowed_from_another_assignment(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    ledger.create_assignment(replace(ledger.assignment("assignment-1"), assignment_id="assignment-2"))
    with pytest.raises(VerificationDenied, match="different Assignment"):
        ledger.create_verification(verification(assignment_id="assignment-2"))
    assert_no_verification(ledger)


@pytest.mark.parametrize("independent_required", [True, False])
def test_verification_without_attempt_does_not_apply_attempt_worker_independence(tmp_path, independent_required):
    ledger = ledger_with_attempt(tmp_path, worker_id=None)
    ledger.create_verification(verification(attempt_id=None, independent_required=independent_required))
    assert ledger.verification("verification-1").attempt_id is None
    assert ledger.verification("verification-1").independent_required is independent_required


def test_gate_03_criteria_are_explicit_and_durable(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    for criteria in ((), ("",), ["mutable criteria"]):
        with pytest.raises(VerificationDenied):
            ledger.create_verification(verification(criteria=criteria))
    assert_no_verification(ledger)
    ledger.create_verification(verification())
    assert ledger.verification("verification-1").criteria == CRITERIA


def test_remediation_01_reordered_explicit_criteria_are_preserved(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    reordered = tuple(reversed(CRITERIA))
    ledger.create_verification(verification(criteria=reordered))
    assert AssignmentLedger(tmp_path).verification("verification-1").criteria == reordered
    assert ledger.assignment("assignment-1").verification_requirements == CRITERIA


@pytest.mark.parametrize("criteria", [("explicit result checks",), CRITERIA[:1],
                                     CRITERIA + ("an additional explicit check",)])
def test_remediation_02_criteria_need_not_equal_assignment_requirements(tmp_path, criteria):
    ledger = ledger_with_attempt(tmp_path)
    ledger.create_verification(verification(criteria=criteria))
    assert AssignmentLedger(tmp_path).verification("verification-1").criteria == criteria


def test_remediation_03_assignment_without_requirements_can_receive_verification(tmp_path):
    ledger = ledger_with_attempt(tmp_path, requirements=())
    ledger.create_verification(verification())
    assert ledger.assignment("assignment-1").verification_requirements == ()
    assert AssignmentLedger(tmp_path).verification("verification-1").criteria == CRITERIA


def test_gate_04_evidence_references_are_explicit_and_immutable(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    ledger.create_verification(verification())
    assert ledger.verification("verification-1").evidence_refs == (EVIDENCE,)
    for reference, digest in (("", "b" * 64), ("mutable/path", ""), ("branch:main", "main")):
        with pytest.raises(VerificationDenied):
            ledger.create_verification(verification(evidence_refs=(EvidenceRef(reference, digest),)))
    with pytest.raises(VerificationDenied):
        ledger.create_verification(verification(evidence_refs=[EVIDENCE]))


@pytest.mark.parametrize("commit_sha", ["c" * 40, "d" * 64])
def test_remediation_04_exact_commit_evidence_needs_no_redundant_digest(tmp_path, commit_sha):
    ledger = ledger_with_attempt(tmp_path)
    evidence = EvidenceRef(commit_sha)
    ledger.create_verification(verification(evidence_refs=(evidence,)))
    persisted = AssignmentLedger(tmp_path).verification("verification-1")
    assert persisted.evidence_refs == (evidence,)
    assert persisted.evidence_refs[0].reference == commit_sha
    assert persisted.evidence_refs[0].sha256 is None
    assert persisted.result == VerificationResult.PASS


@pytest.mark.parametrize("reference", ["test-results/current.json", "branch:main", "abcd"])
def test_mutable_evidence_needs_immutable_supporting_identity(tmp_path, reference):
    ledger = ledger_with_attempt(tmp_path)
    with pytest.raises(VerificationDenied, match="immutable identity"):
        ledger.create_verification(verification(evidence_refs=(EvidenceRef(reference),)))
    assert_no_verification(ledger)


def test_gate_05_verifier_is_required_and_durable(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    for verifier in (None, "", " ", " verifier-1 "):
        with pytest.raises(VerificationDenied):
            ledger.create_verification(verification(verifier=verifier))
    assert_no_verification(ledger)
    ledger.create_verification(verification())
    assert ledger.verification("verification-1").verifier == "verifier-1"


@pytest.mark.parametrize("subject", [SUBJECT, VerificationSubject("COMMIT_SHA", "c" * 40),
                                    VerificationSubject("COMMIT_SHA", "d" * 64)])
def test_gate_06_exact_subject_is_durable(tmp_path, subject):
    ledger = ledger_with_attempt(tmp_path)
    ledger.create_verification(verification(subject=subject))
    assert AssignmentLedger(tmp_path).verification("verification-1").subject == subject


def test_gate_07_missing_required_evidence_cannot_pass(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    with pytest.raises(VerificationDenied, match="PASS requires evidence"):
        ledger.create_verification(verification(evidence_refs=()))
    assert_no_verification(ledger)


@pytest.mark.parametrize("result", ["SUCCESS", "ACCEPTED", "PROMOTED", "", None, 0])
def test_gate_08_other_verdicts_are_rejected(tmp_path, result):
    ledger = ledger_with_attempt(tmp_path)
    with pytest.raises(VerificationDenied, match="unsupported verification result"):
        ledger.create_verification(verification(result=result))
    assert_no_verification(ledger)


@pytest.mark.parametrize("result", list(VerificationResult))
def test_governed_verdicts_remain_distinct_execution_facts(tmp_path, result):
    ledger = ledger_with_attempt(tmp_path)
    attempt_before = (tmp_path / "attempts/attempt-1.json").read_bytes()
    ledger.create_verification(verification(result=result, evidence_refs=() if result != "PASS" else (EVIDENCE,)))
    assert ledger.verification("verification-1").result == result
    assert (tmp_path / "attempts/attempt-1.json").read_bytes() == attempt_before


@pytest.mark.parametrize("result", list(VerificationResult))
def test_gate_09_10_same_worker_rejected_before_any_record(tmp_path, result):
    ledger = ledger_with_attempt(tmp_path)
    with pytest.raises(VerificationDenied, match="different logical worker"):
        ledger.create_verification(verification(verifier="worker-1", result=result))
    assert_no_verification(ledger)


def test_gate_11_changed_subject_needs_distinct_verification(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    original = verification()
    ledger.create_verification(original)
    changed = replace(original, subject=VerificationSubject("SHA256", "c" * 64))
    with pytest.raises(FileExistsError, match="immutable"):
        ledger.create_verification(changed)
    assert ledger.verification("verification-1") == original
    with pytest.raises(FileNotFoundError):
        ledger.verification("verification-2")
    ledger.create_verification(replace(changed, verification_id="verification-2"))
    assert ledger.verification("verification-2").subject == changed.subject
    assert ledger.verification("verification-1").subject == SUBJECT


def test_gate_12_13_verdict_changes_and_supersession_preserve_history(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    original = verification(result=VerificationResult.FAIL)
    ledger.create_verification(original)
    old_bytes = (tmp_path / "verifications/verification-1.json").read_bytes()
    with pytest.raises(FileExistsError):
        ledger.create_verification(replace(original, result=VerificationResult.PASS))
    later = verification(verification_id="verification-2", supersedes_verification_id="verification-1")
    ledger.create_verification(later)
    reopened = AssignmentLedger(tmp_path)
    assert reopened.verification("verification-2") == later
    assert reopened.verification(later.supersedes_verification_id) == original
    assert (tmp_path / "verifications/verification-1.json").read_bytes() == old_bytes
    with pytest.raises(FrozenInstanceError):
        later.result = VerificationResult.FAIL
    with pytest.raises(FrozenInstanceError):
        later.subject.identity = "e" * 64
    with pytest.raises(FrozenInstanceError):
        later.evidence_refs[0].sha256 = "e" * 64


def test_supersession_requires_existing_record_in_same_assignment(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    with pytest.raises(FileNotFoundError):
        ledger.create_verification(verification(supersedes_verification_id="missing"))
    assert_no_verification(ledger)
    ledger.create_verification(verification())
    ledger.create_assignment(replace(ledger.assignment("assignment-1"), assignment_id="assignment-2"))
    with pytest.raises(VerificationDenied, match="same Assignment"):
        ledger.create_verification(verification(verification_id="verification-2", assignment_id="assignment-2",
                                               attempt_id=None, independent_required=False,
                                               supersedes_verification_id="verification-1"))
    assert not (tmp_path / "verifications/verification-2.json").exists()


def test_gate_14_15_creation_has_no_acceptance_or_promotion_effect(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*.json")}
    ledger.create_verification(verification())
    after = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*.json")}
    assert after.keys() - before.keys() == {Path("verifications/verification-1.json")}
    assert all(after[path] == content for path, content in before.items())
    assert {path.name for path in tmp_path.iterdir()} == {
        "assignments", "authorizations", "attempts", "verifications", "used_attempt_ids.json",
    }
    assert not {"acceptance", "promotion"} & Verification.__dataclass_fields__.keys()


def test_gate_16_provider_neutral_core_works_without_adapters(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    ledger.create_verification(verification())
    assert ledger.verification("verification-1").result == VerificationResult.PASS
    for module in ("assignment_ledger.ledger", "assignment_ledger.verification"):
        source = inspect.getsource(sys.modules[module]).lower()
        assert not any(provider in source for provider in ("codex", "claude", "antigravity", "muse", "paperclip"))


@pytest.mark.parametrize("independent_required", [True, False])
def test_gate_17_worker_self_report_cannot_manufacture_pass(tmp_path, independent_required):
    ledger = ledger_with_attempt(tmp_path)
    with pytest.raises(VerificationDenied, match="self-report"):
        ledger.create_verification(verification(method=VerificationMethod.WORKER_SELF_REPORT,
                                               independent_required=independent_required))
    assert_no_verification(ledger)


@pytest.mark.parametrize("method", [VerificationMethod.DETERMINISTIC, VerificationMethod.MODEL_REVIEW,
                                    VerificationMethod.HUMAN_REVIEW])
def test_documented_non_independent_verification_allows_responsible_worker(tmp_path, method):
    ledger = ledger_with_attempt(tmp_path)
    ledger.create_verification(verification(verifier="worker-1", independent_required=False, method=method))
    persisted = AssignmentLedger(tmp_path).verification("verification-1")
    assert persisted.verifier == ledger.attempt("attempt-1")["worker_id"]
    assert persisted.independent_required is False
    assert persisted.result == VerificationResult.PASS
    assert persisted.method == method


@pytest.mark.parametrize("kind,identity", [("PATH", "out/result.json"), ("BRANCH", "main"),
                                          ("WORKSPACE", "workspace-1"), ("ISSUE", "123"),
                                          ("LABEL", "completed"), ("COMMIT_SHA", "abcd"),
                                          ("SHA256", "changed artifact"), ("SHA256", "g" * 64)])
def test_gate_18_mutable_labels_cannot_be_subjects(tmp_path, kind, identity):
    ledger = ledger_with_attempt(tmp_path)
    with pytest.raises(VerificationDenied, match="immutable identity"):
        ledger.create_verification(verification(subject=VerificationSubject(kind, identity)))
    assert_no_verification(ledger)


@pytest.mark.parametrize("method", list(VerificationMethod))
def test_method_nature_survives_persistence(tmp_path, method):
    ledger = ledger_with_attempt(tmp_path)
    ledger.create_verification(verification(method=method, result=VerificationResult.INCONCLUSIVE))
    assert AssignmentLedger(tmp_path).verification("verification-1").method == method
    assert VerificationMethod.MODEL_REVIEW != VerificationMethod.DETERMINISTIC
    assert VerificationMethod.HUMAN_REVIEW != VerificationMethod.DETERMINISTIC


@pytest.mark.parametrize("changes", [{"method": "REVIEW"}, {"created_at": "yesterday"},
                                    {"created_at": "2026-10-03T12:00:00"}, {"independent_required": "false"}])
def test_malformed_records_are_rejected_before_persistence(tmp_path, changes):
    ledger = ledger_with_attempt(tmp_path)
    with pytest.raises(VerificationDenied):
        ledger.create_verification(verification(**changes))
    assert_no_verification(ledger)


def test_clarification_01_02_worker_provenance_is_durable_and_distinct(tmp_path):
    ledger_with_attempt(tmp_path)
    attempt = AssignmentLedger(tmp_path).attempt("attempt-1")
    assert attempt["worker_id"] == "worker-1"
    assert attempt["worker_id"] != attempt["attempt_id"]
    assert set(attempt) == {"attempt_id", "assignment_id", "authorization_id", "started_at", "worker_id"}


def test_clarification_03_other_attempt_or_session_does_not_establish_independence(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    ledger.execute("assignment-1", "authorization-1", lambda request: None,
                   attempt_id="different-run-session-harness-model", worker_id="worker-1")
    with pytest.raises(VerificationDenied, match="different logical worker"):
        ledger.create_verification(verification(attempt_id="different-run-session-harness-model", verifier="worker-1"))
    assert_no_verification(ledger)


def test_clarification_04_unknown_worker_fails_closed_without_rewriting_history(tmp_path):
    ledger = ledger_with_attempt(tmp_path, worker_id=None)
    attempt_bytes = (tmp_path / "attempts/attempt-1.json").read_bytes()
    reopened = AssignmentLedger(tmp_path)
    assert "worker_id" not in reopened.attempt("attempt-1")
    with pytest.raises(VerificationDenied, match="known Attempt worker"):
        reopened.create_verification(verification(verifier="different-run-session-chat-process-reviewer-harness-model"))
    assert_no_verification(ledger)
    assert (tmp_path / "attempts/attempt-1.json").read_bytes() == attempt_bytes


def test_clarification_05_different_logical_verifier_can_proceed(tmp_path):
    ledger = ledger_with_attempt(tmp_path)
    ledger.create_verification(verification())
    record = AssignmentLedger(tmp_path).verification("verification-1")
    assert record.independent_required is True
    assert record.verifier != ledger.attempt(record.attempt_id)["worker_id"]
    assert record.result == VerificationResult.PASS


@pytest.mark.parametrize("authorization_id", [None, "missing"])
def test_clarification_06_worker_provenance_does_not_bypass_authorization(tmp_path, authorization_id):
    ledger = ledger_with_attempt(tmp_path)
    calls = []
    with pytest.raises(AuthorizationDenied):
        ledger.execute("assignment-1", authorization_id, calls.append,
                       attempt_id="attempt-2", worker_id="worker-2")
    assert calls == []
    assert not (tmp_path / "attempts/attempt-2.json").exists()


@pytest.mark.parametrize("worker_id", ["", " ", " worker-1 "])
def test_invalid_worker_provenance_rejected_before_invocation(tmp_path, worker_id):
    ledger = ledger_with_attempt(tmp_path)
    calls = []
    with pytest.raises(VerificationDenied, match="worker_id"):
        ledger.execute("assignment-1", "authorization-1", calls.append,
                       attempt_id="attempt-2", worker_id=worker_id)
    assert calls == []
    assert not (tmp_path / "attempts/attempt-2.json").exists()
