# Safety Checklist: Multi-Document Study Guide

**Purpose**: Safety and evidence gates for Spec 038
**Created**: 2026-08-19
**Feature**: [spec.md](../spec.md)

## Evidence and fabrication

- [x] CHK001 `01`/`02`/`05`/`06` are not produced or indexed
- [x] CHK002 Generated files do not invent Claude Code / Codex / Copilot / CLAUDE.md / Skill workflow advice unless the source summary already contains that text
- [x] CHK003 Speaker-attributed claims keep timestamps that already appear in the source summary
- [x] CHK004 Source-summary 不確定事項 about reconstructed prompts is not promoted to verbatim quotation

## LLM and secrets

- [x] CHK005 Confirmed generation requires exact `api_cost_ack` before `create_provider`
- [x] CHK006 Dry-run constructs no provider and writes nothing
- [x] CHK007 Captured provider messages contain no transcript segment text and no `## Chunk Summaries` body
- [x] CHK008 `_PROVIDER_FACTORY_TOKEN` remains the only construction path
- [x] CHK009 `summarize_chunk` / `summarize_final` signatures unchanged
- [x] CHK010 CLI stdout is metadata-only (no body, prompt, secret, transcript)

## Isolation

- [x] CHK011 Finance / gooaye profiles are refused
- [x] CHK012 Finance-shaped source documents are refused even if the profile says `learning-notes`
- [x] CHK013 `ARTIFACT_LADDER` is unchanged
- [x] CHK014 MCP registry remains exact 22
- [x] CHK015 No automatic cache rebuild
- [x] CHK016 `prohibited_advice` passes on `03`/`04`/`07`; an advice-shaped fixture still fails
- [x] CHK017 Principle IV is not amended

Completion markers reconciled2026-10-04 under authorized052 documentation cleanup. Historical22-tool and live-confirm statements describe038 closeout,not current registry or a new provider run. See completion-record.md (../completion-record.md from checklists).
