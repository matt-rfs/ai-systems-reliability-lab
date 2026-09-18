# AI SYSTEMS RELIABILITY LAB
# CROSS-HARNESS / GOVERNANCE
# ASSIGNMENT LEDGER POST-SLICE-1 REASSESSMENT V001

## PURPOSE

This record reassesses the Minimal Assignment Ledger after accepted Slice 1 implementation.

Slice 1 has proven the bounded authority seam:

Assignment
→ Authorization
→ Attempt
→ mandatory pre-execution authority check.

The purpose of this reassessment is to determine whether another implementation slice is justified now, and if so, which reliability gap should be prioritized.

No implementation is authorized by this record unless explicitly stated in the final disposition.

## AUTHORITATIVE CURRENT STATE

Accepted Slice 1 implementation commit:

`bb92375bedd87ab3b47274e2e618698cdc212c87`

Slice 1 governance acceptance commit:

`2504bff5a8df3dfb1a34fa555746e4a9a3f3e109`

Parallel worktree isolation governance commit:

`faada3245af77b75de854928e4ce493c2b460c5b`

Slice 1 established:

- durable Assignment identity;
- durable Authorization identity;
- durable Attempt identity;
- Attempt-to-Assignment relationship;
- Attempt-to-Authorization relationship;
- mandatory Authorization before invocation;
- provider-neutral authority seam;
- immutable historical Attempt truth for the bounded slice.

Later ledger slices remain unauthorized.

## REASSESSMENT QUESTION

Now that Assignment + Authorization + Attempt is proven:

> What is the smallest next reliability gap worth formalizing?

The candidate answer may be:

- Verification;
- Human Disposition;
- Assignment supersession/versioning;
- Attempt evidence/provenance hardening;
- another narrower seam;
- or no additional implementation at this time.

Do not assume a sequential product roadmap.

Each candidate must independently justify its cost.

## EVALUATION CRITERIA

Each candidate should be assessed against:

1. demonstrated missing reliability seam;
2. direct connection to accepted Slice 1;
3. deterministic verifiability;
4. complexity burden;
5. donor overlap;
6. implementation independence;
7. portfolio value;
8. whether doctrine alone already solves the problem;
9. whether implementation would reduce ambiguity or merely create machinery;
10. whether the capability is required before a realistic governed end-to-end flow can be demonstrated.

Apply:

**COMPLEXITY MUST PAY RENT**

## CANDIDATE A
## VERIFICATION

Question:

Should independent Verification become the next first-class ledger concept?

Potential value:

- separates worker result from correctness judgment;
- preserves implementer ≠ verifier;
- records PASS / FAIL / INCONCLUSIVE independently from Attempt completion;
- supports deterministic verification where exact correctness is possible;
- gives the ledger a durable answer to what evidence was checked, by whom, and against what criteria.

Relevant doctrine:

**DECLARED ≠ DELIVERED ≠ PROVEN**

**IMPLEMENTER DOES NOT DEFINE SUCCESS**

**QUALIFIED HARNESS ≠ ORACLE**

Questions to answer:

- Is Verification currently missing in a way that limits the usefulness of Slice 1?
- Does Verification require a new first-class object, or could evidence references alone suffice?
- Can a minimum Verification slice be tested deterministically without building broader workflow machinery?
- Can verifier independence be represented without introducing worker orchestration?

## CANDIDATE B
## HUMAN DISPOSITION

Question:

Should explicit Human Disposition become the next first-class ledger concept?

Potential value:

- preserves verification ≠ acceptance;
- records ACCEPT / REJECT / REQUIRE_REWORK / CANCEL;
- prevents a verification PASS from silently becoming business or governance acceptance;
- establishes the terminal human-authority boundary.

Relevant doctrine:

**VERIFICATION ≠ ACCEPTANCE**

**HUMAN AUTHORITY REMAINS EXPLICIT**

Questions to answer:

- Is Human Disposition useful before Verification exists?
- Would implementing it now produce an object with insufficient evidence context?
- Is it better treated as the final step of a later end-to-end slice rather than the next isolated slice?

## CANDIDATE C
## ASSIGNMENT SUPERSESSION / VERSIONING

Question:

Should the deferred supersession path become the next implementation slice?

Current Slice 1 blocks unsafe material in-place mutation after an Attempt starts.

What is not yet implemented is the positive replacement path:

Material change
→ new Assignment or explicit revision
→ durable supersession relationship.

Potential value:

