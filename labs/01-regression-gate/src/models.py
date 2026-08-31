from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field

class RequestType(str, Enum):
    BILLING="billing"; ACCOUNT_ACCESS="account_access"; TECHNICAL_ISSUE="technical_issue"; SECURITY="security"; CANCELLATION="cancellation"; FEATURE_REQUEST="feature_request"; GENERAL="general"; UNKNOWN="unknown"

class Urgency(str, Enum):
    LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"

class Action(str, Enum):
    SELF_SERVICE="self_service"; SUPPORT_REVIEW="support_review"; BILLING_REVIEW="billing_review"; ENGINEERING_REVIEW="engineering_review"; SECURITY_ESCALATION="security_escalation"; ACCOUNT_REVIEW="account_review"; HUMAN_REVIEW="human_review"

class ModelOutput(BaseModel):
    request_type: RequestType
    urgency: Urgency
    recommended_action: Action
    requires_human: bool
    evidence_ids: list[str] = Field(default_factory=list)
    customer_reply: str

class GoldenCase(BaseModel):
    case_id: str
    customer_message: str
    account_context: dict
    policy_facts: dict[str, str]
    expected_request_type: RequestType
    acceptable_urgency: list[Urgency]
    acceptable_actions: list[Action]
    must_require_human: bool
    required_evidence_ids: list[str]
    forbidden_actions: list[Action] = Field(default_factory=list)
    difficulty_tags: list[str] = Field(default_factory=list)

class CheckResult(BaseModel):
    name: str
    passed: bool
    detail: str = ""
    hard_gate: bool = False

class CaseEvaluation(BaseModel):
    case_id: str
    schema_valid: bool
    checks: list[CheckResult]

    @property
    def deterministic_pass(self) -> bool:
        return self.schema_valid and all(c.passed for c in self.checks)

    @property
    def hard_gate_failed(self) -> bool:
        return any((not c.passed) and c.hard_gate for c in self.checks)
