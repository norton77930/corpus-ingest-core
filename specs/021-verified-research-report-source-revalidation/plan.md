# Implementation Plan: Verified Research Report Source Revalidation

**Branch**: `021-verified-research-report-source-revalidation` | **Date**: 2026-07-27 | **Spec**: [spec.md](spec.md)

## Summary

Implement a Core-owned exact-locator source revalidation seam, thin CLI, and append-only Tool 18. This is a read-only/offline/zero-write workflow. It preserves bundle/currentness separation and treats hostile paths never dereferenced.

## Technical Context

- Python 3.12 and existing dependencies only; no DB/FTS/vector/cache.
- Reuse SPEC 020 secure exact-bundle evidence and SPEC 018 lineage validation.
- Extract shared canonical-source snapshots and publisher-owned digest calculation; do not duplicate digest JSON rules.
- CLI: `scripts/revalidate_verified_research_report_sources.py PODCAST_ID EPISODE_REF SOURCE_DIGEST`.
- MCP: Tool 18 `revalidate_verified_research_report_sources`; Tools 1–17 unchanged.

## Design Decisions

1. Validate exact locator, securely snapshot bundle, then run unchanged self-consistency.
2. For missing/invalid bundle, every downstream status is `not_evaluated` and no external artifact is read.
3. Validate supported fixed assembly-options shape without disclosing stock query.
4. Derive canonical safe paths from Core-owned locator/storage/options only; compare hostile published strings exactly, never dereference them.
5. Revalidate current lineage, compare published lineage and source role/hash/size/canonical-path metadata, recompute digest, then recheck snapshot stability.

## Non-goals

No latest, next, glob, prefix, batch, repair, adopt, migrate, regenerate, publish, republish, output, raw metadata/body/path disclosure, RSS/HTTP/LLM/.env/download/transcription/remediation, live market API, or investment advice.

## Constitution Check

Local artifacts remain traceable; Core owns policy while CLI/MCP are thin; no writes, network, LLM, provider, cache rebuild, or new dependency exists. TDD precedes every vertical slice.