- allows safe evolution after an attempted Assignment;
- preserves prior Attempt meaning;
- turns a prohibition into a usable workflow.

Questions to answer:

- Is this needed immediately for realistic governed work?
- Can it remain deferred safely while Slice 1 is exercised?
- Does a minimal supersession implementation materially improve reliability or merely completeness?

## CANDIDATE D
## ATTEMPT EVIDENCE / PROVENANCE HARDENING

Question:

Should the next slice formalize what execution evidence an Attempt must retain?

Potential evidence classes include:

- invocation input reference;
- produced artifact reference;
- stdout/stderr reference;
- repository commit or diff;
- harness/model identity;
- session reference;
- runtime version;
- cost/usage telemetry where actually available;
- context transformation provenance;
- routing decision provenance.

Relevant donor-derived doctrine includes:

**PROVIDER FALLBACK ≠ SAME ATTEMPT**

**COMPRESSED CONTEXT ≠ ORIGINAL CONTEXT**

**CAPACITY AVAILABILITY ≠ AUTHORITY**

**ROUTING DECISION MUST BE ATTEMPT PROVENANCE**

**CONTEXT TRANSFORMATION MUST BE ATTEMPT PROVENANCE**

Questions to answer:

- Which evidence fields are required now versus future-facing?
- Would formalizing evidence before Verification reduce ambiguity?
- Is evidence best modeled as references/value objects rather than a subsystem?
- Can provenance hardening remain provider-neutral?

## CANDIDATE E
## STOP HERE FOR NOW

Question:

Should Governance decline another implementation slice until Slice 1 is exercised in a real bounded workflow?

Potential rationale:

- the authority seam is now proven;
- additional objects may be speculative without an actual governed assignment using the seam;
- a real use case may reveal which next concept is genuinely load-bearing;
- donor research can continue without growing implementation.

Questions to answer:

- Is the current ledger already sufficient for a meaningful bounded operational trial?
- Would a real assignment expose more useful evidence than another architecture exercise?
- Is the next best move observation rather than implementation?

## DONOR CONTEXT

Recent external donor research does not currently invalidate the accepted core.

Preserve:

- Agent Skills as future capability-package format donor;
- Graphify as repository-context mechanism donor;
- Ponytail as possible bounded minimalism experiment;
- OmniRoute as capacity/economics routing donor only;
- Omarchy as operator-surface and verification/admission donor.

None currently requires changing:

Assignment
→ Authorization
→ Attempt.

Donor mechanisms should not be assembled into a combined stack.

## CAPACITY MODEL BACKLOG

Future Cross-Harness design should distinguish capacity or availability at:

- provider;
- account/subscription;
- model.

Do not collapse these into one generic harness-availability state.

This is backlog architecture vocabulary only.

It does not authorize routing implementation.

## CONTEXT TRANSFORMATION BACKLOG

Before any context compression or transformation mechanism is considered for governed attempts, Attempt provenance must be capable of recording that transformation explicitly.

At minimum, future design should be able to distinguish:

- no transformation;
- transformation mechanism;
- transformation version or identity;
- whether original context remains recoverable.

This is backlog architecture doctrine only.

It does not authorize context compression.

## DECISION STANDARD

The next slice, if any, should be:

- independently useful;
- smaller than the broader ledger;
- deterministically testable;
- provider-neutral;
- files-first where persistence is required;
- free of orchestration machinery;
- justified by a demonstrated missing seam.

Do not select a candidate merely because it appears next in a conceptual pipeline.

## REQUIRED REASSESSMENT OUTPUT

The reassessment must compare candidates A through E and return exactly one advisory disposition:

**GO**

Authorize one narrowly specified next design/implementation slice.

**NO-GO**

Do not add another ledger slice at this time.

**RESCOPE**

A different reliability seam should take priority.

If GO is recommended, the output must identify:

- exactly one next slice;
- the minimum reliability question it answers;
- required invariants;
- explicit non-goals;
- deterministic acceptance criteria.

## CURRENT GOVERNANCE STATUS

**SLICE 1: ACCEPTED**

**ASSIGNMENT + AUTHORIZATION + ATTEMPT SEAM: PROVEN**

**LATER LEDGER SLICES: NOT AUTHORIZED**

**POST-SLICE-1 REASSESSMENT: ACTIVE**

**NO NEXT SLICE SELECTED YET**

**AUTONOMOUS ORCHESTRATION: NOT AUTHORIZED**
