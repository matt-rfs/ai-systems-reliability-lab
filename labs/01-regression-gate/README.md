# Lab 01 — Model Regression Gate

**Question:** Can a proposed AI configuration be automatically blocked when it makes a bounded business workflow worse?

V0.3 completed a frozen real-model experiment using local Ollama, `qwen2.5:1.5b`, JSON-schema-constrained decoding, temperature 0, and a 200-token ceiling. `configs/frozen_v0.3_execution.json` records the actual execution setting; the frozen manifest remains authoritative.

## Current milestone

- 30 public-safe synthetic golden cases
- strict structured output contract
- deterministic classification, action, evidence, and authority checks
- baseline/candidate comparison
- hard release gate
- deliberately bad mutation to verify the evaluator catches seeded regressions
- fixture mode so tests and CI require no API key and cost $0
- a local-only `ModelGateway` that captures provider, model, prompt hash, token usage when supplied, cost ($0.00), and latency per call
- exactly one semantic evaluator: factual support for `customer_reply`; all other checks remain deterministic
- clean V0.3 evidence and a post-experiment semantic evaluator audit

## Important boundary

The fixture outputs validate the **evaluation system**, not model performance. The known-bad configuration remains a mutation self-test. V0.3 is the completed local synthetic experiment; V0.3.1 is a later evaluator audit and does not rewrite its historical automated decision.

## Why no UI/database/framework?

None is required to answer the experiment question. Complexity must pay rent.
