# API reference

Complete reference for the `podcast_ingest_core` public surface: core
functions, the artifact paths they write, the CLI scripts that wrap them, and
the MCP tool registry.

For a short introduction and a first run, start at the
[README](../README.md). For project status, spec history, and open blockers,
see [`agent-handoff.md`](agent-handoff.md).

Nothing in this repository, and nothing any of these functions produce, is
investment advice.

## Conventions

- **`podcast_id`** is a lowercase slug defined in `config/podcasts.yaml`. The
  core never hard-codes a specific podcast.
- **`episode_ref`** is derived from the RSS title and the profile's
  `default_episode_prefix`, for example `EP672`. Some entry points also accept
  the `latest` selector; those that do not say so explicitly.
- **Dry-run first.** Every function with side effects defaults to
  `confirm=False` and returns a plan instead of acting. Call again with
  `confirm=True` only after reviewing that plan.
- **`api_cost_ack`.** Entry points that can send transcript text to an external
  LLM additionally require an exact acknowledgement string. It is validated
  before profile, `.env`, credential, or provider work happens:

  ```text
  I understand this may call an external LLM API, send transcript text outside this machine, and incur costs.
  ```

- **No automatic cache rebuild.** Side-effect entry points never rebuild the
  SQLite cache; they warn that it may be stale. Call `rebuild_cache` yourself.
- **Filenames** strip characters that are invalid on Windows, plus control
  characters, emoji, and high-risk symbols.

## Core function reference

All names below are importable from `podcast_ingest_core`.

