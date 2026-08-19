# Tasks: X Video Corpus Ingestion

**Feature**: 036-x-video-corpus-ingestion  
**TDD**: RED before GREEN.  
**Status**: Implemented and verified. All nine Success Criteria met; both review axes passed.

## Completion Contract

| Claim | Evidence |
| --- | --- |
| C1 Spec package + clarify | package + Session 2026-08-15 |
| C2 Seam accepts a shaped episode end-to-end | trial run 2026-08-15 (already PASS) |
| C3 Acquisition produces audio + seed from a URL | dry-run plan + one confirmed real run |
| C4 Transcription is reused, not reimplemented | no new emission code; RSS output byte-identical |
| C5 Non-RSS profiles parse; RSS profiles unchanged | config tests |
| C6 RSS-only surfaces refuse non-RSS with a source-aware error | feed_reader / downloader tests |
| C7 Registry unchanged at 22; no MCP surface added | registry contract test green **unmodified** |
| C8 Other podcasts untouched | gooaye index mtime + search output unchanged |
| C9 Full verify | pytest / compileall |

## Spec Kit sequence

`constitution -> specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge`

## Phase 1: Spec Kit

- [x] T001 Constitution: no amendment
- [x] T002 Specify package docs (`spec.md`)
- [x] T003 Clarify: reuse-vs-producer, source registration, groups, title provenance, no MCP tool in v1
- [x] T004 Plan + data-model + checklists
- [x] T005 Tasks + analyze table (below)
- [x] T006 Analyze review pass before any implementation — findings below

## Phase 2: Implement

- [x] T007 RED: `group_segments()` port — 30s sentence-boundary soft break, 90s hard cap
- [x] T008 GREEN: `segment_grouping.py` as a pure function; no persistence
- [x] T009 RED: `PodcastProfile.source_type` defaults to `rss`; non-RSS profile parses without
      `rss_url` / `default_episode_prefix`; `language` still required; existing profile unchanged
- [x] T010 GREEN: `models.PodcastProfile` + `config._parse_profile`
- [x] T011 RED: `list_episodes` / `get_episode` / `download_audio` refuse a non-RSS source with a
      source-aware message, not `KeyError`
- [x] T012 GREEN: one shared `config.require_rss_profile` guard; `download_audio` inherits it
      through `get_episode` rather than carrying a second copy of the message
- [x] T013 RED: `transcribe_episode(audio_path=..., title=...)` names the trio by title; omitting
      `title` reproduces today's bytes for an existing RSS episode
- [x] T014 GREEN: optional keyword-only `title` through `_audio_asset_from_path`
- [x] T015 RED: acquisition — identity parsing, seed payload, dry-run plan, unregistered-source
      refusal; yt-dlp and PyAV stubbed at the module boundary, no test touches x.com
- [x] T016 GREEN: `x_video_ingest.py`
- [x] T017 Thin CLI `scripts/run_x_video_ingest.py`, dry-run first
- [x] T018 `config/podcasts.yaml` x-raytar profile; `pyproject.toml` yt-dlp + av
- [x] T019 Docs: `docs/architecture.md`, `docs/verification-matrix.md`, `specs/README.md` status
- [x] T024 `tests/test_contracts.py` — the podcast-registry assertion now names both sources and
      additionally pins gooaye's `source_type == "rss"`, so the RSS profile is proved untouched
      rather than merely still parsing.
- [x] T025 `tests/test_contracts.py` — `title` added to the pinned `transcribe_episode` parameter
      list, keyword-only, placed after `audio_path`.

## Analyze findings (T006, 2026-08-15)

Verified against code, not inferred:

1. **`load_podcast_profile` has nine callers, not two** — `entity_extractor`,
   `episode_intelligence`, `external_data_boundary`, `feed_reader`,
   `industry_mapping`, `semantic_summarizer`, `stock_lens`, `summarizer`,
   `transcriber`. The design still holds, and now for a checked reason: seven of
   them read only `profile.display_name`, `transcriber` reads only
   `profile.language`, and `feed_reader` is the sole reader of `rss_url` and
   `default_episode_prefix`. Making those two optional therefore cannot reach any
   analysis module.
2. **Two pinned contracts break on contact** — the podcast-registry assertion and
   the `transcribe_episode` signature assertion, both in `tests/test_contracts.py`.
   Neither was in the original plan's file list. Now T024 and T025.
