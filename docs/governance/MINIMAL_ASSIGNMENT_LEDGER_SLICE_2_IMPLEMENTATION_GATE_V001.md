# AI SYSTEMS RELIABILITY LAB
# CROSS-HARNESS / GOVERNANCE
# MINIMAL ASSIGNMENT LEDGER SLICE 2 IMPLEMENTATION GATE V001

## PURPOSE

Freeze the minimum implementation boundary for:

SLICE 2 — VERIFICATION RECORD + INDEPENDENT VERIFICATION BOUNDARY

This gate follows:

ASSIGNMENT
→ AUTHORIZATION
→ ATTEMPT

and adds only:

→ VERIFICATION

No later ledger stage is authorized by this gate.

## AUTHORITATIVE INPUTS

Slice 1 implementation:

`bb92375bedd87ab3b47274e2e618698cdc212c87`

Slice 1 governance acceptance:

`2504bff5a8df3dfb1a34fa555746e4a9a3f3e109`

Post-Slice-1 reassessment:

`81f42863f406e6989b99cbc9a5da42daa5d98144`

Post-Slice-1 decision:

`2816c2b9b3a40502ca449ceb74ef950452b26e14`

Governance disposition:

GO — VERIFICATION RECORD + INDEPENDENT VERIFICATION BOUNDARY

## RELIABILITY QUESTION

Slice 2 must prove:

Can the system durably distinguish an Attempt completing from independent evidence establishing whether that Attempt satisfied explicit verification criteria?

## CORE DOCTRINE

Preserve:

ATTEMPT COMPLETED ≠ VERIFIED

WORKER SELF-REPORT ≠ PROOF

IMPLEMENTER DOES NOT DEFINE SUCCESS

MODEL REVIEW ≠ DETERMINISTIC PROOF

VERIFICATION ≠ ACCEPTANCE

ACCEPTANCE ≠ PROMOTION

VERIFICATION(A) DOES NOT JUSTIFY ACCEPTANCE OR PROMOTION OF B

THE SUBJECT ACCEPTED OR PROMOTED MUST BE THE SAME IMMUTABLE SUBJECT THAT WAS VERIFIED

## IMPLEMENTATION SCOPE

Slice 2 may implement only the minimum provider-neutral structures and behavior needed to represent and enforce:

1. Verification identity.
2. Verification subject identity.
3. Relationship to Assignment.
4. Relationship to Attempt where applicable.
5. Verifier identity.
6. Explicit verification criteria.
7. Evidence references.
8. Verification method.
9. Verification result.
10. Verification timestamp.
11. Historical supersession where needed.
12. Independent-verifier enforcement where required.

## MINIMUM VERIFICATION RECORD

The minimum Verification record must preserve:

- verification_id;
- assignment_id;
- attempt_id where applicable;
- subject;
- verifier;
- criteria;
- evidence_refs;
- method;
- result;
- created_at;
- supersedes_verification_id where applicable.

The exact field names may vary only if implementation conventions clearly justify an equivalent representation.

No additional generalized subsystem is authorized merely because additional fields might be useful later.

## VERIFICATION SUBJECT

Verification must bind to the exact subject actually evaluated.

The subject representation must be sufficient to distinguish one immutable result from another.

Examples may include:

- commit SHA;
- file digest;
- artifact digest;
- immutable result identifier;
- other deterministic identity appropriate to the result type.

A mutable path, branch name, workspace name, issue number, or human-readable label alone is insufficient if it can later refer to different content.

Preserve:

CHANGED ARTIFACT MUST NOT INHERIT VERIFICATION AUTOMATICALLY.

Do not create a generalized artifact registry.

Use the smallest subject representation necessary to prove identity.

## RESULT VOCABULARY

Slice 2 result values are limited to:

PASS
FAIL
INCONCLUSIVE

Absence of a Verification record means:

NOT VERIFIED / NO VERIFICATION RECORDED