```python
list_episodes(podcast_id, limit)
get_episode(podcast_id, episode_ref)
download_audio(podcast_id, episode_ref)
transcribe_episode(
    podcast_id,
    episode_ref,
    model=None,
    device="cpu",
    compute_type="int8",
    vad_filter=False,
    force=False,
    audio_path=None,
    progress_callback=None,
)
validate_transcript(podcast_id, episode_ref)
summarize_episode(
    podcast_id,
    episode_ref,
    force=False,
    max_quotes=10,
    window_seconds=300,
    allow_partial=False,
)
semantic_summarize_episode(
    podcast_id,
    episode_ref,
    provider="openai-compatible",
    model=None,
    base_url=None,
    api_key_env="OPENAI_API_KEY",
    force=False,
    chunk_seconds=600,
    max_segments_per_chunk=120,
    allow_partial=False,
)
extract_mentions(
    podcast_id,
    episode_ref,
    force=False,
    allow_partial=False,
    max_evidence_per_mention=5,
)
generate_episode_intelligence_report(
    podcast_id,
    episode_ref,
    force=False,
    allow_partial=False,
    window_seconds=300,
    max_evidence_per_section=5,
)
generate_industry_chain_mapping(
    podcast_id,
    episode_ref,
    force=False,
    allow_partial=False,
    max_candidates_per_node=5,
    max_evidence_per_candidate=5,
)
generate_external_data_boundary(
    podcast_id,
    episode_ref,
    force=False,
    allow_partial=False,
)
verify_external_data_boundary(
    podcast_id,
    episode_ref,
    confirm=False,
    force=False,
    allow_partial=False,
    provider="fixture",
    fixture_path=DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH,
)
load_gooaye_lens_model(path=DEFAULT_GOOAYE_LENS_CONFIG_PATH)
generate_stock_lens_report(
    podcast_id,
    stock_query,
    force=False,
    allow_partial=False,
    max_evidence_items=10,
)
generate_stock_lens_synthesis_report(
    podcast_id,
    stock_query,
    confirm=False,
    force=False,
    allow_partial=False,
    api_cost_ack="",
    provider="openai-compatible",
    model=None,
    base_url=None,
    api_key_env="OPENAI_API_KEY",
    max_prompt_chars=24000,
)
run_research_workflow(
    podcast_id,
    episode_ref,
    stock_query=None,
    confirm=False,
    force=False,
    allow_partial=False,
    include_semantic_summary=False,
    include_stock_lens_synthesis=False,
    include_external_data_verification=False,
    api_cost_ack="",
    semantic_provider="openai-compatible",
    semantic_model=None,
    semantic_base_url=None,
    semantic_api_key_env="OPENAI_API_KEY",
    semantic_chunk_seconds=600,
    semantic_max_segments_per_chunk=120,
    synthesis_provider="openai-compatible",
    synthesis_model=None,
    synthesis_base_url=None,
    synthesis_api_key_env="OPENAI_API_KEY",
    synthesis_max_prompt_chars=24000,
    external_data_provider="fixture",
    external_fixture_path=DEFAULT_EXTERNAL_MARKET_DATA_FIXTURE_PATH,
    max_evidence_per_mention=5,
    report_window_seconds=300,
    max_evidence_per_section=5,
    max_candidates_per_node=5,
    max_evidence_per_candidate=5,
    max_stock_evidence_items=10,
)
initialize_cache(db_path=None)
index_episode(podcast_id, episode_ref, force=False, db_path=None)
rebuild_cache(podcast_id=None, force=False, db_path=None)
search_transcripts(query, podcast_id=None, limit=20, db_path=None, search_mode="auto", context_segments=0, case_sensitive=False)
search_mentions(query, podcast_id=None, mention_type=None, limit=20, db_path=None, case_sensitive=False)
run_corpus_episode_intake(podcast_id, episode_ref="latest", confirm=False)
generate_corpus_index(podcast_id)
generate_corpus_remediation_plan(podcast_id)
run_corpus_audio_download(podcast_id, episode_ref=None, confirm=False)
run_corpus_remediation(
    podcast_id,
    confirm=False,
    episode_ref=None,
    action_family=None,
    max_actions=None,
    force=False,
    allow_partial=False,
)
run_corpus_local_transcription(
    podcast_id,
    episode_ref=None,
    confirm=False,
    model=None,
    device="cpu",
    compute_type="int8",
    vad_filter=False,
)
run_corpus_episode_workflow(
    podcast_id,
    episode_ref="latest",
    stage="next",
    confirm=False,
    model=None,
    device="cpu",
    compute_type="int8",
    vad_filter=False,
    force=False,
    allow_partial=False,
    max_actions=None,
)
run_corpus_semantic_remediation(
    podcast_id,
    episode_ref,
    action="next",
    confirm=False,
    api_cost_ack="",
    provider="openai-compatible",
    model=None,
    base_url=None,
    api_key_env="OPENAI_API_KEY",
    chunk_seconds=600,
    max_segments_per_chunk=120,
    progress_callback=None,
)
run_corpus_episode_completion_workflow(
    podcast_id,
    episode_ref="latest",
    action="next",
    confirm=False,
    api_cost_ack="",
    transcription_model=None,
    transcription_device="cpu",
    transcription_compute_type="int8",
    transcription_vad_filter=False,
    semantic_provider="openai-compatible",
    semantic_model=None,
    semantic_base_url=None,
    semantic_api_key_env="OPENAI_API_KEY",
    semantic_chunk_seconds=600,
    semantic_max_segments_per_chunk=120,
    progress_callback=None,
)
run_corpus_latest_episode_deterministic_workflow(
    podcast_id,
    confirm=False,
    transcription_model=None,
    transcription_device="cpu",
    transcription_compute_type="int8",
    transcription_vad_filter=False,
)
run_latest_episode_verified_research_report_workflow(
    podcast_id,
    confirm=False,
    expected_episode_ref=None,
    api_cost_ack="",
    stock_query=None,
    include_fixture_verification=False,
)
run_episode_verified_research_report_workflow(
    podcast_id,
    episode_ref,
    confirm=False,
    stock_query=None,
    include_fixture_verification=False,
)
```

## Behaviour contracts

### Ingestion and transcription

- **`list_episodes` / `get_episode`** read the configured RSS feed and return
  episode metadata. `get_episode` accepts the `latest` selector.
- **`download_audio`** fetches the enclosure for one episode into
  `data/audio/`. It does not transcribe.
- **`transcribe_episode`** runs faster-whisper locally and writes `.txt`,
  `.srt`, and a `.json` metadata sidecar. Pass an explicit `audio_path` to
  transcribe a file that did not come from the feed. `tiny` and `base` are good
  for validating the pipeline; `small` and `medium` improve quality. On an
  NVIDIA GPU, try `device="cuda", compute_type="float16"`.
