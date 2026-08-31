# V0.3 Execution Anomalies

- Initial local runtime was unavailable; Ollama was installed locally at $0.
- Concurrent workloads and an orphaned Ollama worker confounded early smoke tests; the worker was stopped and the runtime restarted.
- Free-form decoding failed structured-output smoke testing. Schema-constrained decoding passed 3/3 and was frozen before clean generation.
- A pre-freeze baseline trace and an initial candidate trace became contaminated by appended records. Both are preserved unchanged and excluded.
- Clean baseline and candidate reruns each produced exactly 30 records in separate directories.
- Semantic launch required a missing-import repair and passing the already frozen model identifier; neither changed an experiment variable. One clean candidate semantic response was unavailable and retained as such.
- No anomaly changed the dataset, prompts, final model, constrained schema, evaluators, thresholds, or release-gate logic.