Absence must not be silently mapped to PASS, FAIL, INCONCLUSIVE, zero, or success.

## VERIFICATION METHOD

Verification method must distinguish at minimum between the nature of the proof performed.

The implementation does not need a broad taxonomy.

It must, however, preserve enough information to avoid collapsing:

DETERMINISTIC VERIFICATION

into

MODEL / HUMAN REVIEW.

Where exact correctness is available through deterministic evidence, model judgment must not be represented as equivalent proof.

## EXPLICIT CRITERIA

Verification must evaluate explicit criteria.

A Verification PASS cannot exist without criteria that identify what was required to pass.

Criteria may be represented directly or through a stable reference where repository conventions make that smaller and clearer.

Do not invent a generalized specification subsystem.

## EVIDENCE REFERENCES

Verification evidence must be explicit.

EvidenceRef remains a reference/value concept, not a blob-storage subsystem.

Evidence may reference:

- test result;
- command result;
- file;
- digest;
- repository state;
- structured measurement;
- review artifact;
- other bounded evidence.

Missing required evidence must not produce PASS.

Evidence references must not silently point to mutable content where immutable identity is required to support the verdict.

## VERIFIER IDENTITY

Every Verification must record verifier identity.

Verifier identity must be distinguishable from:

- Assignment identity;
- Worker identity;
- Attempt identity;
- harness identity;
- model identity.

The implementation may reuse an existing durable worker/actor identity where appropriate.

Do not create a generalized identity-management subsystem.

## INDEPENDENT VERIFICATION

Where independent verification is required, independence must be structurally enforceable.

At minimum:

the same logical worker that produced the relevant Attempt must not be permitted to satisfy an independent Verification requirement for that Attempt.

Fail closed when required independence cannot be established.

Do not infer independence merely from:

- a different session;
- a different run;
- a different process;
- a different chat;
- a different reviewer label.

A different harness or model may contribute to independence, but harness/model difference alone is not sufficient unless explicitly required by policy.

Slice 2 does not need a generalized independence-policy language.

The smallest deterministic predicate that proves the bounded requirement is preferred.

## HISTORICAL IMMUTABILITY

Verification records are historical facts.

A later Verification must not silently mutate or replace an earlier Verification.

If a later Verification supersedes an earlier one, the historical relationship must remain recoverable.

A changed subject requires a new Verification.

A changed verdict must not rewrite the prior verdict in place.

Preserve:

HISTORICAL VERIFICATION ≠ CURRENT VERIFICATION STATUS.

## ATTEMPT RELATIONSHIP

Verification must not become part of Attempt completion state.

Attempt execution may finish successfully without any Verification existing.

Verification may occur after the Attempt.

Verification failure must not rewrite historical Attempt execution facts.

The relationship is:

ATTEMPT PRODUCES OR REFERENCES A RESULT

VERIFICATION EVALUATES AN IDENTIFIED SUBJECT

not:

ATTEMPT SUCCESS = VERIFIED SUCCESS.

## PROVIDER NEUTRALITY

No provider-specific logic belongs in the Slice 2 Verification core.

The Verification seam must not depend on:

- Codex;
- Claude;
- Antigravity;
- Muse;
- Paperclip;
- any single provider;
- any single model;
- any single orchestration system.

Provider/harness/model identity may appear as provenance where relevant.

It must not define Verification semantics.

## PAPERCLIP / DONOR BOUNDARY

Recent Paperclip review confirms that generalized orchestration, review routing, worktree coordination, budgeting, run management, approval UI, and effect-policy machinery already exist externally.

Slice 2 must therefore NOT become a generic review-workflow engine.

The Reliability Lab concern is narrower:

- exact verification subject;
- explicit evidence;
- independent verifier identity;
- durable verdict;
- immutable history.

Preserve:

PROCESS STEP ≠ GOVERNED TRUTH

REVIEW STAGE ≠ INDEPENDENT VERIFICATION RECORD

## DATA POLICY

Recent provider research established:

