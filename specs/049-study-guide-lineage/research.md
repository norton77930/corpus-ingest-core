# Research decisions
- Decision: own study_guide.lineage.json separate from048 derivation receipt. Rationale: independent stages and source scope. Alternatives: rewrite048 receipt/aggregate Tool28 rejected to preserve existing query contracts.
- Decision: exclude00. Rationale: cover-only consumes seed/audio independently and must not bless old03/04/07. Alternative: whole bundle freshness would expand scope and break cover semantics.
- Decision: hash full rawUTF8 summary consumed by runner and rendered ordered messages before provider. Rationale: source mutations during provider must remain observable; Chunk Summaries may be omitted from prompt but consumed source still recorded.
- Decision: hash staged03/04/07 bytes after write_text. Rationale: Windows newline conversion. Alternative: hash pre-write strings produces immediate stale results.
- Decision: validate reserved record before provider and again before staging. Rationale: refuse unknown/foreign overwrite; matching record alone may change. Reuse/cover-only preserve even malformed regular receipt without granting it authority.
- Decision: read-only query in existing Core module uses its private safety/resolver helpers; no cross-module private access. Codec reuses only public pure hash helpers. No new dependencies.
- Decision: finite five states; no custom context because Tool26 has none. Distinct current/stale/untracked/not_generated/blocked. Scope warning disclaims upstream provenance and non-atomic reads.
All planning unknowns resolved with repository-local evidence; no network research needed.
