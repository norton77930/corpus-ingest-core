# Spec033 Safety Checklist

- [x] No upstream Hermes source is imported, executed, or packaged under `src/`.
- [x] No local `.env`, Hermes configuration, credentials, sessions, logs, or private endpoint was read.
- [x] No Docker, Compose, WSL, listener, MCP transport, provider, inference, C6, or predecessor verifier was run.
- [x] Acquisition rejects redirects, non-200 responses, oversized data, missing/non-regular targets, identity mismatch, and Git blob mismatch.
- [x] Source expansion beyond the fixed allowlist is prohibited; unresolved graph terminates fail closed.
- [x] `runtime_status=not_run` and `live_actions_authorized=false` are fixed in all public outcomes.
- [x] The final verifier is sealed as reviewed evidence, disables ambient pytest plugin autoload and repository `conftest.py` loading before sentinel startup, and cannot authorize Docker, Hermes, provider, inference, or predecessor execution.
- [x] Acquisition cleanup failures are explicit and retain the publication lock as a recovery marker; no clean rollback is claimed while residual paths remain.
