from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from models import StageTrace


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:16]


def make_trace(run_id: str, case_id: str, stage: str, stage_index: int, input_value: Any,
               output: dict[str, Any], validation_pass: bool, validation_errors: list[str],
               started: float, status: str = "completed", failure_type: str | None = None) -> StageTrace:
    return StageTrace(
        run_id=run_id, case_id=case_id, stage=stage, stage_index=stage_index,
        input_hash=stable_hash(input_value), input_reference=f"{case_id}:{stage_index - 1}",
        input_state=input_value,
        output=output, validation_pass=validation_pass, validation_errors=validation_errors,
        latency_ms=round((time.perf_counter() - started) * 1000, 3), status=status,
        failure_type=failure_type,
    )
