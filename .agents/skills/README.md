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

These are contracts, not prose. Each Skill's own contract test in the table
above reads its `SKILL.md` and asserts the clauses that make it safe to hand to
an agent: the approval boundary, the no-fallback clause, and the absence of
client-specific or command markers. Editing a `SKILL.md` for style will break
one of them.

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
