import inspect
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB / "src"))

from assignment_ledger import Assignment, AssignmentAlreadyAttempted, AssignmentLedger, Authorization, AuthorizationDenied


def assignment(scope=frozenset({"read:fixture"})):
    return Assignment("assignment-1", "inspect fixture", scope, ("local only",), ("report",), ("human review",))


def authorization(*, valid=True, scope=frozenset({"read:fixture"})):
    return Authorization("authorization-1", "approved test fixture", "GOV-001", scope, ("local only",),
                         "2026-09-14T00:00:00+00:00", "governance", valid)


def ledger_with_records(tmp_path, *, auth=True, valid=True, scope=frozenset({"read:fixture"})):
    ledger = AssignmentLedger(tmp_path)
    ledger.create_assignment(assignment())
    if auth:
        ledger.create_authorization(authorization(valid=valid, scope=scope))
    return ledger


def test_01_attempt_references_exactly_one_assignment(tmp_path):
    ledger = ledger_with_records(tmp_path)
    ledger.execute("assignment-1", "authorization-1", lambda request: None, attempt_id="attempt-1")
    record = ledger.attempt("attempt-1")
    assert record["assignment_id"] == "assignment-1"
    assert "assignment_ids" not in record


def test_02_executable_attempt_requires_existing_authorization(tmp_path):
    ledger = ledger_with_records(tmp_path, auth=False)
    with pytest.raises(AuthorizationDenied, match="does not exist"):
        ledger.execute("assignment-1", "missing", lambda request: None)


def test_03_valid_authorization_reaches_normalized_invocation_boundary(tmp_path):
    ledger = ledger_with_records(tmp_path)
    calls = []
    ledger.execute("assignment-1", "authorization-1", calls.append, attempt_id="attempt-1")
    assert len(calls) == 1 and calls[0].authorization_id == "authorization-1"


@pytest.mark.parametrize("authorization_id", [None, "missing"])
def test_04_missing_authorization_blocks_before_invocation(tmp_path, authorization_id):
    ledger = ledger_with_records(tmp_path, auth=False)
    calls = []
    with pytest.raises(AuthorizationDenied):
        ledger.execute("assignment-1", authorization_id, calls.append)
    assert calls == []


@pytest.mark.parametrize("valid,scope", [(False, frozenset({"read:fixture"})), (True, frozenset({"write:fixture"}))])
def test_05_invalid_or_out_of_scope_authorization_blocks_before_invocation(tmp_path, valid, scope):
    ledger = ledger_with_records(tmp_path, valid=valid, scope=scope)
    calls = []
    with pytest.raises(AuthorizationDenied):
        ledger.execute("assignment-1", "authorization-1", calls.append)
    assert calls == []


def test_06_invocation_boundary_is_never_called_on_authorization_failure(tmp_path):
    ledger = ledger_with_records(tmp_path, valid=False)
    calls = []
    with pytest.raises(AuthorizationDenied):
        ledger.execute("assignment-1", "authorization-1", calls.append)
    assert calls == []


def test_07_attempt_ids_are_immutable_and_never_reused(tmp_path):
    ledger = ledger_with_records(tmp_path)
    ledger.execute("assignment-1", "authorization-1", lambda request: None, attempt_id="attempt-1")
    with pytest.raises(ValueError, match="cannot be reused"):
        ledger.execute("assignment-1", "authorization-1", lambda request: None, attempt_id="attempt-1")


def test_08_attempt_retains_assignment_and_authorization_that_started_it(tmp_path):
    ledger = ledger_with_records(tmp_path)
    ledger.execute("assignment-1", "authorization-1", lambda request: None, attempt_id="attempt-1")
    record = ledger.attempt("attempt-1")
    assert (record["assignment_id"], record["authorization_id"]) == ("assignment-1", "authorization-1")
    with pytest.raises(FileExistsError):
        ledger.create_authorization(authorization(valid=False))
    assert ledger.authorization("authorization-1").valid is True


def test_09_material_assignment_change_after_attempt_requires_supersession(tmp_path):
    ledger = ledger_with_records(tmp_path)
    ledger.execute("assignment-1", "authorization-1", lambda request: None, attempt_id="attempt-1")
    changed = assignment(scope=frozenset({"write:fixture"}))
    with pytest.raises(AssignmentAlreadyAttempted, match="superseding"):
        ledger.replace_assignment(changed)
    assert ledger.assignment("assignment-1").scope == frozenset({"read:fixture"})


def test_10_authority_seam_is_provider_neutral(tmp_path):
    ledger = ledger_with_records(tmp_path)
    calls = []
    ledger.execute("assignment-1", "authorization-1", calls.append, attempt_id="attempt-1")
    request = calls[0]
    assert set(request.__dataclass_fields__) == {"attempt_id", "assignment_id", "authorization_id", "objective"}
    seam_source = inspect.getsource(sys.modules["assignment_ledger.ledger"]).lower()
    assert not any(name in seam_source for name in ("claude", "codex", "antigravity", "gemini"))
