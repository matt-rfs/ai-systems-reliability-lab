# AI SYSTEMS RELIABILITY LAB
# CROSS-HARNESS / GOVERNANCE
# MINIMAL ASSIGNMENT LEDGER IMPLEMENTATION GATE V001

## PURPOSE

This record converts the accepted Minimal Assignment Ledger architecture into a bounded implementation gate.

The architecture direction is accepted.

Implementation is authorized only under the frozen invariants and bounded Slice 1 scope defined below.

This record does not authorize broad ledger implementation or autonomous orchestration.

## GOVERNING INPUTS

Authoritative RESCOPE decision:

`docs/governance/CROSS_HARNESS_RESCOPE_DECISION_V001.md`

Commit:

`caec14b797ad0ab9d0f6ebaff63202e7ab71f76e`

Accepted architecture packet:

`AI SYSTEMS RELIABILITY LAB / MINIMAL ASSIGNMENT LEDGER ARCHITECTURE / ARCHITECTURE PACKET V001`

Architecture conclusion:

**The provider-neutral ledger boundary is coherent.**

The ledger may record harness identity as provenance, but provider-specific execution behavior belongs below the ledger boundary.

## ARCHITECTURE DECISION

Architecture status:

**GO**

The architecture does not require redesign before implementation.

Implementation must preserve the three frozen invariants below.

## FROZEN INVARIANT 1
## CANONICAL AUTHORIZATION SEMANTICS

The canonical concept is:

**Authorization**

Authorization is the immutable historical basis under which an Assignment or Attempt is permitted to execute.

Each executable Attempt MUST reference the Authorization under which it started.

At minimum, Authorization must preserve:

- authorization identity;
- authorization basis;
- source or governance reference;
- authorized scope;
- relevant execution constraints;
- grant timestamp;
- human or governance authority where applicable.

Terms such as authority envelope, authority profile, or permission profile may be used descriptively by lower execution layers, but MUST NOT create competing authoritative concepts inside the ledger.

For historical truth, the Authorization applicable when an Attempt started must remain recoverable even if later governance or permission rules change.

**EXECUTED ≠ AUTHORIZED**

## FROZEN INVARIANT 2
## MATERIAL POST-ATTEMPT CHANGES REQUIRE SUPERSESSION

Once any Attempt has started against an Assignment, the following Assignment properties MUST NOT be materially rewritten in place:

- objective;
- scope;
- constraints;
- expected outputs;
- verification requirements;
- execution authority.

A material change requires either:

1. an explicitly superseding Assignment; or
2. an explicitly versioned revision whose relationship to the attempted Assignment is durable and unambiguous.

Historical Attempts remain attached to the Assignment definition they actually executed against.

A later revision MUST NOT retroactively redefine what an earlier Attempt was asked or authorized to do.

**HISTORICAL ATTEMPT TRUTH IS IMMUTABLE**

**MATERIAL SCOPE CHANGE AFTER ATTEMPT START ≠ ORDINARY EDIT**

## FROZEN INVARIANT 3
## AUTHORIZATION MUST BE ON THE MANDATORY PRE-EXECUTION PATH

The implementation MUST prove structurally and deterministically that Authorization is checked before provider execution begins.

It is insufficient for:

- an Authorization object to exist;
- a validation function to exist;
- unit tests for that function to pass;
- an Attempt merely to contain an authorization reference.

The actual execution path MUST require valid Authorization before invocation reaches the provider-normalization or transport boundary.

Required success path:

Valid Authorization
→ Attempt permitted
→ Invocation boundary may be reached

Required failure path:

Missing or invalid Authorization
→ Attempt blocked
→ Invocation boundary is NOT called

This must be demonstrated by deterministic test evidence.

**MECHANISM EXISTS ≠ MECHANISM IS ON THE MANDATORY EXECUTION PATH**

## FIRST IMPLEMENTATION SLICE

Governance authorizes one bounded implementation slice:

**SLICE 1 — ASSIGNMENT + AUTHORIZATION + ATTEMPT AUTHORITY SEAM**

The purpose of Slice 1 is to prove the minimum durable authority boundary before broader ledger capabilities are added.

Slice 1 may implement only what is necessary to represent and deterministically verify:

- Assignment identity and declared intent;
- Authorization identity and historical basis;
- Attempt identity;
- Attempt-to-Assignment relationship;
- Attempt-to-Authorization relationship;
- immutable historical Attempt records;
- provider-neutral pre-execution Authorization check;
- normalized invocation boundary stub or test double;
- deterministic proof that unauthorized execution cannot reach invocation.

## SLICE 1 NON-GOALS

Slice 1 does NOT authorize implementation of:

- Verification objects;
- Human Disposition objects;
- Antigravity adapter integration;
- Claude adapter implementation;
- Codex adapter implementation;
- donor installation;
- donor forking;
- model routing;
- retries;
- scheduling;
- queues;
- dashboards;
- daemons;
- services;
- databases;
- autonomous execution;
- workflow engines;
- distributed state;
- multi-agent orchestration.

A test double or minimal provider-neutral invocation interface is sufficient for proving the authority seam.

## REQUIRED DETERMINISTIC TESTS

Slice 1 must include tests proving at minimum:

1. An Attempt references exactly one Assignment.
2. An executable Attempt references an existing Authorization.
3. Valid Authorization permits the invocation boundary to be reached.
4. Missing Authorization blocks execution before invocation.
5. Invalid or out-of-scope Authorization blocks execution before invocation.
6. The invocation boundary is not called when Authorization fails.
7. Attempt IDs are immutable and not reused.
8. An Attempt remains historically attached to the Assignment and Authorization under which it began.
9. Material post-attempt Assignment changes cannot silently rewrite historical Attempt meaning.
10. No provider-specific branching is required inside the ledger authority seam.

## PERSISTENCE POSTURE

Default:

**FILES FIRST**

No database is authorized for Slice 1.

The implementation should prefer the smallest durable artifact structure that satisfies the invariants.

Do not introduce infrastructure merely for convenience.

## PROVIDER BOUNDARY

Slice 1 must remain provider-neutral.

The ledger may record provenance such as:

- harness_id;
- adapter_id;
- adapter_version;
- provider_session_ref;
- model.

The authority seam MUST NOT branch behavior based on Claude, Codex, Antigravity, or another provider.

Provider-specific behavior belongs below the invocation boundary.

## ACCEPTANCE RULE

Slice 1 is not accepted merely because:

- code runs;
- unrelated tests pass;
- an Authorization structure exists;
- an Attempt records an Authorization reference;
- a worker reports success.

Acceptance requires deterministic evidence that:

> An executable Attempt cannot reach the invocation boundary without valid Authorization.

The implementer does not define success.

Independent verification remains required before Governance accepts the slice.

## AUTHORITY

Implementation authority granted by this record is limited to:

**SLICE 1 — ASSIGNMENT + AUTHORIZATION + ATTEMPT AUTHORITY SEAM**

Nothing in this record automatically authorizes later ledger slices.

Further capabilities require separate governance acceptance.

## STATUS

**MINIMAL ASSIGNMENT LEDGER ARCHITECTURE: GO**

**SLICE 1 IMPLEMENTATION: AUTHORIZED**

**AUTHORIZATION SEMANTICS: FROZEN**

**POST-ATTEMPT MATERIAL MUTATION: PROHIBITED**

**MANDATORY PRE-EXECUTION AUTHORIZATION PATH: REQUIRED**

**BROADER LEDGER IMPLEMENTATION: NOT AUTHORIZED**

**AUTONOMOUS ORCHESTRATION: NOT AUTHORIZED**
