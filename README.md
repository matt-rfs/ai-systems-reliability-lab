# AI Systems Reliability Lab

Small, inspectable experiments in evaluating AI-enabled systems. Lab 01 uses only synthetic, public-safe data.

## Lab 01 — Model Regression Gate

**Question:** Did a frozen AI configuration change make a bounded business workflow measurably worse?

The completed V0.3 experiment ran two frozen prompt configurations across 30 synthetic cases each using local, schema-constrained inference. Both configurations passed deterministic checks **30/30**, with **zero deterministic regressions** and **zero hard-gate violations**.

The historical automated release decision was **FAIL** because its local factual-support judge measured 50.0% baseline support and 58.6% candidate support—below the frozen 90% threshold.

## What the later audit changed

V0.3.1 independently audited all 60 generated replies. The local semantic judge showed low agreement with human review (53.3% baseline; 43.3% candidate), with 24 false positives, 6 false negatives, and one unavailable judgment. The automated V0.3 FAIL remains preserved as the historical system decision, but the audit limits confidence in that semantic gate as a release authority in this bounded setup.

## Evidence

Start with [the public evidence index](labs/01-regression-gate/results/PUBLIC_EVIDENCE.md).

## Decisions I Made

- Used deterministic checks whenever correctness could be established exactly; kept factual support as the sole semantic dimension.
- Froze the dataset, prompts, model, schema-constrained decoding, and release thresholds before clean execution.
- Rejected contaminated execution traces rather than normalizing them into a result.
- Preserved the automated FAIL after the later audit challenged the local semantic evaluator.

## Boundary

This is a synthetic, local experiment with **$0 API/service spend**, not production infrastructure, a general benchmark, or a claim about all LLM-as-judge systems.
