from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


STAGES = ("normalize", "classify", "select_evidence", "recommend", "generate_final_brief")


class StageTrace(BaseModel):
    run_id: str
    case_id: str
    stage: str
    stage_index: int
    input_hash: str
    input_reference: str
    input_state: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    validation_pass: bool
    validation_errors: list[str] = Field(default_factory=list)
    provider: str = "local"
    runtime: str = "Python deterministic fixture"
    model: str | None = None
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    api_service_cost_usd: float = 0.0
    status: str = "completed"
    failure_type: str | None = None
    first_failure: bool = False


class Finding(BaseModel):
    case_id: str
    first_failure_stage: str | None
    failure_type: str | None
    symptom_stages: list[str] = Field(default_factory=list)
    propagation_detected: bool = False
    contained: bool = False
    clean_run: bool
