# AI SYSTEMS RELIABILITY LAB
# CROSS-HARNESS / GOVERNANCE
# RESCOPE DECISION V001

## PURPOSE

This record closes the initial cross-harness qualification, reconciliation, and donor-research sequence and records the resulting governance decision.

Decision:

**RESCOPE**

A meaningful custom gap exists.

However, the evidence does not justify building a broad cross-harness orchestration framework.

The authorized next design target is a much smaller provider-neutral primitive centered on durable assignment truth, attempts, authority, evidence, verification, and human disposition.

No implementation is authorized by this record.

## AUTHORITATIVE INPUTS

This decision is based on:

1. `docs/governance/CROSS_HARNESS_READ_ONLY_REVIEW_V001.md`
2. Q2 repository-truth reconciliation concluding:
   **END-TO-END ENFORCEMENT NOT PRESENT**
3. Cross-harness donor autopsy concluding:
   **RESCOPE**

## CORE FINDING

Existing donor systems substantially solve:

- harness invocation normalization;
- subprocess execution;
- provider permission mapping;
- durable continuation patterns;
- isolated attempts;
- deterministic and independent verification;
- worker-not-tester patterns;
- raw evidence preservation.

The surviving custom gap is a durable provider-neutral record that keeps these concepts explicitly separate:

- ASSIGNMENT
- WORKER
- SESSION
- ATTEMPT
- AUTHORITY
- EVIDENCE
- VERIFICATION
- HUMAN DISPOSITION

## RESCOPE DECISION

The broader cross-harness runner or orchestration concept is:

**NOT AUTHORIZED**

The authorized next design target is:

**MINIMAL PROVIDER-NEUTRAL ASSIGNMENT LEDGER**

Working description:

A durable record of what work was authorized, who or what attempted it, through which execution surface and session, under what authority, what evidence resulted, what an independent verifier concluded, and what the human ultimately accepted.

## COMMODITY LAYERS

Presumptively reuse rather than rebuild:

- harness invocation normalization;
- provider CLI execution;
- timeout and process cleanup;
- provider permission mapping;
- continuity patterns;
- verification patterns;
- Antigravity adapter behavior where safely extractable.

Primary donor posture:

- `twaldin/harness` — ADOPT candidate
- `SUNRNEHUI/agent-harness` — EXTRACT
- Harness Agent Benchmark Runner — DONOR
- AOa / `multi-agent-orchestration` — EXTRACT
- MCO — DONOR

## MINIMUM CUSTOM RESPONSIBILITIES

The proposed custom layer may own:

- durable assignment identity;
- assignment objective and status;
- explicit authority envelope;
- worker identity/reference;
- harness identity/reference;
- session identity/reference;
- attempt identity;
- attempt state;
- evidence references;
- retry and supersession relationships;
- verifier identity and verdict reference;
- final human disposition;
- append-only state-transition history.

## NON-RESPONSIBILITIES

The proposed custom layer should not own unless later justified:

- provider subprocess infrastructure;
- generalized provider adapters;
- model routing;
- task scheduling;
- autonomous retry;
- agent teams;
- queues;
- dashboards;
- daemons;
- control planes;
- distributed state;
- benchmark infrastructure;
- automatic consensus.

## CORE ARCHITECTURAL TEST

The next design phase must answer:

Can the assignment ledger sit above an existing invocation normalizer and an extracted Antigravity adapter while remaining unaware of whether a given attempt executed through Claude, Codex, or Antigravity except through recorded identity metadata?

If substantial provider-specific branching leaks into the ledger, the proposed boundary has failed and must be reconsidered.

## GOVERNING DOCTRINE

Preserve:

**WORKER ≠ SESSION ≠ ATTEMPT ≠ ASSIGNMENT**

**TECHNICAL CAPABILITY ≠ EXECUTION-SURFACE PERMISSION ≠ BUSINESS AUTHORITY ≠ CORRECTNESS**

**DECLARED ≠ DELIVERED ≠ PROVEN**

**SHARED MEMORY ≠ SHARED TRUTH**

**ARTIFACT HANDOFF > TRANSCRIPT HANDOFF**

**QUALIFIED HARNESS ≠ ORACLE**

**MECHANISM EXISTS ≠ MECHANISM IS ON THE MANDATORY EXECUTION PATH**

**UNKNOWN REMAINS UNKNOWN**

**NOT_MEASURED ≠ ZERO**

Human acceptance remains explicit.

## COMPLEXITY RULE

**COMPLEXITY MUST PAY RENT**

Prefer:

- files over databases;
- references over copied evidence;
- append-only events over hidden mutable history;
- deterministic verification over model judgment where possible;
- one authoritative home per fact;
- explicit human disposition over inferred completion.

## NEXT PHASE

Authorized next phase:

**MINIMAL ASSIGNMENT LEDGER ARCHITECTURE DESIGN**

This phase may:

- propose the minimum data model;
- propose artifact/file layout;
- define lifecycle and state transitions;
- define interfaces with invocation and verification layers;
- identify invariants;
- identify failure modes;
- identify what should not be built;
- recommend GO / NO-GO / RESCOPE for implementation.

It may not:

- implement code;
- install donors;
- fork donors;
- modify Lab 03;
- create databases;
- create services;
- authorize autonomous execution.

## IMPLEMENTATION GATE

Implementation remains:

**NOT AUTHORIZED**

Architecture design must return to Cross-Harness / Governance with:

1. minimum schema;
2. state-transition model;
3. authoritative-state rules;
4. provider-neutral interface boundary;
5. donor reuse plan;
6. required invariants;
7. deterministic verification strategy;
8. complexity and burden assessment;
9. portfolio value assessment;
10. GO / NO-GO / RESCOPE recommendation.

## STATUS

**READ-ONLY REPOSITORY REVIEW QUALIFICATION: COMPLETE**

**CROSS-HARNESS COMPARISON: COMPLETE**

**Q2 REPOSITORY-TRUTH RECONCILIATION: COMPLETE**

**DONOR AUTOPSY: COMPLETE**

**GOVERNANCE BUILD DECISION: RESCOPE**

**BROAD CROSS-HARNESS ORCHESTRATION BUILD: NOT AUTHORIZED**

**MINIMAL ASSIGNMENT LEDGER DESIGN: AUTHORIZED**

**IMPLEMENTATION: NOT AUTHORIZED**