- **`validate_transcript`** classifies a transcript as complete, empty,
  partial, missing, or corrupt. Downstream generators refuse partial
  transcripts unless `allow_partial=True`.

### Summaries: two deliberately separate paths

- **`summarize_episode`** is deterministic and extractive. It selects
  representative segments from the existing transcript using a template. It
  calls no external API, needs no credentials, and performs no semantic
  inference. Same transcript in, same summary out.
- **`semantic_summarize_episode`** calls an OpenAI-compatible API to produce a
  semantic summary. It chunks the transcript (default 600 seconds, 120 segments
  per chunk), sends transcript text outside this machine, and requires the
  exact api_cost_ack. Important claims should carry timestamp evidence. Its
  output is an LLM intermediate artifact, not podcast raw evidence, and it is
  not investment advice.

The two paths write to different files and are never substituted for each
other. Anything the deterministic path produces can be re-derived offline from
the transcript; anything the LLM path produces cannot.

### Research artifacts, deterministic

- **`extract_mentions`** scans transcript segments with deterministic rules for
  companies, tickers, industries, macro topics, crypto, and places. Every
  mention keeps timestamp evidence. It is not semantic understanding.
- **`generate_episode_intelligence_report`** builds a single-episode report
  from the existing transcript and mentions artifacts. No LLM, no external
  market data, no stock mapping, no investment advice. If the mentions artifact
  is missing the report is still produced, with a source warning and empty
  mention-derived sections.
- **`generate_industry_chain_mapping`** derives industry-chain nodes and stock
  candidates from the episode intelligence report and
  `config/industry_chain_mappings.yaml`. It separates `podcast_explicit`
  evidence from `inferred_from_industry` research leads, which default to
  `needs_verification`.
- **`generate_external_data_boundary`** produces a verification scaffold from
  the industry mapping. It calls no provider, reads no API key, and asserts no
  prices, valuations, financials, or news. Every candidate is marked
  `external_verification_status=not_requested`, `source_status=not_fetched`,
  `data_date=null`.
- **`verify_external_data_boundary`** is a fixture-backed scaffold: dry-run
  first, and a confirm guard means `confirm=True` updates an existing boundary
  from a local fixture provider only. No live market API, no API key.
- **`load_gooaye_lens_model`** loads and validates the local analysis framework
  in `config/gooaye_lens.yaml`: industry-chain position, supply/demand and
  inventory, cycle, rate and valuation sensitivity, capex and capacity,
  geopolitics and uncertainty. It accepts no stock input and writes nothing.
- **`generate_stock_lens_report`** applies that framework to a podcast's local
  mapping and boundary artifacts for one stock query. Direct podcast evidence
  and needs-verification research leads stay labelled separately; with no
  direct evidence the report is still produced and marked
  `no-direct-podcast-evidence`. No LLM, no external market data, no buy/sell
  recommendation, no target price, no guaranteed return.

### Research artifacts, LLM and opt-in

- **`generate_stock_lens_synthesis_report`** is dry-run first. Confirmed
  execution requires the exact api_cost_ack. The default LLM input boundary is
  `phase-6f-stock-lens-json-only`, that is, 6F stock lens JSON only. Reviewed
  semantic context can be opted into explicitly, which changes the boundary to
  `phase-6f-stock-lens-json-plus-reviewed-semantic-summary`; even then there is
  no raw transcript input and no external market data lookup. Output containing
  buy/sell/hold language, target prices, or guaranteed returns is rejected
  rather than written.
- **`run_research_workflow`** is the dry-run first local runner that chains
  mentions, episode intelligence, industry mapping, external boundary, and
  optionally the stock lens. Optional semantic summary execution inside
  research workflow, workflow opt-in synthesis via
  `include_stock_lens_synthesis`, and optional workflow fixture verification
  via `include_external_data_verification` are each opt-in. Only the LLM steps
  require the exact ack. No live market API, no API key for the fixture path,
  no automatic cache rebuild, no MCP tool changes, and no investment advice.

### Corpus workflows