3. **`PodcastProfile` is constructed in exactly one place** (`config.py:64`) and
   with keyword arguments, so the additive field is safe from positional breakage.
4. **The `audio_path` branch is already tested** —
   `tests/test_transcriber.py:317 test_transcribe_episode_uses_audio_path_without_downloading`
   asserts it does not download. T013 extends this test rather than inventing one,
   which lowers the FR-005/006 risk from the plan's "high" to moderate.
5. **The `download_audio` guard touches a shipped MCP tool** — callers are
   `corpus_audio_download_runner.py:380`, `mcp_tools_side_effect.py:87` (Tool 3),
   `transcriber.py:46`, and `scripts/download_episode.py`. Refusing a non-RSS
   source is the correct behaviour, but it is a runtime behaviour change on an
   existing tool. No signature and no registry change; state it in the PR.
6. **`corpus_episode_intake.py:58` calls `get_episode`**, so the RSS seed
   bootstrap will also refuse non-RSS sources once the guard lands. Correct — X
   sources write their seed through the new acquisition path — but it must be
   deliberate, not a surprise.

## Phase 3: Converge + verify

- [x] T020 Converge FR-001..018 against code
- [x] T026 Real-URL **dry-run** against `https://x.com/Raytar/status/2071290493581840707`:
      yt-dlp resolved live metadata, the plan listed all five planned writes, nothing was
      downloaded or written, and the only warning was the cache-stale notice — so
      `published_at` resolved cleanly. This found the FR-012 title defect (see Assumptions 10)
      and confirmed `info["id"]` is a media id, not the status id (Assumptions 11).
- [x] T021 One confirmed real run — **done**, resolving the reviewer's blocking finding that
      everything past `_resolve_metadata` was stub-verified only. The trial-artifact collision
      was sidestepped by passing `--title` to match the existing paths rather than deleting the
      earlier evidence, so no second transcript was created for the same `episode_ref`.

      Real download: 259.96 MiB in 35s. Real PyAV extraction: the WAV is mono / 16000 Hz /
      16-bit / **2003.9 s**, matching the video's 2003.925 s. The seed now carries a real
      `published_at: 2026-06-28` and `warning_count: 0`. No `.part` residue anywhere.
      Transcription short-circuited to the existing valid transcript as designed, so
      `_download_video` and `_extract_audio` executed for real without spending 33 minutes of
      whisper. Then: `validate_transcript` → `valid` / 366 segments; `generate_corpus_index` →
      **`audio: available`**, closing the gap the 2026-08-15 trial left open, and
      `transcript: valid`; `rebuild_cache --podcast x-raytar` → 1 indexed, 0 problems;
      `search_transcripts "prompting playbook"` → hit at `[00:00:18 - 00:00:23]`.

      **Superseded caveat — resolved 2026-08-19, see T027 below.** Because transcription
      short-circuited, the transcript left on disk was still the one the scratchpad shaper
      wrote, with provenance fields pointing outside the repo.

- [x] T022 gooaye regression: search returns the identical EP672 hit at `[00:26:37 - 00:26:38]`,
      `data/corpus/gooaye/corpus-index.json` is unchanged at 34215 bytes / 2026-08-13 22:25:47,
      and its profile still resolves as `source_type=rss`.
- [x] T023 Full pytest + compileall — see below.

## Final verification (2026-08-15)

`python -m compileall src scripts` exits 0.

`python -m pytest -q` → **24 failed / 1584 passed / 14 skipped**. The failure count
matches the Spec 035 recorded baseline, and the complete list was captured rather than
the tail: every one sits in the pre-existing blocked chain
(`test_hermes_runtime_capability`, `test_mcp_http_transport`, `test_spec_029_offline`,
`test_spec_030…`, `031`, `032`, `033`, `034`). Passed rose 1552 → 1584, exactly the 32
tests added here. Nothing this feature touches is red.

The suite was run five times across this work — after the first slice, after the
error-handling fixes, after the code reviewer's five fixes, after the architecture
reviewer's fix, and after the dry-run plan fix. All five produced a failure list identical
line for line, which is what
makes "no regression" a measurement rather than an assertion.

**One real regression was introduced and fixed, recorded because it nearly slipped.**
An intermediate run showed 26 failures. `tests/test_cache_rebuild_guard.py` scans core
modules for the literal maintenance-function name and treats any occurrence outside a
reviewed allowlist as an unreviewed auto-rebuild risk (constitution VIII). The stale-cache
warning string in `x_video_ingest.py` contained it. Fixed by adopting the phrasing the
other runners already use — "rebuild cache manually", with a space — rather than adding
this module to the allowlist, because the allowlist is for modules that genuinely need
the symbol. The first fix attempt failed too: the explanatory comment reintroduced the
same literal.

