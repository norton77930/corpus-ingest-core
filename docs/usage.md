# Usage guide

This page is organised by **what you want to do**, not by what the code
exposes. Each task shows the same three ways to reach it: a **CLI command**, a
sentence you can **say to an agent** connected over MCP, and whether a **Skill**
exists to hold the agent to a protocol.

It deliberately does not restate the reference material. When a task needs a
full parameter list, an output path, or a client configuration file, this page
links to the document that owns it:

- [`docs/api.md`](api.md) — every core function, every output path, the full CLI
  reference, and the MCP tool registry
- [`docs/mcp-usage.md`](mcp-usage.md) — tool-by-tool MCP notes
- [`docs/claude-mcp-setup.md`](claude-mcp-setup.md),
  [`docs/codex-mcp-setup.md`](codex-mcp-setup.md) — connecting a client
- [`docs/mcp-troubleshooting.md`](mcp-troubleshooting.md) — when a tool does not
  show up or does not run
- [`docs/install-and-porting.md`](install-and-porting.md) — clean install, GPU
  transcription, moving machines

Nothing this project produces is investment advice.

## Before the first task

Install the package (`pip install -e .[dev]` from a clone, or point a client at
`uvx --from git+... corpus-ingest-mcp`) and register the source you care about.
The install details live in [`CONTRIBUTING.md`](../CONTRIBUTING.md) and
[`docs/install-and-porting.md`](install-and-porting.md).

