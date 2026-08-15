# Spec033 Requirements Checklist

- [x] Exact fixed 17-file allowlist acquired from the official repository commit.
- [x] Commit, tree, regular blob, Git blob SHA, SHA-256, length, and LICENSE provenance are persisted and revalidated.
- [x] Pinned `pyproject.toml` proves only commit project version `0.19.0` and its declared CLI entrypoints.
- [x] Static audit distinguishes bounded loader edges from complete loader/register/hook proof.
- [x] Dynamic module execution, unresolved entrypoints, and config/credential/provider order fail closed as `BLOCKED_SOURCE_GRAPH`.
- [x] `plugins list` manifest inspection is not treated as loader proof.
- [x] Receipt is fixed-schema and source-free; all runtime status remains `not_run`.
- [x] The authoritative Spec029–032 chain is structurally bound through Spec032's pinned verifier inventory, predecessor manifest, and reviewed manifest; Spec032-owned bytes are revalidated, shared pointers are resealed by Spec033, and predecessors remain unedited and unexecuted.
- [x] The reviewed manifest includes the final verifier and is sealed by a detached review root designed to be shared by both required reviews and the one Main-only final verifier receipt; the root will be regenerated after the current bounded repairs.
- [ ] Code and architecture reviews, then one Main-only final verifier run.