These are the batch and lifecycle entry points. All are dry-run first; the
dry-run of the workflow runners is strict zero-file, meaning it creates,
modifies, or deletes zero files.

- **`generate_corpus_index`** scans local per-episode artifacts and semantic
  review metadata and writes a deterministic status JSON and Markdown. It reads
  no RSS, no SQLite cache, no `.env`, and emits no raw transcript, evidence, or
  semantic body.
- **`generate_corpus_remediation_plan`** refreshes the index, then derives
  full-ladder gaps, blockers, warnings, and manual-only actions. It executes
  nothing.
- **`run_corpus_episode_intake`** bootstraps an episode from RSS. Confirmed
  execution writes only safe seed metadata and an intake report.
- **`run_corpus_audio_download`**, **`run_corpus_local_transcription`**, and
  **`run_corpus_remediation`** each refresh the plan, then, on confirmation and
  for a single explicitly named episode or action family, call the existing
  core function and write a latest run report. Reports carry no source URL,
  query string, secret, or traceback.
- **`run_corpus_episode_workflow`** picks the next safe stage among intake,
  audio download, local transcription, and deterministic remediation.
  Confirmed execution runs exactly one stage and stops.
- **`run_corpus_semantic_remediation`** is the standalone single-episode
  semantic runner. It does not accept `latest` and does not call the other
  corpus runners. Confirmed `semantic_summary` validates the exact api_cost_ack
  before profile, `.env`, credential, and provider construction; confirmed
  `semantic_review` is deterministic and reads no LLM configuration at all. It
  writes `corpus-semantic-remediation-run.json` and `.md` on confirmed runs
  only, with no generated_at field, and does not rebuild the index, the plan,
  or the SQLite cache.
- **`run_corpus_episode_completion_workflow`** previews the next action from
  intake through semantic review with strict zero-file behaviour, then executes
  exactly one human-approved action against the canonical episode and stops.
  `next` and `latest` are rejected at confirmation time. It writes
  `corpus-episode-completion-workflow-run.json` and `.md`.
- **`run_corpus_latest_episode_deterministic_workflow`** resolves `latest`
  once, locks that canonical episode, runs intake, audio download, local
  transcription, and any needed deterministic remediation, fails closed on a
  failed or blocked stage, and stops at `ready_for_semantic_summary` without
  touching `.env`, a provider, semantic summary or review, retries, or the
  cache. SPEC 017 is Implemented.

### Verified research reports

- **`run_latest_episode_verified_research_report_workflow`** previews with
  strict zero-write and returns one canonical episode reference plus the exact
  required acknowledgement. Confirmation must supply that same
  `expected_episode_ref` and an exactly equal api_cost_ack, before RSS,
  environment or provider, writer, or child stage work. It reuses the pinned
  deterministic ladder, gates on an exact `passed` semantic review, and
  atomically publishes a digest-versioned bundle. Identical content is reused;
  conflicts fail closed.
- **`run_episode_verified_research_report_workflow`** does the same for an
  explicitly named episode, including historical ones. It rejects the latest
  and next selectors, needs no api_cost_ack, and calls no LLM, RSS, or
  download: it only assembles and publishes once lineage and review already
  pass. Missing inputs return `blocked` with the missing or stale roles listed.
- **`list_verified_research_reports`**, **`search_verified_research_reports`**,
  and **`inspect_verified_research_report`** are offline, read-only,
  manifest-first catalog seams over `data/research-reports`. `list` filters on
  exact values, `search` covers safe metadata only, and `inspect` checks one
  exact bundle's local self-consistency. `inspect` always returns
  `source_currentness_status=not_evaluated`.

  Boundary shorthand: no body search; no raw manifest; no absolute paths; no export; no DB/FTS/vector/cache; no RSS/HTTP/LLM/.env/download/transcription/remediation; no latest selector; no source latest or currentness claim.
- **`list_verified_research_report_coverage`** joins local inventory against
  published bundles per episode, optionally filtered to episodes with or
  without a bundle. Offline, zero-write, no report body, no revalidation, and
  no currentness claim.
- **`revalidate_verified_research_report_sources`**,
  **`suggest_historical_verified_report_next_step`**, and
  **`list_verified_report_gap_backlog`** are the remaining offline read
  queries: exact-locator source revalidation, historical next-step suggestion,
  and inventory gap backlog.

