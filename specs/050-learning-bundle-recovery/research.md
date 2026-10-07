# Decisions
- Decision: inspect five fixed Core-derived directory names. Rationale: protocol already uses .part/.old/.wfderive.part/.wfderive.old. Alternative broad glob/old-title lookup rejected as unnecessary or ambiguous.
- Decision: validate schema/identity/output fingerprints per safe location; original unsuffixed stem remains receipt identity. Rationale: sibling name does not redefine episode. Alternative source freshness orchestration rejected; Tool28/29 already separately own freshness scope.
- Decision: first classify all ancestors/leaf/children; then read only two owned receipt names and known output files. Use existing secure directory listing max256 and capped snapshots. Alternative following links/unbounded scandir rejected.
- Decision: no winner or cleanup guidance. Rationale: role presence/hash match cannot prove which publication/cleanup/report transaction completed. Alternative timestamp ranking/recovery executor out of approved scope.
- Decision: fixed location/role labels and extra count; no unknown names/paths/hash/body text in results. Rationale: metadata diagnosis is sufficient and portable.
- Decision: absent canonical identity ->closed blocker, not guessed storage stem. Clear means no anomalies/remnants observed, not workflow readiness. Invalid/orphan or partial public state requires manual review.
All unknowns resolved with repository-local evidence. No new technology or external research needed.

Review refinement: secure listing previously applied its acceptance cap after eager listdir. Preserve public API and handle/containment proofs, iterate via scandir/islice up to max_entries+1, then refuse overflow. This is necessary to meet FR003/007, not a shared boundary refactor. All generators/Skills remain unchanged.
