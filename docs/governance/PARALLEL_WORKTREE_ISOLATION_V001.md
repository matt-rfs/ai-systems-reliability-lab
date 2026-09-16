# AI SYSTEMS RELIABILITY LAB
# CROSS-HARNESS / GOVERNANCE
# PARALLEL WORKTREE ISOLATION V001

## PURPOSE

This record captures a governance correction discovered during parallel Reliability Lab work.

Two authorized workstreams were operating against the same mutable repository checkout and branch:

- Lab 03 Cost / Quality Router
- Cross-Harness / Governance / Harness R&D

Both were legitimately advancing `main`.

Lab 03 execution packets depended on exact-HEAD authority.

Unrelated governance commits therefore invalidated Lab 03 execution packets even though those commits did not change Lab 03 execution semantics.

The resulting failures were correct enforcement of the exact-HEAD gate.

The defect was workspace topology.

## CORE LESSON

**SHARED REPOSITORY ≠ SHARED MUTABLE EXECUTION SURFACE**

When parallel governed workstreams may both write to the same repository, they must not share one mutable checkout if any active workstream depends on exact-HEAD execution authority.

## DURABLE OPERATING RULE

**PARALLEL GOVERNED WORKSTREAMS MUST NOT SHARE A MUTABLE CHECKOUT WHEN ANY ACTIVE WORKSTREAM DEPENDS ON EXACT-HEAD EXECUTION AUTHORITY.**

For concurrent write-capable governed workstreams, prefer:

- one branch per active workstream;
- one Git worktree per active workstream;
- one local working directory per active workstream;
- exact-HEAD authority pinned to the workstream branch HEAD.

`main` should function primarily as an integration and accepted-truth branch rather than as the shared mutable execution surface for concurrent governed implementation work.

## COROLLARIES

1. Exact-HEAD packets should pin to the relevant workstream branch HEAD.

2. Unrelated commits in another workstream should not require routine repinning of an isolated workstream.

3. Accepted work should merge deliberately into `main`.

4. Repeated exact-HEAD repinning caused by unrelated concurrent work is a workspace-topology smell.

5. Worktree isolation is preferred over repeated packet regeneration when parallel governed work is expected.

6. Repository identity does not imply shared execution authority.

7. Branch separation alone is insufficient if multiple governed workstreams continue to operate through the same mutable checkout.

## LAB 03 ISOLATION

Dedicated Lab 03 branch:

`lab03/live-v002`

Dedicated Lab 03 worktree:

`/Users/Matt/.codex/.chatgpt-projects/g-p-6a23bb6d9b68819182ddea5285e32191/ai-systems-reliability-lab-lab03`

Lab 03 branch base at isolation:

`f8eacb9a74a1060eae38ea58a4a1fae6c4935db4`

The uncommitted Lab 03 live-plumbing files were copied into the dedicated worktree and SHA-256 verified byte-for-byte before removal from the shared main checkout.

Lab 03 implementation and execution now continue only from the dedicated Lab 03 worktree unless Governance explicitly changes that topology.

Do not direct Lab 03 implementation, remediation, canary execution, or exact-HEAD execution commands back into the shared main checkout.

## SHARED MAIN CHECKOUT

The original checkout remains:

`/Users/Matt/.codex/.chatgpt-projects/g-p-6a23bb6d9b68819182ddea5285e32191/ai-systems-reliability-lab`

This checkout may continue to serve the Cross-Harness / Governance workstream.

If additional concurrent write-capable workstreams begin depending on exact-HEAD authority, they should receive their own branches and worktrees rather than sharing this mutable checkout.

## EXACT-HEAD INTERPRETATION

The observed failures:

`EXPECTED HEAD != CURRENT HEAD`

were not false positives.

Exact-HEAD enforcement behaved correctly.

An execution packet bound to one repository state must not silently continue after HEAD changes.

The correction is to isolate the workstream execution surface, not weaken the exact-HEAD gate.

Therefore:

**EXACT-HEAD ENFORCEMENT FAILURE ≠ WORKSPACE-TOPOLOGY FAILURE**

and:

**DO NOT WEAKEN A CORRECT GATE TO COMPENSATE FOR A SHARED MUTABLE WORKSPACE**

## RELATION TO ASSIGNMENT / AUTHORIZATION / ATTEMPT

This finding reinforces the broader Reliability Lab distinction between repository identity and execution authority.

A repository may be shared while execution authority remains workstream-specific.

Branch, worktree, checkout, Assignment, Authorization, Attempt, and exact HEAD are separate facts.

A future ledger must not infer:

shared repository
=
shared execution surface

or:

same branch name
=
same authorized Attempt context

## CURRENT LAB 03 STATUS

Lab 03 Freeze A V002 remains authoritative.

The live execution plumbing exists, but independent review required two corrections before canary execution:

1. truthful failure-path call_count telemetry;
2. expanded direct live-plumbing test coverage.

Those corrections are being handled exclusively in:

`lab03/live-v002`

No V002 canary inference has executed.

Attempt 01 remains unused.

No measured cases have executed.

No Freeze B exists.

## GOVERNANCE STATUS

**PARALLEL WORKTREE ISOLATION RULE: ADOPTED**

**EXACT-HEAD ENFORCEMENT: PRESERVED**

**LAB 03 DEDICATED WORKTREE: ACTIVE**

**LAB 03 EXECUTION IN SHARED MAIN CHECKOUT: NOT AUTHORIZED**

**MAIN: INTEGRATION / ACCEPTED-TRUTH SURFACE**

**WEAKENING EXACT-HEAD AUTHORITY: NOT AUTHORIZED**
