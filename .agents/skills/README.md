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

These are contracts, not prose. `tests/test_hermes_skill_protocol.py` runs the
first four through `validate_skill_artifacts`, which fails the build when a
`SKILL.md` loses its portable frontmatter, drops a required clause, reorders
the approval clauses, or mentions **any** registry tool name other than the one
that Skill is bound to. Editing a `SKILL.md` for style will break it.

The four-vs-five split is deliberate and easy to get wrong:

- `MANAGED_SKILLS` (`src/podcast_ingest_core/hermes_integration.py`) is the
  exact four above that satisfy the Spec 027 single-tool contract.
- `SYNCED_SKILLS` adds `historical-episode-verified-report-path`, which is what
  actually ships to a Hermes install. It is an orchestrator that names four
  tools by design, so it cannot satisfy the single-tool contract and carries
  its own Spec 023 tests instead.

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
