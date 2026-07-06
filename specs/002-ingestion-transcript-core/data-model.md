# Ingestion Transcript Core Data Model

**Status: Backfilled / As-built**

## Entities

- Episode metadata: podcast id, episode reference, title, publication metadata,
  audio URL, and local artifact references.
- Audio artifact: local path created by download flows.
- Transcript artifact: local JSON transcript with segment metadata and status.
- Summary artifact: deterministic extractive Markdown derived from transcript segments.

## State Boundaries

- Transcript status gates later research use.
- Missing, corrupt, incomplete, and partial transcript states must be visible to callers.
- Local artifact paths are the source of truth for downstream cache and research layers.

## Safety Notes

This model is deterministic, uses no LLM provider, uses no live market API, and
does not provide investment advice.
