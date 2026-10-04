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
and exact subject identity. The currently supported subject forms are full commit
SHA and SHA-256 content digest; these are implementation support, not a permanent
exhaustive taxonomy. An evidence reference can be an exact full commit SHA without
a redundant digest, or a locator with a SHA-256 content identity. A mutable path or
label alone cannot identify the evidence content supporting a verdict. EvidenceRef
identifies evidence; accepting a syntactically valid identity does not prove the
referenced evidence true. This seam does not resolve or recompute evidence.

Criteria are explicit durable values identifying what was evaluated, with no
mechanical relationship to Assignment `verification_requirements`. PASS requires
evidence. The caller supplies the actual proof method: DETERMINISTIC, MODEL_REVIEW,
HUMAN_REVIEW, or
WORKER_SELF_REPORT. Method distinctions survive persistence; this seam records proof
references and does not execute tests, inspect referenced bytes, authenticate actor
identity, or turn model judgment into deterministic proof. The WORKER_SELF_REPORT
method cannot produce PASS; recording a worker's report alone does not establish proof.

`independent_required` defaults to true and is persisted explicitly. When independent
Verification is required for a related Attempt, its logical `worker_id` must be
known and different from `verifier`; the responsible worker is rejected and unknown
worker provenance fails closed. When independence is not required, worker identity
alone does not prohibit PASS with explicit criteria, evidence, and a supported proof
method. Verification without an Attempt relationship is not automatically subject
to Attempt-worker independence. The caller explicitly supplies the requirement;
Slice 2 does not determine upstream independence policy or assign reviewers. Not
all Verification is independent Verification.

There is no implicit current status: completion creates no Verification, and missing
Verification is reported as missing. Reads retrieve an exact Verification ID. New
subjects or verdicts require new IDs. Optional `supersedes_verification_id` references
an existing Verification in the same Assignment, preserving both historical records.
Multiple later records may coexist; Slice 2 selects no canonical current verdict.
Future Acceptance must reference an exact Verification identity unless later
Governance authorizes different semantics.
Verification never updates an Attempt or creates acceptance or promotion. Immutability
is enforced through the ledger API and exclusive record creation, following Slice 1's
file model; direct external edits to ledger files are outside this bounded API.

Run the Slice 1 and Slice 2 tests from the repository root:

```sh
python3 -m pytest -q internal/assignment_ledger/tests/test_authority_seam.py
python3 -m pytest -q internal/assignment_ledger/tests/test_verification_seam.py
```

These tests implement and exercise requirements from the frozen governance gate;
the tests themselves are not governance authority. Slice 2 tests named `test_gate_01`
through `test_gate_18` map to the gate's eighteen acceptance requirements. Tests
named `test_clarification_01` through `test_clarification_06` cover the six
worker-provenance requirements. Additional
tests cover relationship mismatch, explicit method distinctions, malformed values,
supersession validity, and provenance rejection before invocation.