**Two of the failures were confirmed pre-existing, not assumed.**
`test_mcp_http_transport::test_streamable_http_sets_public_settings_and_runs_the_existing_server`
and `test_spec_029_offline::test_offline_clis_reject_invalid_argv_without_echo_and_docs_remain_consistent`
both fail on a clean `HEAD` worktree. (A full-suite baseline in that worktree was
worthless — `data/` is gitignored, so 838 tests errored; only the targeted comparison
is evidence.)

## Analyze (pre-implement)

| FR | Task | Risk |
| --- | --- | --- |
| FR-001..004 | T015, T016 | medium; the only new I/O, and the only network surface |
| FR-005, FR-007 | T013, T014 | **high**; touches the function every RSS episode uses |
| FR-006 | T013, T014 | medium; a wrong default silently renames existing outputs |
| FR-008..010 | T009..T012 | medium; config schema is additive but load-bearing |
| FR-011, FR-012 | T016, T017 | low |
| FR-013 | T007, T008 | low; pure function, no storage |
| FR-014..017 | T015..T017 | medium; dry-run must not download or transcribe |
| FR-018 | T018 | medium; PyAV wheels are the likely install friction |

**CRITICAL constitution issues**: none. No LLM, no secrets, no market data, no
advice surface, no automatic cache rebuild.

**Watch item**: FR-005 and FR-006 are the regression risk in this spec. The gate
is byte-for-byte equality of an existing RSS episode's transcript outputs, not a
green test suite.

## T007/T008 evidence (2026-08-15)

`src/podcast_ingest_core/segment_grouping.py` + `tests/test_segment_grouping.py`,
built in two red→green cycles (soft break, then hard cap) plus two behaviour pins
(empty input; an over-long single segment stays whole, because the first segment
of a group is admitted without a break check).

**Fidelity check against the original, run once outside the suite**: the ported
function was applied to the prototype's real 366 segments and compared with the
prototype's own 25 stored groups. 25 vs 25, and zero differences in boundaries,
segment composition, or text across all of them. This is the evidence that the
rule was ported rather than reinvented; it is not a committed test because it
depends on `../prompt-engineering`, which is outside this repo.

**Record correction (architecture review F5).** This paragraph originally claimed the
module was "intentionally not exported from `__init__.py`". That became false later in
the same session, when it was exported alongside `run_x_video_ingest`
(`__init__.py:124,390`), and the note was never updated. Accurate statement:
`group_segments` **is** a public export; nothing in `src/` or `scripts/` imports it, so
it cannot affect any existing test — but its return shape
`{start, end, text, segments}` is a public commitment with zero consumers today.
Exporting it follows house style; the stale claim was the defect.

Full suite after the slice: **24 failed / 1552 passed / 14 skipped**; the failure
count matches the Spec 035 baseline of 24, all inside the pre-existing Spec
026-034 blocked chain. `python -m compileall src scripts` exits 0.

## Phase 2 deviations, recorded rather than smoothed over

1. **TDD discipline slipped once.** Implementing the dry-run test (T015) I wrote the
   whole of `run_x_video_ingest`, including the confirmed path. The later tests for
   unregistered-source refusal and for the confirmed run therefore passed on first
   write instead of driving code — they are behaviour pins, not red→green cycles.
   The grouping, profile, guard, and title slices were genuine red→green.
2. **`yt-dlp` and `av` are core dependencies, not an optional extra.** The lazy
   `_load_yt_dlp` / `_load_av` guards would also support an extra, and PyAV's native
   wheels are the likeliest install friction. Core placement follows the repo's own
   precedent: `faster-whisper` is core and uses the same guard shape in
   `transcriber._load_whisper_model_class`. Revisit if a wheel gap actually bites.
3. **`title` is ignored, not rejected, on the RSS download branch.** When
   `audio_path` is absent the feed's title is authoritative, so overriding it would
   be wrong; the docstring says so. Raising was considered and dropped as a new
   failure mode nothing currently needs.
4. **No numpy dependency was added.** The prototype's extraction used
   `np.asarray(...)`; the port calls `frame.to_ndarray().astype("int16")` instead,
   which needs no explicit import.