### Cache and search

- **`initialize_cache`**, **`index_episode`**, and **`rebuild_cache`** manage
  the SQLite metadata cache. `rebuild_cache` only indexes artifacts that
  already exist; it never downloads, transcribes, summarizes, extracts
  mentions, or generates any report, mapping, boundary, or stock lens.
- **`search_transcripts`** uses SQLite FTS5 when available and falls back to
  LIKE when FTS5 is missing or the query is a CJK exact substring. Results
  include `highlighted_text`, the `search_mode` actually used, and optional
  surrounding segments via `context_segments`.
- **`search_mentions`** queries indexed mentions, optionally filtered by
  `mention_type`.

The cache is derived data. It can be deleted and rebuilt; the source of truth
stays in `data/transcripts/`, `data/summaries/`, and `data/mentions/`. There is
no embedding and no vector search.

## Output paths

Every artifact lives under `data/`, with deterministic naming so tools can find
files without a database.

| Artifact | Path |
| --- | --- |
| Audio | `data/audio/{podcast_id}/{episode_ref}__{safe_title_slug}.{ext}` |
| Transcript | `data/transcripts/{podcast_id}/{episode_ref}__{safe_title_slug}.txt` |
| Subtitles | `data/transcripts/{podcast_id}/{episode_ref}__{safe_title_slug}.srt` |
| Transcript metadata | `data/transcripts/{podcast_id}/{episode_ref}__{safe_title_slug}.json` |
| Extractive summary | `data/summaries/{podcast_id}/{episode_ref}__{safe_title_slug}.md` |
| Semantic summary | `data/summaries/{podcast_id}/{episode_ref}__{safe_title_slug}.semantic.md` |
| Mentions | `data/mentions/{podcast_id}/{episode_ref}__{safe_title_slug}.mentions.json` and `.mentions.md` |
| Episode intelligence | `data/reports/{podcast_id}/{episode_ref}__{safe_title_slug}.intelligence.json` and `.intelligence.md` |
| Industry mapping | `data/mappings/{podcast_id}/{episode_ref}__{safe_title_slug}.industry-map.json` and `.industry-map.md` |
| External data boundary | `data/external/{podcast_id}/{episode_ref}__{safe_title_slug}.external-boundary.json` and `.external-boundary.md` |
| Stock lens | `data/stock-lens/{podcast_id}/{safe_stock_query}.stock-lens.json` and `.stock-lens.md` |
| Stock lens synthesis | `data/stock-lens/{podcast_id}/{safe_stock_query}.stock-lens-synthesis.json` and `.stock-lens-synthesis.md` |
| SQLite metadata cache | `data/cache/podcast_ingest.sqlite3` |
| Episode cache | `data/cache/{podcast_id}/episodes.json` |

Corpus and workflow run reports, all under `data/corpus/{podcast_id}/`:

| Report | Filenames |
| --- | --- |
| Corpus index | `corpus-index.json`, `corpus-index.md` |
| Episode seed | `episode-seeds/{episode_ref}.episode-seed.json` |
| Episode intake run | `corpus-episode-intake-run.json`, `corpus-episode-intake-run.md` |
| Remediation plan | `corpus-remediation-plan.json`, `corpus-remediation-plan.md` |
| Remediation run | `corpus-remediation-run.json`, `corpus-remediation-run.md` |
| Local transcription run | `corpus-local-transcription-run.json`, `corpus-local-transcription-run.md` |
| Audio download run | `corpus-audio-download-run.json`, `corpus-audio-download-run.md` |
| Episode workflow run | `corpus-episode-workflow-run.json`, `corpus-episode-workflow-run.md` |
| Semantic remediation run | `corpus-semantic-remediation-run.json`, `corpus-semantic-remediation-run.md` |
| Episode completion workflow run | `corpus-episode-completion-workflow-run.json`, `corpus-episode-completion-workflow-run.md` |
| Latest deterministic workflow run | `corpus-latest-episode-deterministic-workflow-run.json`, `corpus-latest-episode-deterministic-workflow-run.md` |
| Verified research checkpoint | `verified-research/{episode_ref}.checkpoint.json` |

