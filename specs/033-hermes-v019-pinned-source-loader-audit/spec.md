# Spec033: Hermes v0.19 Pinned Source Loader Audit

## Requirements

1. The bundle is exactly the fixed allowlist, proven against the official repository and pinned commit by tree/blob identity, SHA-256, length, and `LICENSE` provenance.
2. `pyproject.toml` bytes alone prove project version `0.19.0`; this is not a tag or release claim.
3. Static AST analysis must prove only bounded direct loader edges, distinguish `model_tools.py` import-time discovery from call-time CLI candidates, and fail closed for dynamic import, plugin top-level execution, incomplete dependency graph, config, credential, provider, prompt, tool, or inference ordering that cannot be proven from the allowlist.
4. Decisions are factory-issued and receipt projection rejects forged, copied, subclassed, mutated, or mismatched decision pairs without disclosing source bytes, local paths, URLs, exceptions, credentials, or arbitrary symbols.
5. Acquisition stages complete fsynced files under the target parent, requires fresh publication paths, validates before/after publication, and removes any partial bundle on failure. If cleanup itself fails, it raises an explicit cleanup error, reports only residual paths to the local caller, and retains the publication lock as a recovery marker rather than claiming a clean rollback.
6. The predecessor boundary must structurally bind the complete authoritative Spec029–032 evidence chain through Spec032's pinned verifier inventory, predecessor manifest, and reviewed manifest, without executing a predecessor verifier. Spec032-owned artifact bytes remain pinned; its four successor-mutable top-level pointers must remain inventory members and are sealed at their current bytes by Spec033. A detached review root seals the Spec033 reviewed-artifact manifest, including the final verifier, without a self-hash cycle; the verifier checks the seal before and after tests, regenerates and exact-compares the static receipt/verdict, and emits the detached root digest for Main to match against review evidence.

## Terminal state

`SPEC033_PINNED_SOURCE_AUDIT_IMPLEMENTED` and `BLOCKED_SOURCE_GRAPH`; `runtime_status=not_run`; `live_actions_authorized=false`.