## Review findings and fixes (2026-08-15)

The first `code-reviewer` and `architecture-reviewer` dispatch both terminated early on an
API session limit and produced no findings. A second `code-reviewer` dispatch completed
and its findings are recorded below. **`architecture-reviewer` never ran** — the
structural questions in its brief (dependency direction of `x_video_ingest` → `transcriber`,
whether `source_type` is the right seam for a third source type, the operational boundary
around yt-dlp) remain unreviewed.

Findings 1 and 2 came from self-review before the reviewer completed; both are the same
class — third-party exceptions escaping the module's error contract.

1. **`_acquire_audio` caught only `OSError`.** `yt_dlp.utils.DownloadError` and
   `av.error.FFmpegError` both derive from `Exception`, not `OSError` — verified against
   the installed packages. A download or extraction failure therefore escaped as a raw
   third-party exception, which `scripts/run_x_video_ingest.py` does not handle, and the
   `.part` cleanup hung off the `OSError` branch so a failed extraction left a stale file
   in `data/audio/`. Fixed: re-raise our own errors unchanged, wrap everything else in
   `XVideoIngestFailedError`, and move `.part` cleanup into `finally`.

2. **`_resolve_metadata` had no protection at all**, and it is both the first step and
   the likeliest to fail — a post with no video, a deleted post, or a broken X extractor
   all surface there. It also sits on the dry-run path, so this was the first thing a
   user would hit. Found by actually running the CLI against a bad URL, not by reading:
   `python scripts/run_x_video_ingest.py --url https://x.com/Raytar/status/1` produced a
   yt-dlp traceback. The fix for defect 1 had missed this call site entirely because its
   test only covered `_download_video`. Now returns
   `{"error": "解析來源 metadata 失敗：ERROR: [twitter] 1: No video could be found in this tweet"}`
   with exit 1.

### Independent review, second attempt — findings accepted and fixed

The re-dispatched `code-reviewer` completed. Five findings were acted on; one was
declined with reasons.

3. **`segment_grouping` only recognised ASCII sentence endings** — the most valuable
   finding, and one the author missed entirely. This repo's primary corpus is zh
   (`gooaye`, `language: zh`), whose sentences end with `。？！`. With ASCII-only
   endings a Chinese transcript never soft-breaks and every group runs to the 90s hard
   cap, defeating the purpose of grouping. The function is exported package-wide, not
   scoped to English X videos. Fixed; the prototype fidelity check still reports 25 vs
   25 groups with zero boundary differences, so English behaviour is unchanged.
4. **`_download_video` trusted `prepare_filename`** — with ffmpeg present yt-dlp merges
   `bestvideo*+bestaudio`, and the merged container's extension can differ from the
   predicted name, handing back a path that does not exist and killing the run during
   audio extraction. Now prefers `info["requested_downloads"][0]["filepath"]`.
5. **Recovery re-downloaded the whole video.** There was no `audio_target.exists()`
   short-circuit, so re-running after a transcription failure fetched ~260 MB again even
   though the extracted WAV was already on disk. Now reuses it and says so in warnings.
6. **The seed was written with a bare `write_text`**, unlike `corpus_episode_intake`,
   which stages through `.part` + `replace`. A mid-write failure left truncated JSON at
   the canonical path. Now follows the same convention.
7. **A whitespace-only `--title` produced an empty seed title** (`if explicit:` is true
   for `"   "`). Now falls back to the metadata title.

**Declined**: the reviewer argued `yt-dlp` and `av` belong in an optional extra, since
the lazy-import guards are dead code in a normal install. That is a fair reading, but the
decision recorded above follows this repo's own precedent — `faster-whisper` is a core
dependency and uses the identical guard shape. Recorded as a dissent rather than silently
overridden; the reviewer also marked it follow-up, not blocking.

**Correction to the claim.** "Only acquisition is new" was not literally accurate:
`segment_grouping.group_segments` is a second new public API, sanctioned by FR-013 but
omitted from the summary.

Note on process: findings 5, 6 and 7 were fixed in one batch rather than three separate
red→green cycles. Their tests were written first and confirmed failing together.

Verified as sound, not changed:

- Non-RSS refusal through the shipped MCP surface. `mcp_runtime._tool_call`
  (`mcp_runtime.py:112-120`) catches `PodcastIngestCoreError`, so Tool 3 returns a clean
  envelope carrying `UnsupportedSourceTypeError` rather than a crash.
