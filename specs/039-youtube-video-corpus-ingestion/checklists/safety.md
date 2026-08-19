# Safety Checklist: YouTube Video Corpus Ingestion

**Purpose**: Safety, secret, and side-effect requirement quality for Spec 039
**Created**: 2026-08-19
**Feature**: [spec.md](../spec.md)

## Dry-run and writes

- [x] CHK001 Is dry-run specified as zero-write (including no `.part` residue) while still allowing metadata network? [Clarity, Spec §Safety, FR-018]
- [x] CHK002 Is confirmed execution required to be explicit (`confirm=true` / CLI flag) before download, extract, transcribe, or write? [Completeness, Spec §Safety]
- [x] CHK003 Is reuse-versus-write required to be truthful when a WAV already exists? [Clarity, Spec §US2 AC2]
- [x] CHK004 Is the source video forbidden under `data/`? [Completeness, FR-003]
- [x] CHK005 Are arbitrary local write paths forbidden (URL in, storage-derived paths only)? [Completeness, Spec §Safety]

## Credentials, secrets, LLM

- [x] CHK006 Is guest-token-only acquisition specified, with refuse (not prompt) when the URL is not public? [Completeness, FR-020]
- [x] CHK007 Are cookies, login, and stored sessions explicitly out of scope / forbidden? [Coverage, Spec §Out of Scope]
- [x] CHK008 Is this path specified as no LLM, no `api_cost_ack`, and no `.env` read? [Completeness, Spec §Safety, Assumption 6]
- [x] CHK009 Is stdout required to be metadata-only (no transcript body, prompt, or secret)? [Clarity, Spec §US2 AC3]
- [x] CHK010 Is Principle IV left unamended? [Consistency, Assumption 6]

## Isolation and advice

- [x] CHK011 Is ingestion required not to modify any other `podcast_id`'s artifacts? [Completeness, FR-021]
- [x] CHK012 Is gooaye index byte-identity specified as a success criterion? [Measurability, Success Criteria]
- [x] CHK013 Is automatic cache rebuild forbidden and a stale-cache warning required? [Completeness, FR-019]
- [x] CHK014 Are live market API and investment advice explicitly out of scope? [Coverage, Spec §Out of Scope]
- [x] CHK015 Is the MCP registry required to stay at exactly 22 tools? [Completeness, FR-023]
- [x] CHK016 Is `corpus_index` forbidden from importing config? [Completeness, FR-011]

## Notes

Evaluated against the written spec/plan, not against code. All items pass. Future MCP exposure must document zero-write ≠ zero-network (Spec §Safety); that is a successor constraint, not a v1 gap.
