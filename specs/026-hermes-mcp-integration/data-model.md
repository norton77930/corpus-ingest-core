# Data Model: Hermes Integration

## StreamableHttpConfig

| Field | Type | Constraint |
| --- | --- | --- |
| host | string | exactly `127.0.0.1` |
| port | integer | 1–65535; deployment default 8767 |
| path | string | exactly `/mcp` |
| transport | string | derived constant `streamable-http` |

## IntegrationPlan

| Field | Description |
| --- | --- |
| config_path | Explicit Hermes YAML path |
| mcp_name | exactly `podcast-ingest-core` |
| mcp_url | loopback Streamable HTTP URL; never emitted in result output |
| skills_source | repository `.agents/skills` root |
| skills_target | managed Hermes external Skills root |
| local_skills_root | path checked for shadowing only |
| backup_root | persistent integration backup directory |
| action | `plan`, `apply`, or `rollback` |

## IntegrationResult

Safe JSON/console fields only:

- `status`: `planned`, `changed`, `no_op`, `rolled_back`, or `failed`
- `changed_keys`: managed key names only
- `backup_path`: local path or null
- `before_digest` / `after_digest`
- `managed_skill_digests`
- `error_code`: bounded non-sensitive code

Must not include configuration values, URL, headers, credentials, provider data, Skill content, raw YAML, or exception representations that may embed those values.

## SkillManifest

- schema version
- UTC creation timestamp
- aggregate Skills before/after digests
- config/Skills backup relative paths
- config/Skills existed/changed flags
- rollback state

The redacted plan/apply result separately reports exactly four allowlisted per-Skill source digests. The image digest is runtime evidence recorded outside the rollback manifest.

## ProtectedSurfaceSnapshot

Internal-only state per protected surface:

- metadata manifest: entry count plus a SHA-256 digest of relative names and non-content kind/mode/size/mtime metadata;
- content token: a domain-separated, deterministically framed `sha256().digest()` value held only in memory.

The content token treats bytes as opaque input and is never decoded, parsed, emitted, or persisted. Traversal uses POSIX directory/file descriptors with `O_NOFOLLOW`, `dir_fd`, descriptor-based `scandir`, and same-descriptor `fstat`; unsupported platforms such as native Windows fail before protected path access. It rejects `.env`/`.env.*`, symlink/reparse, missing, malformed, and special entries. Public `hermes-direct-smoke-v2` evidence removes protected manifests/tokens entirely and emits only `metadata_unchanged` and `content_unchanged` booleans with `protected_surface_evidence_scope=metadata_and_content_equality`. These are before/after endpoint comparisons, not a claim that no transient mutation occurred between snapshots. The model, both reviewer checks, and the single live v2 result passed, so C6 is PASS-current; invocation count is fixed at 1.