- `scripts/download_episode.py` still shows a traceback for a non-RSS source, but it did
  so before this change too (`KeyError` from the profile lookup); the message is now
  informative. That script has no error handling by design; not a regression.
- `derive_identity` cannot produce an identifier that escapes the `storage` slug rules:
  the handle pattern is `[A-Za-z0-9_]{1,15}` with `_` mapped to `-` and lowercased behind
  a fixed `x-` prefix, and the status id is `\d+`. A userinfo-style host such as
  `https://evil.com@x.com/...` fails the netloc allowlist.

### Transcript provenance repair (2026-08-19)

- [x] T027 Re-transcribed from the corpus's own audio asset, closing the T021 caveat.

      **A dry-run defect surfaced first, and only because the operator asked to see the
      plan before spending the time.** The plan listed the `.wav` under `planned_writes`
      even though the confirmed path would reuse the existing file — the
      `audio_target.exists()` check sat *after* the dry-run return, so it only affected
      the confirmed branch. A plan that promises a write it will not perform is a false
      plan, which is precisely what FR-014 exists to prevent. The check now runs before
      the return: the `.wav` drops out of `planned_writes` when it already exists, and a
      "reusing existing audio" warning appears in the dry-run itself. Fixed red-green with
      `test_dry_run_plan_reflects_that_existing_audio_will_be_reused`.

      **The repair.** Ran with `--force` on GPU (`medium` / `cuda` / `float16`; cuBLAS and
      cuDNN were already on this shell's PATH). No download occurred — the reuse
      short-circuit worked, and the source read was the corpus WAV, never the prototype's
      `.mp4`. Provenance is now internally consistent:

      | field | before (shaper) | after (pipeline) |
      | --- | --- | --- |
      | `source_audio_path` | prototype `.mp4`, outside the repo | `data/audio/x-raytar/…wav` |
      | `source_audio_size_bytes` | 272589549 (the video) | 64125654 (matches the WAV) |
      | `model` / `device` | `small` / `cpu` | `medium` / `cuda` |
      | `segment_count` | 366 | 593 |

      **The cascade was flagged before starting, not discovered after.** A finer model
      re-segments the audio, so both summaries were describing a superseded transcript,
      timestamp citations included. Both were regenerated: extractive at 593 segments, and
      semantic at 7 chunks / 22 evidence items — up from 4 / 10, because finer segments
      give the summariser more citable material. Cache rebuilt; search re-verified
      (`"prompting playbook"` at `[00:00:21 - 00:00:23]`, tighter than the previous
      `[00:00:18 - 00:00:23]`). `corpus_index` reports audio, transcript, extractive and
      semantic all present.

      **One honest wart, deliberately not chased.** `last_segment_end_seconds` is 2005.12
      against an audio length of 2003.9 — whisper extrapolates the final segment's end
      slightly past the media. `validate_transcript` accepts it, the previous `small` run
      did not exhibit it, and it would affect every source rather than X alone. Out of
      scope here; recorded so the number is not a surprise later.

## Downstream verification (2026-08-16)

One Success Criterion was still unverified when the work was committed: "the semantic
summariser runs on an X episode with no source-specific branching". Splitting it:

- **Deterministic downstream: verified.** `summarize_episode.py --mode extractive` ran on
  the X episode with no source-specific handling, correctly using the profile's
  `display_name` ("@Raytar (X)"), reporting 366 segments / 00:33:23 / 25372 characters,
  and constructing no provider (`provider: null`, `model: null`). `corpus_index` now
  reports `extractive_summary: available` alongside `audio: available` and
  `transcript: valid`.
- **Semantic (LLM) summary: verified.** It ran on the X episode with no source-specific
  branching — `summary_mode: semantic-llm`, 4 chunks, 10 evidence items — and
  `corpus_index` now reports `semantic_summary: available`. This was the last
  unverified Success Criterion; all nine are now met.

  Three attempts were needed, and the failures are worth recording because none was a
  code defect. First: a connect timeout, because the configured provider sits on a
  private network segment the machine could not reach. Second, on VPN: a read timeout at
  120s and again at 600s. Rather than keep raising the timeout, a liveness probe was sent
  with no transcript and no key — the gateway answered in 0.2s (401 on `/v1/models`, 200
  on `/`), proving it healthy and isolating the fault to model routing. Passing an
  explicit model name resolved it; the model configured in the environment was not one
  the gateway routes, and that class of proxy hangs rather than erroring on an unknown
  model.

  **The criterion is met, but the output is not yet the deliverable.** "Runs with no
  source-specific branching" is satisfied precisely because there is no branching — and
  that is also why roughly a third of the generated sections are dead weight here. The
  summariser's template is finance-shaped: an AI-teaching video gets empty
  台股觀點 / 美股觀點 / 總經觀點 / 生活閒聊 / 廣告 sections, one of which strains to
  invent a market connection, and the artifact carries a "not investment advice" notice.
  The substance it does produce is strong — timestamped evidence throughout, and it
  correctly flagged the transcript's model-version names as uncertain rather than
  asserting them. Reshaping the output toward the prototype's `00_*.md`..`07_*.md`
  study-guide sequence is the next spec's work, not this one's.

## Architecture review (2026-08-15)

`architecture-reviewer` ran after the code review and answered all eight structural
questions. **Sound as implemented, with no material finding**: dependency direction
(the repo already has both `transcriber → downloader` and `runner → transcribe_episode`,
so nothing is inverted, and no cycle exists); `require_rss_profile` placement; the reuse
claim (verified — `transcriber._write_transcript_outputs` remains the only transcript-trio
writer in `src/`); and deferring the MCP tool. It also judged the module correctly placed
*outside* the `corpus_*_runner` family for v1, since that family is remediation-plan-driven
and podcast-scoped while this is URL-driven and single-episode.

Two findings were acted on immediately:

8. **The X surface never read the discriminant it introduced** (in-scope contradiction).
   `_registration_problem` checked only that a profile existed. RSS surfaces enforce
   `source_type`; this one did not, so an RSS profile whose id happened to match a derived
   `x-{handle}` would have received X artifacts silently, and a typo'd `source_type` was
   refused by RSS surfaces yet accepted here. Fixed with the mirror check.
9. **A stale record** — see the correction above; `tasks.md` claimed `segment_grouping` was
   unexported while `__init__.py` exported it.

Recorded as follow-ups, deliberately not fixed here:

- **The corpus maintenance flow is still single-source.** `corpus_remediation_plan.py`
  emits a "ready" audio action suggesting `scripts/download_episode.py` for an x-video
  episode missing audio, and the seed's `has_audio_url=True` suppresses the existing
  "feed audio unavailable" blocker. Execution then fails soft with the source refusal.
  `source_type` does not propagate through index → plan → runner. This is the seam the
  next source spec must close, and the first operational confusion an operator will hit.
- **Divergent title provenance can fork one episode's artifacts.**
  `corpus_local_transcription_runner` passes no `title`, so re-transcribing an x-video
  episode writes a trio at `{ref}__{ref}.*` while this flow derives paths from
  `seed.title`; `storage.find_transcript_asset_paths` then resolves the ambiguity by
  `sorted()[0]`. T021 already met this collision and sidestepped it with `--title`. The
  pre-existing title-in-path scheme is the root cause; this change adds the second writer
  that makes it bite.
- **Family-shape gaps for the exposure spec**: `XVideoIngestResult` lacks
  `not_investment_advice` and `run_mode`, and no confirmed-run report is persisted, unlike
  every `Corpus*RunResult`.
- **Identity is permanent.** `x-{handle}` with `_`→`-` is baked into every on-disk path.
  The mapping is injective for valid X handles (handles cannot contain `-`), so no
  collisions — but a handle rename splits one account across two podcast ids forever.
  Inherent to handle-based identity; accepted knowingly.

**On the dependency dissent (F7):** the reviewer would not reopen it, but corrected the
reasoning — the `faster-whisper` precedent is weaker than claimed above, because
faster-whisper serves the repo's central capability while yt-dlp/av serve exactly one
module, and the real cost is install-time (a PyAV wheel gap breaks `pip install` for
users who never touch x-video), which lazy guards cannot mitigate. At version 0.1.0 this
is cheap to undo. Also noted: the `yt-dlp>=2024.1.0` floor is nominal — X extractor health
needs a *current* yt-dlp, so treat it as a keep-fresh dependency; the absent upper bound
is correct.

## Deliberately not created

`research.md` — the research is the 2026-08-15 seam trial, recorded in the spec's
Assumptions with its measured results. `quickstart.md` — the plan's Verification
block already carries the runnable sequence. `contracts/` — v1 adds no MCP tool
and no new artifact family, so there is no interface to pin. Create them if the
scope grows to include exposure.
