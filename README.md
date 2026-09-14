# AI Systems Reliability Lab

A public series of small, inspectable experiments testing reliability mechanisms for AI-enabled systems.

**EVALUATE → DIAGNOSE → ROUTE**

## Lab 01 — Model Regression Gate

**Status:** COMPLETED PROOF
**Question:** Can a proposed AI configuration be automatically blocked when it makes a bounded business workflow worse?

The completed frozen experiment evaluates deterministic checks and one semantic factual-support judge across synthetic, public-safe cases. Both frozen configurations passed deterministic checks 30/30 with zero deterministic regressions and zero hard-gate violations. The historical automated release decision remains **FAIL** because the semantic judge fell below its frozen 90% support threshold.

A later human audit found the local semantic judge unreliable as release authority in this bounded setup. The historical automated FAIL is preserved rather than rewritten. See [Lab 01 public evidence](labs/01-regression-gate/results/PUBLIC_EVIDENCE.md).

## Lab 02 — Failure Forensics

**Status:** COMPLETED PROOF
**Question:** Can a bad multi-stage AI outcome be traced to the stage that first caused it?

The deterministic local fixture contains 14 frozen cases and 70 structured traces, with 14/14 first-failure localization, 14/14 failure-type classification, and 14/14 propagation or containment determinations. It used $0 API/service spend. See [Lab 02](labs/02-failure-forensics/README.md).

## Lab 03 — Cost / Quality Router

**Status:** FOUNDATION PUBLIC / MEASUREMENT PENDING
**Question:** Can an AI system select the lowest-burden execution route only after that route proves it clears frozen quality and policy-authority requirements?

The public foundation provides deterministic runbook verification, a frozen V001 quality floor, evidence-derived route eligibility, measured/held-out conjunction, explicit metric epistemics, Pareto burden comparison, deterministic-route anti-lookup boundaries, canonical freeze-surface hashing, and route-bound/verifier-bound evidence contracts.

No measured Lab 03 routing result exists yet. R0, R1, and R2 have not executed publicly; there is no routing winner, measured cost saving, or observed NO-ROUTER-NEEDED outcome. See [Lab 03](labs/03-cost-quality-router/README.md).

## Program story

**Evaluate:** Lab 01 asks whether a changed AI configuration became worse.
**Diagnose:** Lab 02 asks where a bad outcome first became invalid.
**Route:** Lab 03 builds the foundation for deciding which execution path is eligible before burden is compared.

## Boundary

These are synthetic, bounded experiments. They are not production infrastructure, a general AI benchmark, or an autonomous orchestration system.
