"""A deliberately small, local-only model gateway for the Lab 01 experiment."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import time
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


class LocalInferenceUnavailable(RuntimeError):
    """Raised when no configured local OpenAI-compatible server is reachable."""


@dataclass(frozen=True)
class ModelCall:
    output: dict[str, Any]
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float
    latency_ms: int


class OpenAICompatibleLocalGateway:
    """Calls a local server only; this class never accepts credentials or cloud URLs."""
    provider = "openai_compatible_local"

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("LOCAL_MODEL_BASE_URL", "http://127.0.0.1:1234/v1")).rstrip("/")
        self.model = model or os.getenv("LOCAL_MODEL_ID", "")
        if not self.base_url.startswith(("http://127.0.0.1", "http://localhost")):
            raise ValueError("Lab 01 permits local model servers only.")

    def available(self) -> bool:
        try:
            with urlopen(f"{self.base_url}/models", timeout=2) as response:
                return 200 <= response.status < 300
        except (URLError, OSError):
            return False

    def complete_json(self, system_prompt: str, user_payload: dict[str, Any], *, temperature: float, max_tokens: int) -> ModelCall:
        if not self.model:
            raise LocalInferenceUnavailable("LOCAL_MODEL_ID is not configured.")
        payload = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, sort_keys=True)},
            ],
        }
        request = Request(f"{self.base_url}/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        started = time.perf_counter()
        try:
            with urlopen(request, timeout=120) as response:
                raw = json.loads(response.read())
        except (URLError, OSError) as exc:
            raise LocalInferenceUnavailable(f"Local model request failed: {exc}") from exc
        latency_ms = round((time.perf_counter() - started) * 1000)
        try:
            content = raw["choices"][0]["message"]["content"]
            output = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LocalInferenceUnavailable("Local model did not return a JSON object.") from exc
        usage = raw.get("usage", {})
        return ModelCall(output=output, provider=self.provider, model=raw.get("model", self.model), input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"), cost_usd=0.0, latency_ms=latency_ms)
