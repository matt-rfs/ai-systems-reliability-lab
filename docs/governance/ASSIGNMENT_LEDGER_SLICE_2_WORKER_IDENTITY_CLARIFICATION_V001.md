# AI SYSTEMS RELIABILITY LAB
# CROSS-HARNESS / GOVERNANCE
# ASSIGNMENT LEDGER SLICE 2
# WORKER IDENTITY CLARIFICATION V001

## PURPOSE

Clarify one prerequisite discovered during the first authorized Slice 2
implementation attempt.

The frozen Slice 2 gate requires structural independent-verifier enforcement:

the logical worker responsible for the relevant Attempt must not be permitted
to satisfy an independent Verification requirement for that Attempt.

Inspection of the accepted Slice 1 implementation established that Attempt
records currently preserve:

- attempt_id;
- assignment_id;
- authorization_id;
- started_at.

They do not currently preserve logical worker identity.

Therefore the frozen independence requirement cannot be truthfully enforced
without one additional bounded provenance fact.

## GOVERNANCE DISPOSITION

**CLARIFY / AUTHORIZE MINIMUM PREREQUISITE**

Slice 2 implementation may extend Attempt provenance with:

`worker_id`

or an equivalently named minimal logical-worker identifier consistent with
existing implementation conventions.

This authorization exists only to make the already-frozen independent
Verification invariant enforceable.

It does not authorize broader Assignment Ledger expansion.

## SEMANTICS

Worker identity and Attempt identity remain distinct.

Preserve:

WORKER ≠ ATTEMPT

WORKER ≠ SESSION

WORKER ≠ HARNESS

WORKER ≠ MODEL

A logical worker identifier is provenance identifying the actor responsible
for the Attempt.

It is not a session identifier, process identifier, chat identifier, harness
identifier, or model identifier.

## MINIMUM IMPLEMENTATION AUTHORITY

Slice 2 may:

1. record a minimal logical `worker_id` on an Attempt;
2. expose that recorded identity to the Verification independence check;
3. reject an independent Verification when verifier identity equals the
   Attempt worker identity;
4. fail closed when independent Verification is required but Attempt worker
   identity is absent or cannot be established;
5. add or update bounded tests necessary to prove those behaviors.

## BACKWARD / HISTORICAL TRUTH

Existing historical Attempt records lacking worker identity must not be
silently rewritten or assigned invented worker identities.

Unknown remains unknown.

Preserve:

UNKNOWN WORKER ≠ INDEPENDENT WORKER

An Attempt without durable worker identity may remain valid historical
execution truth.

However, where independent Verification is required, missing worker identity
must prevent creation of a valid independent Verification.

## COMPATIBILITY

The implementation should preserve accepted Slice 1 behavior with the
smallest compatible change.

It may make worker identity available as bounded Attempt provenance without
requiring migration of historical records.

Do not redesign Slice 1.

Do not weaken Authorization-before-invocation behavior.

## EXPLICIT NON-GOALS

This clarification does NOT authorize:

- a Worker registry;
- Worker lifecycle management;
- identity-provider integration;
- session management;
- harness registration;
- model registration;
- organizational roles;
- permissions expansion;
- authentication;
- authorization redesign;
- orchestration;
- reviewer routing;
- autonomous assignment;
- Human Acceptance;
- Promotion;
- database changes;
- generalized provenance infrastructure.

## TEST REQUIREMENTS

In addition to the frozen Slice 2 acceptance tests, implementation must prove:

1. Attempt worker identity can be durably recorded.
2. Attempt identity and worker identity remain distinct.
3. Required independent Verification rejects the same logical worker.
4. Required independent Verification fails closed when Attempt worker identity
   is unknown.
5. A different logical verifier may proceed when all other Verification
   requirements are satisfied.
6. Existing Slice 1 Authorization-before-invocation behavior remains passing.

## RELATION TO FROZEN GATE

This record does not supersede or weaken:

`docs/governance/MINIMAL_ASSIGNMENT_LEDGER_SLICE_2_IMPLEMENTATION_GATE_V001.md`

It supplies only the minimum missing prerequisite necessary to implement the
independence invariant already frozen by that gate.

If implementation requires anything broader than this bounded provenance fact:

STOP.

RETURN TO GOVERNANCE.

## GOVERNANCE STATUS

SLICE 2 IMPLEMENTATION GATE:

REMAINS FROZEN

MINIMUM ATTEMPT WORKER PROVENANCE:

AUTHORIZED

WORKER SUBSYSTEM:

NOT AUTHORIZED

SLICE 2 IMPLEMENTATION:

MAY RESUME AFTER THIS CLARIFICATION IS COMMITTED AND AVAILABLE IN THE
AUTHORIZED SLICE 2 WORKTREE
