"""The one non-deterministic evaluator: factual support for customer replies."""
from __future__ import annotations

from dataclasses import dataclass
from .gateway import OpenAICompatibleLocalGateway
from .models import GoldenCase, ModelOutput

JUDGE_PROMPT = """You are a narrow factual-support evaluator. Return JSON only with keys supported (boolean) and unsupported_claims (array of strings). A reply is supported only when every material factual claim is grounded in the supplied customer message, account context, or policy facts. Recommendations and hedged process statements are allowed only if the policy facts support them. Do not judge style, helpfulness, or classification."""

@dataclass(frozen=True)
class FactualSupport:
    supported: bool
    unsupported_claims: list[str]
    judge_model: str
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    raw_judge_output: dict

def evaluate_factual_support(case: GoldenCase, output: ModelOutput, gateway: OpenAICompatibleLocalGateway) -> FactualSupport:
    call = gateway.complete_json(JUDGE_PROMPT, {"customer_message": case.customer_message, "account_context": case.account_context, "policy_facts": case.policy_facts, "customer_reply": output.customer_reply}, temperature=0, max_tokens=200)
    return FactualSupport(supported=bool(call.output["supported"]), unsupported_claims=list(call.output.get("unsupported_claims", [])), judge_model=call.model, latency_ms=call.latency_ms, input_tokens=call.input_tokens, output_tokens=call.output_tokens, raw_judge_output=call.output)
