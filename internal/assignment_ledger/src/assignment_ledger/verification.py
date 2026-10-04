"""Immutable values for the bounded Verification record, without proof execution."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re


class VerificationDenied(ValueError):
    """A proposed Verification cannot be recorded as a valid historical fact."""


class VerificationResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class VerificationMethod(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    MODEL_REVIEW = "MODEL_REVIEW"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    WORKER_SELF_REPORT = "WORKER_SELF_REPORT"


def require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise VerificationDenied(f"{name} must be non-empty text without surrounding whitespace")


@dataclass(frozen=True)
class VerificationSubject:
    """Exact content identity: a full commit SHA or a SHA-256 content digest."""

    kind: str
    identity: str

    def __post_init__(self) -> None:
        lengths = {"COMMIT_SHA": (40, 64), "SHA256": (64,)}
        if (self.kind not in lengths or not isinstance(self.identity, str)
                or len(self.identity) not in lengths[self.kind]
                or re.fullmatch(r"[0-9a-f]+", self.identity) is None):
            raise VerificationDenied("subject requires a full commit SHA or SHA256 immutable identity")


@dataclass(frozen=True)
class EvidenceRef:
    """A locator plus the SHA-256 of the exact evidence content supporting the verdict."""

    reference: str
    sha256: str

    def __post_init__(self) -> None:
        require_text(self.reference, "evidence reference")
        if not isinstance(self.sha256, str) or re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None:
            raise VerificationDenied("evidence requires a SHA256 immutable identity")


@dataclass(frozen=True)
class Verification:
    verification_id: str
    assignment_id: str
    subject: VerificationSubject
    verifier: str
    criteria: tuple[str, ...]
    evidence_refs: tuple[EvidenceRef, ...]
    method: VerificationMethod
    result: VerificationResult
    attempt_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    supersedes_verification_id: str | None = None
    independent_required: bool = True

    def __post_init__(self) -> None:
        for name in ("verification_id", "assignment_id", "verifier"):
            require_text(getattr(self, name), name)
        for name in ("attempt_id", "supersedes_verification_id"):
            if getattr(self, name) is not None:
                require_text(getattr(self, name), name)
        if not isinstance(self.subject, VerificationSubject):
            raise VerificationDenied("subject requires an immutable VerificationSubject")
        if not isinstance(self.criteria, tuple) or not self.criteria:
            raise VerificationDenied("explicit criteria are required as an immutable tuple")
        for criterion in self.criteria:
            require_text(criterion, "criterion")
        if (not isinstance(self.evidence_refs, tuple)
                or any(not isinstance(ref, EvidenceRef) for ref in self.evidence_refs)):
            raise VerificationDenied("evidence_refs must be an immutable tuple of EvidenceRef values")
        try:
            object.__setattr__(self, "result", VerificationResult(self.result))
            object.__setattr__(self, "method", VerificationMethod(self.method))
        except (TypeError, ValueError) as error:
            raise VerificationDenied("unsupported verification result or method") from error
        if type(self.independent_required) is not bool:
            raise VerificationDenied("independent_required must be an explicit boolean")
        try:
            timestamp = datetime.fromisoformat(self.created_at)
        except (TypeError, ValueError) as error:
            raise VerificationDenied("created_at requires an ISO timestamp") from error
        if timestamp.utcoffset() is None:
            raise VerificationDenied("created_at requires a timezone")
        if self.result == VerificationResult.PASS:
            if not self.evidence_refs:
                raise VerificationDenied("PASS requires evidence")
            if self.method == VerificationMethod.WORKER_SELF_REPORT:
                raise VerificationDenied("worker self-report cannot establish PASS")
