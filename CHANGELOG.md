# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-08-29

The release that makes this repository usable by someone who did not write it.
Everything below serves one of two goals: a stranger can install and run it, or
a contributor can change it without stepping on a mine.

### ⚠ BREAKING CHANGES

- **The package is renamed** from `podcast_ingest_core` to `corpus_ingest_core`,
  and the distribution from `podcast-ingest-core` to `corpus-ingest-core`.
  `podcast` was accurate when RSS was the only source; X and YouTube ingest
  landed in specs 036 and 039, and keeping the old name meant renaming again at
  the next source type.
- **The MCP server is renamed** from `podcast-ingest-core` to
  `corpus-ingest-core`. **Update your client config** — Claude Desktop, Claude
  Code and Codex each need the one-line change. See
  [`examples/mcp/`](examples/mcp/) for the current shape of each.
- **Four environment variables are renamed.** The old spellings still work and
  will be removed in 0.3.0; the new name wins when both are set.

  | Was | Now |
  | --- | --- |
  | `PODCAST_INGEST_CONFIG` | `CORPUS_INGEST_CONFIG` |
  | `PODCAST_INGEST_DATA_DIR` | `CORPUS_INGEST_DATA_DIR` |
  | `PODCAST_INGEST_MCP_PORT` | `CORPUS_INGEST_MCP_PORT` |
  | `PODCAST_INGEST_STOCK_LENS_SYNTHESIS_DEBUG_OUTPUT_PATH` | `CORPUS_INGEST_STOCK_LENS_SYNTHESIS_DEBUG_OUTPUT_PATH` |

- **The Hermes sidecar integration is removed** from `main`. Specs 026–034, the
  18 `hermes_*` modules, their tests and scripts, and `deploy/` are archived at
  the tag `archive/hermes-audit-chain` and restorable from it.

### Added

- Two console scripts, so an agent can reach the MCP server without cloning:
  `corpus-ingest-mcp` (stdio) and `corpus-ingest-mcp-http` (loopback HTTP).
- [`examples/`](examples/) — client configs for Claude Desktop, Claude Code and
  Codex; prompts to try with what each should do; and a **synthetic** two-episode
  sample corpus, indexed and ready, so the search and evidence tools return real
  results before you have transcribed anything. Regenerate it with
  `python examples/generate_sample_corpus.py`.
- `ruff`, `mypy` and coverage gates, all three enforced in CI.
- `ubuntu-latest` in the CI matrix. The code was always written to be portable;
  none of that was ever exercised.
- Packaging metadata that was missing entirely: SPDX license expression,
  classifiers, project URLs, and `LICENSE` shipped inside the wheel.
- `CODE_OF_CONDUCT.md`, issue and pull-request templates, `dependabot.yml`,
  `CODEOWNERS`, and this file.

### Fixed

- README's Quickstart told you to clone
  `https://github.com/<your-account>/corpus-ingest-core.git`. The first command a
  visitor ran did not work.
- Tool-count drift. `docs/architecture.md` claimed 21 tools on one line and 25
  on another; `docs/install-and-porting.md` claimed 22 in two places. The live
  registry has 25, and `test_docs_registry_count_consistency.py` now recognises
  the two phrasings that had escaped it for three releases.
- A `fresh_review` flag in the latest-episode workflow runner was assigned in two
  branches and read nowhere.
- Three `pytest.raises(Exception)` blocks narrowed to the type each actually
  raises; two `zip()` calls given `strict=True`.
- `test_artifact_lock`'s spawned-worker budget was 10 seconds, which is not
  enough for a fresh interpreter to import a 39k-line package under coverage on
  a contended runner. The correctness assertion is unchanged.
- `.gitignore` did not cover `.coverage`, `.coverage.*`, `htmlcov/`,
  `.mypy_cache/` or `.ruff_cache/`.

### Changed

- Line endings are normalised repo-wide (`* text=auto`). `.gitattributes` went
  from roughly sixty `-text` pins to one rule: the audit chain that needed those
  pins is archived, and Windows and Linux runners now see identical bytes.
- `pyproject.toml` has no `--ignore` list. Every test in `tests/` runs on a bare
  `python -m pytest`.
- The display title is "Corpus Ingestion Core" wherever it faces a user.

### Known limitations

- The mypy baseline exempts 30 of 84 modules (87 errors). The other 54 are gated
  from this release forward. Shrink the list by deleting a line and fixing what
  mypy reports.
- Branch coverage is off. Several tests spawn subprocesses from a temporary
  working directory; those children never find `pyproject.toml`, measure in
  statement mode, and combining the two data sets fails outright.
- `ruff format` has not been run. It would touch every file in the repository
  and belongs in a commit of its own.
- The cross-cutting `SKILL.md` validator — portable frontmatter and single-tool
  binding — lived in the removed Hermes modules. Each Skill's own contract test
  still runs; those two checks do not.

## 0.1.0 - 2026-08-21

First public release, at commit
[`8110d84`](https://github.com/norton77930/corpus-ingest-core/commit/8110d841d871f3d39927f9339addc2c0434d0579).
It was never tagged, which is why this entry carries no comparison link and why
0.2.0 is the first release anyone can pin. Documented here retroactively.

RSS episode listing and lookup, audio download, local faster-whisper
transcription, transcript validation, deterministic extractive summaries, opt-in
LLM semantic summaries behind a review gate, deterministic mention extraction
with timestamp evidence, a SQLite metadata cache with FTS5 search, X and YouTube
video ingest, deterministic research artifacts, verified research report bundles
with content-digest versioning, and a 25-tool MCP server over stdio and
loopback HTTP.

[Unreleased]: https://github.com/norton77930/corpus-ingest-core/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/norton77930/corpus-ingest-core/compare/8110d841d871f3d39927f9339addc2c0434d0579...v0.2.0
