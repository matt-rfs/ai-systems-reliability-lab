# Lab 04 — Human Authority Gate

This is the minimum deterministic implementation of the frozen `HUMAN_AUTHORITY_GATE_FREEZE_A_V001` experiment. It evaluates one bounded synthetic action against zero or one synthetic authorization record at the frozen timestamp, then mechanically maps the gate disposition to a synthetic executor state.

The implementation uses the Python standard library only. It does not call a model, a database, an external service, or a real messaging system. The exact experiment contract is [the Freeze A governance artifact](../../docs/governance/LAB04_HUMAN_AUTHORITY_GATE_FREEZE_A_V001.md).

Run the frozen matrix with:

```text
python labs/04-human-authority-gate/run_lab.py
```

The resulting compact report is written to `results/measured_results.json`.
