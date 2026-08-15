# Contract: Managed Skill Synchronization

Exact allowlist:

- `corpus-episode-completion`
- `corpus-latest-episode-processing`
- `latest-episode-verified-research-report`
- `episode-verified-research-report`

Rules:

- Copy each complete source directory byte-for-byte.
- Compute deterministic SHA-256 tree digests from relative paths and file bytes.
- Identical source/target is no-op.
- Changed target is backed up, staged, and validated. Before live mutation, the helper persists a manifest in `applying` state; an existing target is renamed to a recoverable sibling before staged install. This is crash-recoverable staged replacement, not an uninterrupted atomic directory exchange.
- A same-name directory in Hermes local `skills/` is a fail-closed shadow collision; do not read or overwrite it.
- Missing any allowlisted source Skill, partial target, invalid manifest, or path escaping the explicit roots fails before apply. Non-allowlisted repository Skills are ignored and must never be copied.
- Rollback restores the manifest-bound prior managed root and does not touch unrelated Skills.