Verified research report bundles live outside `data/corpus/`, at
`data/research-reports/{podcast_id}/{episode_ref}/v1-{source_digest}/` and
contain `report.json`, `report.md`, and `manifest.json`.

## CLI reference

Scripts under `scripts/` parse arguments and call the core functions. They add
no logic of their own. Examples use PowerShell, which is the primary
development environment; the same commands work in any shell.

### Episodes, audio, transcripts

```powershell
python scripts/list_episodes.py --podcast gooaye --limit 10
python scripts/list_episodes.py --podcast gooaye --episode latest
python scripts/download_episode.py --podcast gooaye --episode latest
python scripts/transcribe_episode.py --podcast gooaye --episode latest --model tiny --device cpu --compute-type int8
python scripts/validate_transcript.py --podcast gooaye --episode latest
```

To check that faster-whisper, PyAV, and the output plumbing work without
waiting for a full episode, transcribe a short local file:

```powershell
python scripts/transcribe_episode.py --audio-path path\to\sample.mp3 --podcast gooaye --episode smoke-test --model tiny --device cpu --compute-type int8 --force
```

A 50-minute episode can take a long time on CPU. If a timeout leaves a
high-CPU Python process behind, stop it before retrying. With an NVIDIA GPU:

```powershell
python scripts/transcribe_episode.py --podcast gooaye --episode latest --model small --device cuda --compute-type float16
```

### Summaries

```powershell
python scripts/summarize_episode.py --podcast gooaye --episode EP672 --mode extractive --max-quotes 5 --window-seconds 300
```

Summarization only reads an existing transcript; it never downloads or
transcribes. A partial transcript is refused unless you pass `--allow-partial`.

Semantic summaries need an API key and a model. For manual testing, use a local
`.env`, which is gitignored and must not be committed:

```text
API_KEY=your-api-key
MODEL=your-model
BASE_URL=https://api.openai.com/v1
```

```powershell
python scripts/summarize_episode.py --podcast gooaye --episode EP672 --mode semantic --force --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
python scripts/summarize_episode.py --podcast gooaye --episode EP672 --mode semantic --model your-model --base-url https://api.openai.com/v1 --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

LLM-facing CLIs load `.env` by default. Use `--env-file path\to\.env` for a
different file or `--no-env-file` to disable it. A variable already set in the
shell session wins over `.env`. `MODEL` and `BASE_URL` are the current names;
the older `OPENAI_MODEL` and `OPENAI_BASE_URL` are still read as a fallback.
CLI metadata reports which environment variable names were loaded and never
shows secret values. `extractive` mode needs no API key.

Provider profiles live in `config/llm_profiles.yaml` and store only provider,
model, base URL, and the name of the API key environment variable, never a key
value. The working `pro4500` profile uses `api_key_env=API_KEY`, so it pairs
with `API_KEY=...` in `.env`. Explicit `--model`, `--base-url`, and
`--api-key-env` flags override a profile.

### Research artifacts

```powershell
python scripts/extract_mentions.py --podcast gooaye --episode EP672 --force
python scripts/generate_episode_intelligence_report.py --podcast gooaye --episode EP672 --force
python scripts/generate_industry_chain_mapping.py --podcast gooaye --episode EP672 --max-candidates-per-node 3
python scripts/generate_external_data_boundary.py --podcast gooaye --episode EP672 --force
python scripts/verify_external_data_boundary.py --podcast gooaye --episode EP672 --confirm --fixture-path config/external_market_data_fixtures.yaml
python scripts/inspect_gooaye_lens.py --path config/gooaye_lens.yaml
python scripts/generate_stock_lens_report.py --podcast gooaye --stock NVDA --max-evidence-items 5
```

Stock lens synthesis is dry-run first and needs the exact acknowledgement:

```powershell
python scripts/generate_stock_lens_synthesis_report.py --podcast gooaye --stock TSMC
python scripts/generate_stock_lens_synthesis_report.py --podcast gooaye --stock TSMC --llm-profile pro4500 --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

The consolidated workflow runner:

