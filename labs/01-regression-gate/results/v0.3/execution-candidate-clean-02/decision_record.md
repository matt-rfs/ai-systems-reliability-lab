# Lab 01 V0.3 — Frozen Real Experiment Decision

## Release decision: FAIL

The candidate tested a plausible streamlined prompt against the frozen 30-case synthetic dataset. Both baseline and candidate achieved 30/30 deterministic passes, with zero schema, evidence, authority, or forbidden-action violations and zero case-level regressions or fixes.

The release is nevertheless blocked by the frozen factual-support threshold. The local semantic judge marked 15/30 baseline replies and 12/29 available candidate replies as unsupported, yielding 50.0% and 58.6% respectively—both below the required 90.0% minimum. The candidate semantic judge had one unavailable response, retained in the raw evidence.

## Human disposition

Do not release the candidate. No prompt, dataset, model, schema, evaluator, threshold, or gate variable was changed after the result. The logical follow-up is a separate evaluator-reliability investigation, not a rerun or tuning of this frozen experiment.
