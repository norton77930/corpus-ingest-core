# Safety Checklist: Multi-Document Study Guide

**Purpose**: Safety and evidence gates for Spec 038
**Created**: 2026-08-19
**Feature**: [spec.md](../spec.md)

## Evidence and fabrication

- [ ] CHK001 `01`/`02`/`05`/`06` are not produced or indexed
- [ ] CHK002 Generated files do not invent Claude Code / Codex / Copilot / CLAUDE.md / Skill workflow advice unless the source summary already contains that text
- [ ] CHK003 Speaker-attributed claims keep timestamps that already appear in the source summary
- [ ] CHK004 Source-summary 不確定事項 about reconstructed prompts is not promoted to verbatim quotation

## LLM and secrets

- [ ] CHK005 Confirmed generation requires exact `api_cost_ack` before `create_provider`
- [ ] CHK006 Dry-run constructs no provider and writes nothing
- [ ] CHK007 Captured provider messages contain no transcript segment text and no `## Chunk Summaries` body
- [ ] CHK008 `_PROVIDER_FACTORY_TOKEN` remains the only construction path
- [ ] CHK009 `summarize_chunk` / `summarize_final` signatures unchanged
- [ ] CHK010 CLI stdout is metadata-only (no body, prompt, secret, transcript)

## Isolation

- [ ] CHK011 Finance / gooaye profiles are refused
- [ ] CHK012 Finance-shaped source documents are refused even if the profile says `learning-notes`
- [ ] CHK013 `ARTIFACT_LADDER` is unchanged
- [ ] CHK014 MCP registry remains exact 22
- [ ] CHK015 No automatic cache rebuild
- [ ] CHK016 `prohibited_advice` passes on `03`/`04`/`07`; an advice-shaped fixture still fails
- [ ] CHK017 Principle IV is not amended
