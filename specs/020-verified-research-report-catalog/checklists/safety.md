# Safety Checklist: SPEC 020 Catalog

**Purpose**: Review data-boundary and containment requirements before implementation.
**Created**: 2026-07-26
**Feature**: [spec.md](../spec.md)

- [x] Read-only/offline includes zero writes on missing root and every rejected candidate.
- [x] List/search never read report, transcript, or source-artifact bodies; inspect reads only the exact three files necessary for integrity checks.
- [x] Search has a strict whitelisted safe metadata projection, not arbitrary manifest search.
- [x] Public output forbids raw manifest, report/transcript body, source paths, absolute paths, unsafe URI data, secret-like values, and traceback bodies.
- [x] Traversal is level-by-level and bounded; canonical `v1-[a-f0-9]{64}` is mandatory; symlink, junction, special file, and out-of-root targets fail closed.
- [x] Inspect requires exactly `report.json`, `report.md`, and `manifest.json`, then validates schema, identity, hashes, and sizes.
- [x] Self-consistency is not currentness: every inspection sets `source_currentness_status=not_evaluated`.
- [x] The contract excludes export/copy/zip/output path/re-publish and no DB/FTS/vector/cache.
- [x] The contract excludes RSS/HTTP/LLM/.env/download/transcription/remediation and no latest selector.
- [x] No investment advice, live market API, automatic cache rebuild, or new dependency is introduced.

## Notes

- Checklist completion reviews specification safety only; no implementation behavior is claimed.
