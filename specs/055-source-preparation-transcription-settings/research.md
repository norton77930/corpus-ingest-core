# Research decisions

Date: 2026-10-07. Repository-only research; one read-only research role, no writes/test/media processes or .env access by that role.

- Decision: source-profile setting rather than per-call AI overrides. Rationale: approved URL dialogue uses stable operator policy. Alternative: new MCP arguments, rejected as an expanded agent consent surface.
- Decision: complete strict mapping, finite standard names. Rationale: explicit null/typos/paths must not default silently. Alternative: partial defaults/automatic hardware/model choice, rejected as ambiguous.
- Decision: settings in both context and persisted plan. Evidence: context_digest currently omits them and jobs._PLAN_KEYS would discard unlisted fields. Worker uses the persisted tuple rather than rereading a replacement policy.
- Decision: JSON payload2 with strict payload1 support and unchanged DB schema. Evidence: _decode has exact version/key checks. Alternative: migration/rewrite, rejected to preserve history and zero-write inspection.
- Decision: retain the selected validated existing JSON snapshot. Evidence: _artifacts accepts a recorded title different from current remote title; reused TranscriptAsset exposes requested rather than historical settings.
- Decision: CUDA capability-only preflight. Rationale: preview cannot initialize/download models. Runtime/library/VRAM failure remains possible later and must preserve uncertainty without fallback.
- Decision: current versus recorded/unknown settings, no regeneration. Rationale: changed policy must not overwrite complete artifacts. Explicit replacement stays separate.
- Decision: evolve Tool33/34 response fields and Skill while keeping signatures/count/order. Alternative: a redundant preparation tool, rejected.

Constitution unchanged. Prior conversation resolves operator-owned configuration, omitted historical defaults and no fallback; no further clarification needed. Q&A remains an unnumbered future proposal; package055 is unused and assigned to this approved feature.