```powershell
python scripts/run_research_workflow.py --podcast gooaye --episode EP672
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --confirm --stock TSMC
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --confirm --include-semantic-summary --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --semantic-model your-model
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --confirm --include-external-data-verification --external-fixture-path config/external_market_data_fixtures.yaml
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --confirm --stock TSMC --include-stock-lens-synthesis --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --synthesis-model your-model
```

### Smoke and review harnesses

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock TSMC --llm-profile pro4500 --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --force --debug-llm-output
python scripts/review_research_llm_smoke.py --podcast gooaye --episode EP672 --stock TSMC
python scripts/run_semantic_summary_smoke.py --podcast gooaye --episode EP672 --llm-profile pro4500
python scripts/review_semantic_summary_smoke.py --podcast gooaye --episode EP672
```

The smoke harness performs a real OpenAI-compatible smoke plus Codex manual
review; there is no direct Codex-session backend, so Codex acts only as a
manual reviewer of artifacts, prompt boundaries, and quality. Semantic summary
must be opted into explicitly because it sends transcript text outside this
machine. Review reports are deterministic: no LLM call, no `.env` read, no
external market data. `--debug-llm-output` writes raw provider output to the
gitignored `evals/research-llm-smoke/raw/` and never into a published artifact.
CLI stdout stays JSON with no raw transcript stdout and no secret values.

### Corpus workflows

```powershell
python scripts/generate_corpus_index.py --podcast gooaye
python scripts/generate_corpus_remediation_plan.py --podcast gooaye
python scripts/run_corpus_episode_intake.py --podcast gooaye --episode latest
python scripts/run_corpus_audio_download.py --podcast gooaye --episode EP672 --confirm
python scripts/run_corpus_local_transcription.py --podcast gooaye --episode EP672 --confirm --model small --device cuda --compute-type float16
python scripts/run_corpus_remediation.py --podcast gooaye --action-family mentions --confirm
python scripts/run_corpus_episode_workflow.py --podcast gooaye --episode latest --stage next --confirm
python scripts/run_corpus_semantic_remediation.py --podcast gooaye --episode EP700 --action semantic_review --confirm
python scripts/run_corpus_episode_completion_workflow.py --podcast gooaye --episode EP677 --action audio_download --confirm
python scripts/run_corpus_latest_episode_deterministic_workflow.py --podcast gooaye --confirm
```

Note the difference in dry-run persistence. `run_corpus_audio_download`,
`run_corpus_local_transcription`, and `run_corpus_remediation` refresh the
corpus index and remediation plan first, so a standalone dry-run still
persists those two files. The workflow runners
(`run_corpus_episode_workflow`, `run_corpus_semantic_remediation`,
`run_corpus_episode_completion_workflow`) use one shared in-memory snapshot
instead, and their dry-run is strict zero-file.

### Verified research reports

```powershell
python scripts/run_latest_episode_verified_research_report_workflow.py --podcast gooaye
python scripts/run_episode_verified_research_report_workflow.py --podcast gooaye --episode EP672
python scripts/query_verified_research_report_catalog.py list --podcast-id gooaye --limit 50
python scripts/query_verified_research_report_catalog.py search "EP672" --podcast-id gooaye
python scripts/query_verified_research_report_catalog.py inspect gooaye EP672 <lowercase-64-hex-source-digest>
python scripts/revalidate_verified_research_report_sources.py gooaye EP672 <lowercase-64-hex-source-digest>
python scripts/query_verified_research_report_coverage.py gooaye --has-bundle false --limit 20
python scripts/suggest_historical_verified_report_next_step.py gooaye
python scripts/list_verified_report_gap_backlog.py gooaye
```

### Cache and search

```powershell
python scripts/rebuild_cache.py --podcast gooaye --force
python scripts/search_transcripts.py --podcast gooaye --query TSMC --limit 10 --search-mode auto
python scripts/search_transcripts.py --podcast gooaye --query TSMC --limit 10 --search-mode like --context-segments 1
python scripts/search_mentions.py --podcast gooaye --query TSMC --type company
```

### MCP servers and validation

```powershell
python scripts/validate_mcp_setup.py --podcast gooaye --query TSMC
python scripts/run_mcp_server.py
python scripts/run_mcp_http_server.py
python scripts/new_mcp_eval_report.py --name codex-session-001
```

## MCP tool registry

The server builds a single `FastMCP` instance. Local Codex and Claude clients
use stdio; the reviewed sidecar serves Streamable HTTP bound to
`127.0.0.1:8767/mcp` only, with no legacy SSE and no published port. Both
transports expose the same registry of exactly 25 reviewed tools.

Read and query tools:

- `list_episodes`
- `get_episode`
- `validate_transcript`
- `search_transcripts`
- `search_mentions`
- `rebuild_cache`
- `query_verified_research_report_catalog` (Tool 17; offline read-only manifest-first list/search/inspect)
- `revalidate_verified_research_report_sources` (Tool 18; exact-locator offline source revalidation)
- `query_verified_research_report_coverage` (Tool 19; episode-centric offline coverage join)
- `suggest_historical_verified_report_next_step` (Tool 20; historical next-step suggestion)
- `list_verified_report_gap_backlog` (Tool 21; inventory gap backlog)
- `generate_stock_lens_report` (Tool 22; deterministic stock lens, side-effect and dry-run first)
- `ingest_x_video` (Tool 23; X video ingest, zero-write preview that reads public metadata)
- `ingest_youtube_video` (Tool 24; YouTube video ingest, zero-write preview that reads public metadata)
- `derive_workflow_bundle` (Tool 25; Spec 042 `05`/`06` workflow derivation, zero-write and zero-network preview; confirm calls an LLM and needs the exact `api_cost_ack`)

Side-effect tools:

- `download_audio`
- `transcribe_episode`
- `summarize_episode_extractive`
- `extract_mentions`
- `semantic_summarize_episode`
- `run_research_workflow`
- `run_corpus_episode_completion_workflow`
- `run_corpus_latest_episode_deterministic_workflow`
- `run_latest_episode_verified_research_report_workflow`
- `run_episode_verified_research_report_workflow`
- `generate_stock_lens_report`
- `ingest_x_video`
- `ingest_youtube_video`
- `derive_workflow_bundle`

Tool 25, `derive_workflow_bundle`, is append-only; the contracts and order of
Tools 1 through 24 are unchanged. Unlike Tools 23 and 24 its preview is also
zero-network: it plans paths without constructing an LLM provider, so it needs
no `api_cost_ack` and makes no call. Confirm forwards the operator's exact
`api_cost_ack` to Core's gate. The tool accepts no provider, model, endpoint,
credential, or workflow-context parameter — the last of those names a file
whose contents reach an LLM prompt.

Tool 24, `ingest_youtube_video`, is append-only; the contracts and order of
Tools 1 through 23 are unchanged. An ingest preview is zero-write but resolves
public metadata over the network, so it is not the zero-network dry-run that
the corpus runners provide.

Every side-effect tool defaults to `confirm=false` and returns an action plan
rather than acting:

```text
Call transcribe_episode with confirm=false first to review the action plan.
Call transcribe_episode again with confirm=true only if you accept the runtime and resource cost.
```

`semantic_summarize_episode` is stricter still: beyond `confirm=true` it needs
the exact `api_cost_ack`, because it sends transcript text to an external
provider. Dry-run never returns raw transcript text and no response ever
returns an API key.

Responses use a JSON envelope. Success is `{"ok": true, "data": ...}`, failure
is `{"ok": false, "error_type": "...", "message": "..."}`, and a dry-run plan
is `{"ok": true, "dry_run": true, "requires_confirmation": true, ...}`.

No side-effect tool rebuilds the SQLite cache when it finishes. Call
`rebuild_cache` yourself to pick up new artifacts. No MCP tool provides
investment advice.

### Client setup and evaluation

- Codex: [`codex-mcp-setup.md`](codex-mcp-setup.md)
- Claude: [`claude-mcp-setup.md`](claude-mcp-setup.md)
- Usage notes: [`mcp-usage.md`](mcp-usage.md)
- Troubleshooting: [`mcp-troubleshooting.md`](mcp-troubleshooting.md)

These documents use placeholder paths only. Do not commit a personal
`.codex/config.toml`, any config containing personal absolute paths, `.env`,
or an API key.
