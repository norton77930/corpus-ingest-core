# Research: Verified Research Report Coverage Index

## Decisions

1. **Episode inventory source** — Public `corpus_index.discover_local_episode_refs` (zero-write; no `generate_corpus_index`), matching 008 discovery families.
2. **Bundle source** — Public `verified_research_report_catalog.discover_eligible_report_summaries` / `require_safe_podcast_id` so eligibility, path safety, and identifier rules stay single-sourced; coverage does not import package-private helpers.

3. **Union vs left-only** — Include orphan bundle episodes (`inventory_present=false`) so operators see catalog entries not mirrored by local artifacts.
4. **Filter semantics** — `has_bundle` filters rows after join; page totals still report full complete-join statistics.
5. **MCP** — New Tool 19 read-query only; no `confirm` / ack.

## Alternatives rejected

- Extending Tool 17 with a `coverage` action: would widen Tool 17 contract and mix bundle-centric vs episode-centric APIs.
- Persisting a coverage JSON under `data/corpus/`: out of scope; v1 is query-only.
- Calling 021 for every row: side-effect-free but expensive and out of v1; coverage is presence, not currentness.

## Constitution

Reviewed; no amendment required for this read-only offline join.
