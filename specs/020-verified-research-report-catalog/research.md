# Research: Verified Research Report Catalog

## Decision 1 — Read the catalog tree, not a database or cache

- **Decision**: Discover bundles directly from `data/research-reports` with bounded level-by-level directory enumeration.
- **Rationale**: The catalog is offline, needs no dependency or rebuild policy, and treats existing published bundles as the local artifact truth.
- **Alternatives**: SQLite index, FTS, vector index, cache — rejected: each adds derived-state staleness, writes, or an unapproved dependency.

## Decision 2 — Metadata-only list and search

- **Decision**: List and search consume only a whitelisted, scalar, manifest-derived safe metadata projection; they do not open `report.json`, `report.md`, transcripts, or source artifacts.
- **Rationale**: The catalog must discover reports without becoming a raw report/transcript reader or secret/path reflector.
- **Alternatives**: Full-text Markdown/JSON search — rejected: violates the body-read boundary and expands disclosure risk.

## Decision 3 — Exact inspect is a self-consistency verifier

- **Decision**: Inspect validates the exact three files, manifest schema/version, directory/manifest/report identity, and manifest-recorded `report.json`/`report.md` SHA-256 and byte sizes.
- **Rationale**: This provides a useful local integrity signal without inspecting upstream artifact lineage or claiming freshness.
- **Alternatives**: Reuse 018 lineage/source-currentness validation — rejected: it reads outside the bundle and would turn a catalog read into a currentness workflow.

## Decision 4 — Path safety precedes parsing

- **Decision**: At every root/podcast/episode/version/file step, reject reparse points (symlinks and Windows junctions), resolve only under the canonical root, and never recurse past the three expected directory levels.
- **Rationale**: The catalog root is untrusted filesystem input; containment and predictable traversal are prerequisites to safe metadata reads.
- **Alternatives**: `rglob` or follow links then filter — rejected: unbounded traversal and out-of-root exposure.

## Decision 5 — Append surfaces only after Core tests are green

- **Decision**: Implementation order is Core list → Core search → Core inspect → thin CLI → appended MCP Tool 17.
- **Rationale**: Constitution Principle II requires thin interfaces over Core; Tool 17 must preserve Tools 1–16 unchanged.
- **Alternatives**: MCP/CLI-specific catalog logic — rejected: duplicate policy and weakens testability.

## Decision 6 — No source-currentness implication

- **Decision**: Every inspect response includes `source_currentness_status=not_evaluated`, including a self-consistent bundle.
- **Rationale**: Report source artifacts may have changed after publication; the catalog does not read or revalidate them.
- **Alternatives**: Infer currentness from timestamps, manifest paths, or digest — rejected: none prove current upstream bytes.
