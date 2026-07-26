# Requirements Checklist: Verified Research Report Catalog

**Purpose**: Validate SPEC 020 requirement quality before implementation.
**Created**: 2026-07-26
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] User stories are independently testable vertical slices for list, search, and inspect.
- [x] No `[NEEDS CLARIFICATION]` or template residue remains.
- [x] Scope is explicitly read-only/offline and matches the implemented Core, CLI, and MCP boundaries.

## Requirement Completeness

- [x] Core seams, thin CLI subcommands, and appended MCP Tool 17 are named.
- [x] Exact optional filters, deterministic sort, default/max limits, missing-root behavior, and traversal caps are testable.
- [x] Search's manifest-derived safe metadata boundary and no body-read rule are explicit.
- [x] Inspect requires canonical identity, exactly three files, schema, hash/size, and report-identity validation.
- [x] Successful inspect is constrained to bundle self-consistency with `source_currentness_status=not_evaluated`.
- [x] Symlink, junction, out-of-root, canonical `v1-[a-f0-9]{64}`, raw manifest, and absolute paths are covered.
- [x] No export/copy/zip/output path/re-publish, DB/FTS/vector/cache, RSS/HTTP/LLM/.env/download/transcription/remediation, or latest selector is allowed.
- [x] No dependency addition and 015–019 / Tools 1–16 compatibility are required.

## Notes

- Checklist completion means the written requirements were reviewed; it does not claim runtime implementation or test execution.