If you want to see real output before transcribing anything of your own, skip
ahead to [Try it without your own corpus](#try-it-without-your-own-corpus).

## The three sources, and what each one can do

A profile in `config/podcasts.yaml` declares a `source_type`. It defaults to
`rss`, and that default decides which entry points apply to it.

| | `rss` | `x-video` | `yt-video` |
| --- | --- | --- | --- |
| Profile needs | `rss_url`, `default_episode_prefix` | neither | neither |
| Episode discovery | `list_episodes`, `get_episode`, `latest` | none — you supply a post URL | none — you supply a video URL |
| Audio acquisition | `download_audio` from the feed enclosure | `ingest_x_video` | `ingest_youtube_video` |
| Episode reference | `EP672`-style, from the feed | the tweet status id | the video id |
| Local transcription | yes | yes, inside the ingest call | yes, inside the ingest call |
| Summaries, mentions, search, research artifacts | yes | yes, once a transcript exists | yes, once a transcript exists |
| Latest-episode workflows | yes | no | no |

One rule explains every difference above. **Everything that resolves `latest` or
reads a feed enclosure is RSS-only** — `list_episodes`, `get_episode`,
`download_audio`, and the latest-episode workflows all refuse a video profile
with `UnsupportedSourceTypeError` rather than failing somewhere deep in the feed
parser. Everything downstream of a transcript treats all three sources
identically, because by then they are the same artifacts on disk.

The summary shape is a separate choice from the source type. Set
`summary_profile: learning-notes` on any profile whose content is a talk or a
tutorial rather than market commentary; it defaults to `finance`.

## Task: process the latest episode

The whole deterministic chain for one RSS podcast, in one confirmed run: pin the
current latest episode, download, transcribe locally, and stop at
`ready_for_semantic_summary`.

**CLI**

```powershell
python scripts/run_corpus_latest_episode_deterministic_workflow.py --podcast gooaye
python scripts/run_corpus_latest_episode_deterministic_workflow.py --podcast gooaye --confirm
```

**Say to an agent**

> Process the latest Gooaye episode.

**Skill** — yes, `corpus-latest-episode-processing`. It maps the spoken show
name to a configured id, treats your sentence as the one-time authorization,
calls the tool once with `confirm=true`, and stops. It will ask rather than
guess if the name is not an unambiguous configured id.

Run the first command without `--confirm` first if you want to see the plan.
Note that the Skill deliberately skips that preview: your explicit request is
the approval, and a second round trip would add nothing.

## Task: advance one step at a time

The conservative path. Ask what the next step is, look at it, approve it, and
get exactly that one step — nothing chains.

**CLI**

```powershell
python scripts/run_corpus_episode_completion_workflow.py --podcast gooaye --episode EP677 --action next
python scripts/run_corpus_episode_completion_workflow.py --podcast gooaye --episode EP677 --action audio_download --confirm
```

**Say to an agent**

> What is the next step for Gooaye EP677? Do not run it yet.

**Skill** — yes, `corpus-episode-completion`. One preview, one explicit
approval, one matching action, then stop. If the selected action is
`semantic_summary`, the Skill requires *you* to type the exact acknowledgement
string; it is forbidden from synthesizing, shortening, or substituting it.

This is the right shape when an episode is in an unknown state, when a previous
run failed partway, or when you want to keep a hand on each side effect.

## Task: ingest one X or YouTube video

**CLI**

```powershell
python scripts/run_x_video_ingest.py --url "https://x.com/<handle>/status/<id>"
python scripts/run_x_video_ingest.py --url "https://x.com/<handle>/status/<id>" --confirm

python scripts/run_youtube_video_ingest.py --url "https://www.youtube.com/watch?v=<id>"
python scripts/run_youtube_video_ingest.py --url "https://www.youtube.com/watch?v=<id>" --confirm
```

**Say to an agent**

> Bring this video into the corpus: `<url>`

**Skill** — yes, `x-video-ingest` and `youtube-video-ingest`. Both follow the
preview → explain → one approval → one confirmed call → report shape.

Two things are specific to video sources and worth knowing before you approve:

- **The preview is not offline.** `confirm=false` writes nothing, but it has to
  resolve public source metadata over the network before it can name a title or
  plan a write. By the time you are asked to approve, the video host has already
  been contacted once. "Zero-write" and "zero-network" are separate properties;
  see [How the confirmation boundary works](#how-the-confirmation-boundary-works).
- **The source video is never kept.** It is downloaded to a scratch directory,
  the audio track is extracted, and the video is discarded. Only audio,
  transcript, and a metadata run report land under `data/`.

Neither tool takes an `api_cost_ack`, because neither calls an LLM.

A confirmed run needs the profile registered in `config/podcasts.yaml` first —
the ingest refuses an unregistered source *before* downloading rather than
after. `CONTRIBUTING.md` explains why the committed profile set is asserted by a
test, and `examples/` shows how to point `CORPUS_INGEST_CONFIG` at your own
registry instead of editing the committed one.

If YouTube metadata resolves and then the media URL returns `HTTP 403`, your
`yt-dlp` is too old. See [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Task: search a topic across episodes

Search reads the SQLite index, which is built from artifacts already on disk.

**CLI**

```powershell
python scripts/rebuild_cache.py --podcast gooaye --force
python scripts/search_transcripts.py --podcast gooaye --query TSMC --limit 10 --context-segments 1
python scripts/search_mentions.py --podcast gooaye --query TSMC --type company
```

**Say to an agent**

> Search the corpus for what was said about TSMC, and show me the timestamps.

**Skill** — none, and none is needed. These tools are read-only: there is no
side effect to gate, so an agent may call them directly.

One rule matters here. **No tool rebuilds the index behind your back.** After
anything writes a new artifact you get a "cache may be stale" warning, and the
rebuild is yours to trigger. If a search returns nothing you expected, run
`rebuild_cache` before concluding the content is absent.

Use `search_transcripts` for what was literally said and `search_mentions` for
the deterministic company / ticker / industry / macro index. Mentions are
rule-based pattern matching, not semantic understanding.

## Task: produce a verified research report

A verified research report bundle assembles existing artifacts into one
citable, content-digest-versioned unit. Which route you want depends on the
episode.

**CLI**

```powershell
python scripts/run_latest_episode_verified_research_report_workflow.py --podcast gooaye
python scripts/run_episode_verified_research_report_workflow.py gooaye EP672
python scripts/suggest_historical_verified_report_next_step.py gooaye EP672
python scripts/list_verified_report_gap_backlog.py gooaye
```

**Say to an agent**

> Produce a verified research report for Gooaye EP672.

**Skill** — three of them, and they are not interchangeable:

| Situation | Skill |
| --- | --- |
| The latest episode, whole chain | `latest-episode-verified-research-report` |
| One named episode that already has its artifacts | `episode-verified-research-report` |
| One named historical episode, state unknown | `historical-episode-verified-report-path` |

Start with the historical path Skill when you do not know what the episode is
missing. It calls the suggestion tool first, tells you the suggestion code and
which artifact roles are missing or stale, and routes to whichever of the other
two tools actually applies. Reach for the named-episode Skill only when the
inputs are known to be complete.

`list_verified_report_gap_backlog` and
`query_verified_research_report_coverage` answer the inventory question — which
episodes have no bundle yet — without touching anything.

## How the confirmation boundary works

Two separate gates, for two separate reasons.

**`confirm=false` is the default on every tool that writes, downloads, or
spends money.** Called that way, the tool returns an action plan — the inputs it
would use, the paths it would write, the risks — and does nothing. You call it
again with `confirm=true` to execute. This is not a wrapper an agent can decide
to skip: the default lives in the tool signature and a contract test asserts it
for every side-effect tool in the registry.

"Zero-write" is exact. "Zero-network" is not implied by it, and the difference
is per-tool:

| Preview | Writes | Network |
| --- | --- | --- |
| `derive_workflow_bundle` | none | none — it returns before an LLM provider is built |
| corpus episode workflows | none | reads the configured RSS feed to resolve the episode |
| `ingest_x_video`, `ingest_youtube_video` | none | reads public metadata from the video host |

No preview in any row spends money or sends transcript text anywhere. What
differs is whether the preview has already contacted the source by the time it
asks you to approve.

**`api_cost_ack` is a second gate, and only on tools that call an external
LLM.** `confirm=true` alone is not enough; the call also carries an exact
acknowledgement string, and anything other than an exact match is refused before
the request is built. It exists because those calls do something the confirm
gate cannot express: they send transcript text off your machine and they cost
money. Making the operator reproduce the sentence is what keeps that from being
a habit-click.

Two consequences follow, and both are deliberate:

- An agent must not compose the acknowledgement for you. The Skills say so
  explicitly.
- Tools that spend nothing never ask for it. `ingest_x_video`,
  `ingest_youtube_video`, and every deterministic tool take `confirm` only.

The exact string, the per-tool parameter lists, and the LLM provider
configuration are in [`docs/api.md`](api.md).

## Try it without your own corpus

[`examples/sample-corpus/`](../examples/sample-corpus) is a committed,
**entirely synthetic** corpus: a podcast that does not exist, two episodes, and
transcripts written by hand. It ships already indexed, so search, mentions, and
evidence tools return real results with nothing downloaded and nothing
transcribed.

Point two environment variables at it and the same commands from the search
task above work unchanged against podcast id `sample`.
[`examples/README.md`](../examples/README.md) has the exact variables, the
commands, and the reasons the sample corpus is fiction. Do not cite it and do
not read any of it as commentary on a real market.

[`examples/prompts/agent-prompts.md`](../examples/prompts/agent-prompts.md)
carries prompts to try once a client is connected.

## Known limits

These are boundaries, not a backlog:

- **No web UI.** CLI and MCP are the whole interface.
- **No scheduling.** Nothing runs unattended. There is no cron integration, and
  the Skills explicitly forbid an agent from building one as a fallback.
- **No embeddings and no vector search.** Search is SQLite FTS5 with a LIKE
  fallback. "Find semantically similar passages" is not a thing this project
  does.
- **No live market data.** External market data is bounded to local fixtures on
  purpose. Adding a market API would be a reviewed decision, not a feature.
- **No investment advice.** No buy/sell/hold, no target prices, no guaranteed
  returns, nothing personalized.
- **Deterministic and LLM outputs are never merged.** The rule-based path is the
  default and stays re-derivable offline; LLM output is labelled as an LLM
  intermediate artifact and passes a deterministic review gate before anything
  downstream may consume it. [`docs/architecture.md`](architecture.md) explains
  why that separation is load-bearing.

Summaries and extracted mentions can be incomplete or wrong, and LLM-generated
content can be confidently mistaken. Verify anything that matters against the
original audio and a primary source.
