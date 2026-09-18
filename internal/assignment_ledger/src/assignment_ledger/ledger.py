"""The deliberately small, provider-neutral Slice 1 authority boundary."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4


class AuthorizationDenied(ValueError):
    """Raised before an invocation boundary can be reached."""


class AssignmentAlreadyAttempted(ValueError):
    """Raised when a material Assignment rewrite would alter history."""


@dataclass(frozen=True)
class Assignment:
    assignment_id: str
    objective: str
    scope: frozenset[str]
    constraints: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    verification_requirements: tuple[str, ...]


@dataclass(frozen=True)
class Authorization:
    authorization_id: str
    basis: str
    source_reference: str
    authorized_scope: frozenset[str]
    constraints: tuple[str, ...]
    granted_at: str
    granted_by: str | None
    valid: bool = True


@dataclass(frozen=True)
class InvocationRequest:
    """Normalized input at the boundary; it intentionally names no provider."""

    attempt_id: str
    assignment_id: str
    authorization_id: str
    objective: str


class AssignmentLedger:
    """Append-only JSON records and the only route to the invocation boundary."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        for kind in ("assignments", "authorizations", "attempts"):
            (self.root / kind).mkdir(parents=True, exist_ok=True)
        self._used_attempt_ids = self.root / "used_attempt_ids.json"
        if not self._used_attempt_ids.exists():
            self._write_new(self._used_attempt_ids, [])

    def create_assignment(self, assignment: Assignment) -> None:
        self._write_new(self._path("assignments", assignment.assignment_id), self._assignment_data(assignment))

    def create_authorization(self, authorization: Authorization) -> None:
        self._write_new(self._path("authorizations", authorization.authorization_id), self._authorization_data(authorization))

    def assignment(self, assignment_id: str) -> Assignment:
        data = self._read(self._path("assignments", assignment_id))
        return Assignment(**{**data, "scope": frozenset(data["scope"]), "constraints": tuple(data["constraints"]),
                             "expected_outputs": tuple(data["expected_outputs"]),
                             "verification_requirements": tuple(data["verification_requirements"])})

    def authorization(self, authorization_id: str) -> Authorization:
        data = self._read(self._path("authorizations", authorization_id))
        return Authorization(**{**data, "authorized_scope": frozenset(data["authorized_scope"]),
                                "constraints": tuple(data["constraints"])})

    def attempt(self, attempt_id: str) -> dict[str, str]:
        return self._read(self._path("attempts", attempt_id))

    def replace_assignment(self, assignment: Assignment) -> None:
        """Forbid in-place material rewrites after an Attempt has started."""
        if any(record["assignment_id"] == assignment.assignment_id for record in self._attempt_records()):
            raise AssignmentAlreadyAttempted("an attempted Assignment requires a superseding or versioned revision")
        path = self._path("assignments", assignment.assignment_id)
        if not path.exists():
            raise FileNotFoundError(assignment.assignment_id)
        self._write_replace(path, self._assignment_data(assignment))

    def execute(
        self,
        assignment_id: str,
        authorization_id: str | None,
        invoke: Callable[[InvocationRequest], object],
        *,
        attempt_id: str | None = None,
    ) -> object:
        """Validate authorization, persist immutable attempt truth, then invoke."""
        assignment = self.assignment(assignment_id)
        authorization = self._require_valid_authorization(authorization_id, assignment)
        attempt_id = attempt_id or str(uuid4())
        self._record_attempt(attempt_id, assignment, authorization)
        return invoke(InvocationRequest(attempt_id, assignment_id, authorization.authorization_id, assignment.objective))

    def _require_valid_authorization(self, authorization_id: str | None, assignment: Assignment) -> Authorization:
        if authorization_id is None:
            raise AuthorizationDenied("an executable Attempt requires an Authorization")
        try:
            authorization = self.authorization(authorization_id)
        except FileNotFoundError as error:
            raise AuthorizationDenied("Authorization does not exist") from error
        if not authorization.valid:
            raise AuthorizationDenied("Authorization is invalid")
        if not assignment.scope.issubset(authorization.authorized_scope):
            raise AuthorizationDenied("Authorization is out of scope for Assignment")
        return authorization

    def _record_attempt(self, attempt_id: str, assignment: Assignment, authorization: Authorization) -> None:
        used = self._read(self._used_attempt_ids)
        if attempt_id in used or self._path("attempts", attempt_id).exists():
            raise ValueError("Attempt IDs are immutable and cannot be reused")
        used.append(attempt_id)
        self._write_replace(self._used_attempt_ids, used)
        self._write_new(self._path("attempts", attempt_id), {
            "attempt_id": attempt_id,
            "assignment_id": assignment.assignment_id,
            "authorization_id": authorization.authorization_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
        })

    def _attempt_records(self) -> list[dict[str, str]]:
        return [self._read(path) for path in (self.root / "attempts").glob("*.json")]

    def _path(self, kind: str, record_id: str) -> Path:
        if not record_id or "/" in record_id or "\\" in record_id or record_id in {".", ".."}:
            raise ValueError("record identifiers must be simple non-empty names")
        return self.root / kind / f"{record_id}.json"

    @staticmethod
    def _assignment_data(record: Assignment) -> dict[str, object]:
        data = asdict(record)
        data["scope"] = sorted(record.scope)
        return data

    @staticmethod
    def _authorization_data(record: Authorization) -> dict[str, object]:
        data = asdict(record)
        data["authorized_scope"] = sorted(record.authorized_scope)
        return data

    @staticmethod
    def _read(path: Path):
        with path.open() as handle:
            return json.load(handle)

    @staticmethod
    def _write_new(path: Path, data: object) -> None:
        with path.open("x") as handle:
            json.dump(data, handle, sort_keys=True, indent=2)

    @staticmethod
    def _write_replace(path: Path, data: object) -> None:
        temporary = path.with_suffix(".tmp")
        with temporary.open("x") as handle:
            json.dump(data, handle, sort_keys=True, indent=2)
        temporary.replace(path)
