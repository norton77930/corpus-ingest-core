# Requirements Checklist: SPEC 021 Source Revalidation

**Purpose**: Validate requirement quality before implementation.
**Feature**: [spec.md](../spec.md)

- [x] C0 records separate current MCP/governance documentation evidence and drift closure.
- [x] C1 defines the complete Spec Kit, exact locator, required non-goals, and review sequence.
- [x] C2 requires bundle/currentness separation and untouched downstream readers on bundle failure.
- [x] C3 requires hostile paths never dereferenced and canonical-before-read tests.
- [x] C4 requires shared SPEC 018 lineage and publisher source/digest rules.
- [x] C5 bounds public Core/CLI/MCP disclosure: no raw manifest, body, path, absolute paths, or stock query.
- [x] C6 requires thin interfaces, Tool 18 append-only, and Tools 1–17 unchanged.
- [x] C7 requires read-only/offline/zero-write, no DB/FTS/vector/cache, network, provider, or dependency.
- [x] C8 requires targeted 018–020 publisher/workflow/catalog regression evidence.
- [x] No latest, next, glob, prefix, batch, repair, adoption, migration, regeneration, publish, republish, or investment advice is in scope.

Checklist completion reviews written requirements only; all Completion Contract claims remain `planned` until their selected evidence is green.