MODEL AVAILABLE ≠ MODEL AUTHORIZED

CAPACITY AVAILABLE ≠ DATA POLICY ACCEPTABLE

Data-policy compatibility is a future qualification concern.

It is not part of Slice 2 Verification implementation.

No data-policy schema is authorized by this gate.

## DETERMINISTIC ACCEPTANCE TESTS

Slice 2 implementation must include tests proving at minimum:

1. A completed Attempt does not automatically create Verification PASS.

2. A valid Verification can reference the intended Assignment and Attempt.

3. Verification records explicit criteria.

4. Verification records explicit evidence references.

5. Verification records verifier identity.

6. Verification records the exact verification subject.

7. PASS is rejected when required evidence is absent.

8. Result values outside PASS / FAIL / INCONCLUSIVE are rejected.

9. An independent-verification requirement rejects the worker responsible for the Attempt.

10. Independence failure occurs before a valid independent Verification can be created.

11. A different immutable subject requires a distinct Verification.

12. A later Verification does not silently overwrite an earlier Verification.

13. Supersession preserves historical Verification identity.

14. Verification creation does not create Human Acceptance.

15. Verification creation does not create Promotion.

16. Provider-specific adapters are not required to exercise the Verification seam.

17. Worker self-report alone cannot manufacture PASS.

18. Mutable labels alone cannot substitute for required immutable subject identity.

Tests must prove behavior, not merely object construction.

## EXPLICIT NON-GOALS

Slice 2 does NOT authorize:

- Human Disposition;
- Human Acceptance implementation;
- Promotion;
- merge automation;
- deployment automation;
- approval UI;
- review routing;
- autonomous reviewer assignment;
- provider adapters;
- provider routing;
- fallback routing;
- retries;
- schedulers;
- queues;
- dashboards;
- databases;
- services;
- daemons;
- orchestration;
- generalized artifact registry;
- generalized evidence store;
- generalized specification system;
- generic task management;
- workflow engine;
- policy language;
- data-policy engine;
- capacity router;
- skill installation;
- Agent Skills integration;
- Paperclip integration;
- Muse integration;
- Graphify integration;
- Ponytail integration;
- OmniRoute integration;
- context compression;
- repository graph authority.

## LOCATION / STRUCTURAL RULE

Slice 2 must extend the existing neutral internal Assignment Ledger implementation.

Do not create or redefine a numbered public Reliability Lab.

Do not modify project-wide configuration unless strictly necessary for the bounded Slice 2 implementation.

If project-wide configuration change is claimed necessary, return to Governance before making it.

## COMPLEXITY RULE

COMPLEXITY MUST PAY RENT.

Prefer:

- files first;
- narrow immutable records;
- references over duplicated evidence;
- deterministic predicates;
- explicit failure;
- one authoritative home per fact.

If the implementation begins requiring generalized orchestration, workflow management, persistent services, routing, databases, or broad integration infrastructure:

STOP.

Return to Governance for RESCOPE.

## IMPLEMENTATION AUTHORITY

Once this gate is committed, implementation authority is limited to:

SLICE 2 — VERIFICATION RECORD + INDEPENDENT VERIFICATION BOUNDARY

Implementation must remain within the frozen invariants, acceptance tests, structural rules, and non-goals above.

No later ledger slice is authorized.

## GOVERNANCE STATUS

SLICE 1:

ACCEPTED

SLICE 2 DESIGN DIRECTION:

ACCEPTED

SLICE 2 IMPLEMENTATION GATE:

FROZEN BY THIS RECORD ON COMMIT

SLICE 2 IMPLEMENTATION:

AUTHORIZED ONLY AFTER THIS RECORD IS COMMITTED

HUMAN DISPOSITION:

NOT AUTHORIZED

PROMOTION:

NOT AUTHORIZED

AUTONOMOUS ORCHESTRATION:

NOT AUTHORIZED

BROADER CONTROL-PLANE IMPLEMENTATION:

NOT AUTHORIZED
