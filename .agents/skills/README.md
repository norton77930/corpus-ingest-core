# `.agents/skills`

Portable agent Skills, in the layout the Spec Kit scaffold expects (Phase 7B).
Each Skill is a directory holding a single `SKILL.md` with YAML frontmatter.
Nothing here is imported by `src/`; these files are read by the agent host, and
by the offline contract checkers listed below.

Two families live here, and they have different rules.

## Project workflow Skills

Authored in this repo. Each one wraps a single MCP tool behind an explicit
human-approval protocol — preview first, act only after the operator approves.

| Directory | Wraps | Contract test |
| --- | --- | --- |
| `corpus-episode-completion/` | one-step episode advance | `tests/test_corpus_episode_completion_skill.py` |
| `corpus-latest-episode-processing/` | latest-episode deterministic run | `tests/test_corpus_latest_episode_processing_skill.py` |
| `episode-verified-research-report/` | named-episode verified report | `tests/test_episode_verified_research_report_skill.py` |
| `latest-episode-verified-research-report/` | latest-episode verified report | `tests/test_latest_episode_verified_research_report_skill.py` |
| `historical-episode-verified-report-path/` | historical-episode path | `tests/test_historical_verified_report_path_skill.py` |
| `x-video-ingest/` | one X post video into the corpus | `tests/test_x_video_ingest_skill.py` |
| `youtube-video-ingest/` | one YouTube video into the corpus | `tests/test_youtube_video_ingest_skill.py` |
| `study-guide-bundle/` | one lecture generation/reuse/cover-only operation | `tests/test_study_guide_bundle_skill.py` |
| `workflow-derivation-bundle/` | one workflow derivation generation/reuse operation | `tests/test_workflow_derivation_bundle_skill.py` |

These are contracts, not prose. Each Skill's own contract test in the table
above reads its `SKILL.md` and asserts the clauses that make it safe to hand to
an agent: the approval boundary, the no-fallback clause, and the absence of
client-specific or command markers. Editing a `SKILL.md` for style will break
one of them.

The two video Skills carry one clause the podcast Skills do not need. Their
preview is zero-write but **not** zero-network: `ingest_x_video` and
`ingest_youtube_video` resolve public source metadata before they can plan a
single write. The Skill must say so before it asks for approval, because the
operator is approving a second network step, not the first one.

> **Coverage note.** A second, cross-cutting validator once checked portable
> frontmatter and single-tool binding across the first four Skills. It lived in
> the Hermes integration modules and was archived with them at the
> `archive/hermes-audit-chain` tag. The per-Skill contract tests above are
> unaffected; the frontmatter and single-tool-name checks are not currently
> enforced and are tracked as a follow-up.

Adding a Skill here means adding its contract test too — an unchecked `SKILL.md`
is a human-approval boundary with nothing holding it in place.

## Vendored Spec Kit Skills

`speckit-analyze/`, `speckit-checklist/`, `speckit-clarify/`,
`speckit-constitution/`, `speckit-converge/`, `speckit-implement/`,
`speckit-plan/`, `speckit-specify/`, `speckit-tasks/`, and
`speckit-taskstoissues/` come from upstream `github-spec-kit` (their frontmatter
carries `metadata.author`). They drive the `$speckit-*` workflow documented in
`AGENTS.md` and read the scaffold under `.specify/`.

Treat these as vendored: re-sync them from upstream rather than hand-editing.
`tests/test_spec_kit_bootstrap.py` asserts all ten are present.


## SPEC 045: Learning workflow Skills

Use `study-guide-bundle` for a named episode with an existing learning-notes semantic summary; use `workflow-derivation-bundle` for an existing lecture and the configured default operator-workflow context. These are independent requests: preview, explain, wait for explicit approval, confirm once, report and stop. Neither Skill fills missing sources or starts the other operation automatically. Existing tool registry and Core behavior are unchanged.

Generation requires the user's exact API-cost acknowledgement after preview. Lecture reuse/cover-only and complete derivation-pair reuse pass an empty acknowledgement, even if one exists in conversation history. Every successful confirm writes run reports, including reuse. A preview is not a digest pin; state is recomputed on confirm, and a no-cost plan that becomes generation must stop on refusal without retry.

SPEC 046: Tool 25 refuses pre-existing recovery entries and unsafe local paths before preview/reuse/generation; force never overrides refusal. It preserves all regular non-pair file bytes and maps MCP failures to fixed safe messages. Distinct errors identify rollback failure, published cleanup/report failure and reused report failure. Only this attempt owns its rollback/cleanup; no automatic recovery of old entries or agent retry. Writers must be serialized; publication is not crash-durable, race-proof or one artifact/report transaction.

Validation is offline: static instruction contracts, actual-backend characterization and synthetic conversation oracles. These do not prove live agent compliance. No CLI/terminal/filesystem fallback, automatic cache rebuild, installation or deployment is performed.


## SPEC 053: Unified learning entry Skill

Use `learning-workflow-advance` when asking for the next learning step of one explicit podcast/episode. It binds only Tool32 `advance_learning_workflow`: one zero-write/offline preview, disclose artifact/reuse/lineage/report plans and costs, wait for fresh cycle approval and exact cost text for generation, confirm once, report and stop. Cover sends empty acknowledgement; complete/blocked states never confirm. Returned action/plan_id are approval bindings, not content snapshots or locks. Missing tools, drift, malformed replies and failures stop without fallback, retries or automatic next action/cache rebuild.

Example: request one learning step for a named podcast and episode; review the returned action/files/cost, then approve this cycle. Existing explicitly selected study-guide/derivation Skills remain independent. No full-chain/batch/repair/force operation is added. Portable Skill and response reference must be loaded by the agent host manually when needed; no installation or live client compliance guarantee. Evidence is offline instruction contracts, labelled dialogue oracles, temporary fake-provider backend checks and read-only synthetic pressure/review.


## SPEC054: Source preparation Skill

Use `source-preparation` for one configured YouTube/X URL: preview public metadata
and local effects, obtain fresh approval, submit Tool33 once, report job_id and
stop. A later explicit progress request uses read-only Tool34 once. Missing
profiles/tools, recovery entries, malformed replies, drift and uncertain outcomes
stop without fallback or retry. No downstream learning/Q&A chain, LLM, profile
editing, polling or automatic cache rebuild. Windows stdio new jobs are blocked;
an operator may use already independent loopback HTTP hosting. See
[Skill](source-preparation/SKILL.md). Offline oracles do not prove live compliance.

## SPEC056: Prepared-source QA Skill

Use [source-content-qa](source-content-qa/SKILL.md) for one known prepared RSS/YouTube/X source. Tool35 reads timed evidence without SQLite; pinned pages support complete or explicitly partial learning notes. Literal multilingual search, hostile content and host privacy/billing are explained. No automatic preparation/publication. Synthetic/SDK evidence is separate from actual Hermes mounting.


## SPEC057: Source learning entry

Use [source-learning-entry](source-learning-entry/SKILL.md) for one source learning request: known prepared IDs go to QA; a configured YouTube/X URL previews preparation and can hand off to QA when ready. Missing-source preparation requires fresh approval and one confirm, then stops. Later status-only stops; explicit learning continuation checks the retained source/job before QA. Install/reload the complete entry, source-preparation and source-content-qa folders with references; keep one editable QA notes template. Existing standalone routes and35tools remain unchanged. Conversation context is not durable memory; no polling/retry/publication/settings/service changes. Actual mounted Hermes acceptance remains separate from developer/synthetic checks.
