# Contract: Hermes Configuration Merge

Managed keys only:

```text
mcp_servers.podcast-ingest-core
<verified Hermes external Skills directory key>
```

Operations:

```text
plan(config_path, desired_entry, skills_dir) -> safe result; zero writes
apply(...) -> changed | no_op; backup before atomic replacement
rollback(manifest_path) -> rolled_back | failed
```

- Preserve all existing and unknown YAML keys/entries.
- No-op creates no backup and changes no mtime.
- Apply creates a timestamped bundle, writes a sibling temporary file, re-parses it, preserves permissions, then atomically replaces.
- Rollback accepts only a valid manifest-bound backup for the same target.
- Output may contain status, managed key names, paths, and SHA-256 digests only.
- Output must not contain full YAML, URL, provider values, credentials, headers, tokens, or exception text that embeds values.
