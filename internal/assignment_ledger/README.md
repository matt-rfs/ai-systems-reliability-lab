# Bounded Assignment Ledger

The file-backed core records Assignment → Authorization → Attempt → Verification.
Authorization is still checked before an Attempt is recorded or invocation occurs.
`execute(..., worker_id="logical-worker")` optionally records the responsible actor.
Omitting this argument preserves historical unknown worker provenance. Worker IDs
identify logical actors, independently of attempts, sessions, harnesses, or models;
callers must supply that identity, never substitute a run or reviewer label.

`create_verification(Verification(...))` validates relationships before exclusively
creating a new JSON record. Every record includes a verifier, criteria, evidence
references, method, explicit PASS/FAIL/INCONCLUSIVE result, timezone-aware timestamp,
and exact subject identity (full commit SHA or SHA-256 content digest). Each evidence
reference includes a locator and the SHA-256 of its exact supporting content. A path
or label can locate evidence but cannot identify its content alone.

Criteria must match the related Assignment's recorded `verification_requirements`;
the verifier cannot substitute easier criteria. PASS requires evidence. The caller
supplies the actual proof method: DETERMINISTIC, MODEL_REVIEW, HUMAN_REVIEW, or
WORKER_SELF_REPORT. Method distinctions survive persistence; this seam records proof
references and does not execute tests, inspect referenced bytes, authenticate actor
identity, or turn model judgment into deterministic proof. Worker self-report cannot
produce PASS, including a responsible worker relabeling its report as another method.

`independent_required` defaults to true and is persisted explicitly. In that case
an existing related Attempt must have a known logical `worker_id` different from
`verifier`. Missing worker provenance fails closed. The boolean is the caller's
explicit bounded requirement, not an inferred policy or reviewer assignment. A
Verification without an Attempt can be recorded only with independence not required.
Such a record does not establish independent Verification of an Attempt.

There is no implicit current status: completion creates no Verification, and missing
Verification is reported as missing. Reads retrieve an exact Verification ID. New
subjects or verdicts require new IDs. Optional `supersedes_verification_id` references
an existing Verification in the same Assignment, preserving both historical records.
Verification never updates an Attempt or creates acceptance or promotion. Immutability
is enforced through the ledger API and exclusive record creation, following Slice 1's
file model; direct external edits to ledger files are outside this bounded API.

Run the frozen Slice 1 and Slice 2 checks from the repository root:

```sh
python3 -m pytest -q internal/assignment_ledger/tests/test_authority_seam.py
python3 -m pytest -q internal/assignment_ledger/tests/test_verification_seam.py
```

Slice 2 tests named `test_gate_01` through `test_gate_18` map to the gate's eighteen
acceptance requirements. Tests named `test_clarification_01` through
`test_clarification_06` cover the six worker-provenance requirements. Additional
tests cover relationship mismatch, explicit method distinctions, malformed values,
supersession validity, and provenance rejection before invocation.
