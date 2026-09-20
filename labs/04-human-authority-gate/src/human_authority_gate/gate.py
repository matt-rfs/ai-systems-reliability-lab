"""Deterministic implementation of the frozen Freeze A gate contract."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any


EVALUATION_TIME = "2030-01-15T12:00:00Z"
ACTION_REQUIREMENTS = {
    "SAVE_INTERNAL_DRAFT": "AUTONOMOUS",
    "SEND_EXTERNAL_MESSAGE": "HUMAN_REQUIRED",
    "DELETE_EXTERNAL_MESSAGE": "PROHIBITED",
}
PAYLOAD_FIELDS = {
    "SAVE_INTERNAL_DRAFT": {"body", "title"},
    "SEND_EXTERNAL_MESSAGE": {"body", "subject", "to"},
    "DELETE_EXTERNAL_MESSAGE": {"message_id"},
}
AUTHORIZATION_FIELDS = {
    "decision", "action_type", "action_scope", "action_payload_fingerprint", "valid_from", "valid_until"
}
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
FINGERPRINT = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class GateResult:
    authority_requirement: str
    disposition: str
    reason_code: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def canonical_json(payload: dict[str, Any]) -> str:
    """Return the exact canonical serialization frozen by Freeze A."""
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def payload_fingerprint(payload: dict[str, Any]) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not TIMESTAMP.fullmatch(value):
        raise ValueError("timestamp must be strict UTC second-precision Z syntax")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def validate_action(action: object) -> dict[str, Any]:
    if not isinstance(action, dict) or set(action) != {"action_type", "action_scope", "action_payload"}:
        raise ValueError("proposed action must contain exactly the frozen fields")
    action_type, scope, payload = action["action_type"], action["action_scope"], action["action_payload"]
    if action_type not in ACTION_REQUIREMENTS or not isinstance(scope, str) or not scope:
        raise ValueError("invalid frozen proposed action identity")
    if not isinstance(payload, dict) or set(payload) != PAYLOAD_FIELDS[action_type]:
        raise ValueError("payload does not match the frozen action schema")
    if not all(isinstance(value, str) for value in payload.values()):
        raise ValueError("payload values must be strings")
    canonical_json(payload)  # rejects non-finite values should an unsupported object reach this boundary
    return action


def _valid_authorization(record: object) -> bool:
    if not isinstance(record, dict) or set(record) != AUTHORIZATION_FIELDS:
        return False
    if record["decision"] not in {"GRANTED", "REJECTED"} or record["action_type"] not in ACTION_REQUIREMENTS:
        return False
    if not isinstance(record["action_scope"], str) or not record["action_scope"]:
        return False
    if not isinstance(record["action_payload_fingerprint"], str) or not FINGERPRINT.fullmatch(record["action_payload_fingerprint"]):
        return False
    try:
        return _timestamp(record["valid_from"]) < _timestamp(record["valid_until"])
    except (TypeError, ValueError):
        return False


def _authorization_boundary(authorization: object) -> tuple[dict[str, Any] | None, bool]:
    if authorization is None:
        return None, False
    if isinstance(authorization, (list, tuple)):
        if len(authorization) == 0:
            return None, False
        if len(authorization) != 1:
            return None, True
        authorization = authorization[0]
    return (authorization, False) if _valid_authorization(authorization) else (None, True)


def evaluate_gate(action: object, authorization: object = None, *, evaluation_time: str = EVALUATION_TIME) -> GateResult:
    """Apply the exact frozen precedence; no policy inference or side effects occur here."""
    action = validate_action(action)
    now = _timestamp(evaluation_time)
    requirement = ACTION_REQUIREMENTS[action["action_type"]]
    if requirement == "PROHIBITED":
        return GateResult(requirement, "BLOCK", "PROHIBITED_ACTION")
    if requirement == "AUTONOMOUS":
        return GateResult(requirement, "EXECUTE", "AUTONOMOUS_ALLOWED")

    record, malformed = _authorization_boundary(authorization)
    if malformed:
        return GateResult(requirement, "BLOCK", "AUTHORIZATION_MALFORMED")
    if record is None:
        return GateResult(requirement, "BLOCK", "AUTHORIZATION_MISSING")
    if record["action_type"] != action["action_type"]:
        return GateResult(requirement, "BLOCK", "ACTION_TYPE_MISMATCH")
    if record["action_scope"] != action["action_scope"]:
        return GateResult(requirement, "BLOCK", "ACTION_SCOPE_MISMATCH")
    if record["action_payload_fingerprint"] != payload_fingerprint(action["action_payload"]):
        return GateResult(requirement, "BLOCK", "ACTION_PAYLOAD_MISMATCH")
    valid_from, valid_until = _timestamp(record["valid_from"]), _timestamp(record["valid_until"])
    if now < valid_from:
        return GateResult(requirement, "BLOCK", "AUTHORIZATION_NOT_YET_VALID")
    if now >= valid_until:
        return GateResult(requirement, "BLOCK", "AUTHORIZATION_EXPIRED")
    if record["decision"] == "REJECTED":
        return GateResult(requirement, "BLOCK", "AUTHORIZATION_REJECTED")
    return GateResult(requirement, "EXECUTE", "VALID_AUTHORIZATION")


def synthetic_execute(result: GateResult, action: object) -> str:
    """Mechanical downstream executor; action is deliberately not inspected."""
    validate_action(action)
    if result.disposition == "EXECUTE":
        return "ACTION_EXECUTED"
    if result.disposition == "BLOCK":
        return "ACTION_BLOCKED"
    raise ValueError("unknown frozen gate disposition")
