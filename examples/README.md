# Examples

Everything you need to point an MCP client or the CLI at this project and get a
real answer back within a minute, without downloading or transcribing anything.

```
examples/
  generate_sample_corpus.py    regenerates the sample corpus below
  sample-corpus/               a committed, fully synthetic corpus
    podcasts.yaml              its own profile registry
    data/                      transcripts, summaries, mentions, SQLite index
  mcp/                         client configuration snippets
  prompts/agent-prompts.md     prompts to try against the server
```

## The sample corpus is fiction

**Nothing in `sample-corpus/` is a real podcast.** There is no real show, no
real transcript, and no real audio anywhere in this directory. The podcast, the
two episodes, both hosts, and every company, price and statistic in the
transcripts were written by hand for this demo:

- **The Synthetic Signal** -- a podcast that does not exist
- **Ada Kestrel** and **Milo Vance** -- hosts who do not exist
- **Harbour Robotics**, **Northwind Logistics**, **Meridian Grid** -- invented
  companies, deliberately not modelled on any real one, with no ticker
- every number in the transcripts -- invented, and said to be invented in the
  transcripts themselves

Do not cite it, do not train on it as if it were speech, and do not read any of
it as commentary on a real market. It exists so that a person or an agent can
exercise the query tools before spending twenty minutes on a real episode.

### There is no audio

The corpus starts at the transcript stage, so `data/audio/` is empty and no
`.mp3` or `.wav` is committed anywhere. The transcript JSON still records the
path where audio *would* live, because that is what the real pipeline writes.

### Why `data/` is committed here

The repository root `.gitignore` ignores every directory named `data/` so no
real runtime artifact can be committed by accident. `sample-corpus/.gitignore`
re-includes this one tree, and only this one. That policy is unchanged for
every other `data/` directory, including the repository's own.

## Point the tools at it

Two environment variables do all the work. `CORPUS_INGEST_DATA_DIR` moves the
artifact root; `CORPUS_INGEST_CONFIG` moves the podcast profile registry. The
sample corpus ships its own registry rather than adding a profile to
`config/podcasts.yaml`, because `tests/test_contracts.py` asserts the exact
profile set of that committed file on purpose.

Both are read at import time, so set them before starting the process. Run from
the repository root; the paths below are relative to it.

PowerShell:

```powershell
$env:CORPUS_INGEST_DATA_DIR = "examples/sample-corpus/data"
$env:CORPUS_INGEST_CONFIG   = "examples/sample-corpus/podcasts.yaml"

python scripts/search_transcripts.py --podcast sample --query harbour --limit 5
python scripts/search_mentions.py --podcast sample --query GPU --limit 5
python scripts/validate_transcript.py --podcast sample --episode SAMPLE-001
python scripts/rebuild_cache.py --podcast sample --force
```

bash / zsh:

```bash
export CORPUS_INGEST_DATA_DIR=examples/sample-corpus/data
export CORPUS_INGEST_CONFIG=examples/sample-corpus/podcasts.yaml

python scripts/search_transcripts.py --podcast sample --query harbour --limit 5
python scripts/search_mentions.py --podcast sample --query GPU --limit 5
python scripts/validate_transcript.py --podcast sample --episode SAMPLE-001
python scripts/rebuild_cache.py --podcast sample --force
```

The MCP server reads the same two variables. Start it in the foreground:

```powershell
$env:CORPUS_INGEST_DATA_DIR = "examples/sample-corpus/data"
$env:CORPUS_INGEST_CONFIG   = "examples/sample-corpus/podcasts.yaml"
corpus-ingest-mcp
```

```bash
CORPUS_INGEST_DATA_DIR=examples/sample-corpus/data \
CORPUS_INGEST_CONFIG=examples/sample-corpus/podcasts.yaml \
corpus-ingest-mcp
```

For a client that launches the server itself, put both variables in the client's
`env` block instead -- see the snippets in [`mcp/`](mcp/), which already have
the right keys and only need the two values changed to the paths above.

### Things to search for

The transcripts were seeded with terms the query tools can actually find:

| Query | Tool | What comes back |
| --- | --- | --- |
| `harbour`, `northwind`, `meridian` | `search_transcripts` | the invented company names, with hits in both episodes |
| `timestamp`, `fictional`, `invented` | `search_transcripts` | the corpus talking about itself |
| `GPU`, `AI` | `search_mentions` | `industry` mentions with timestamp evidence |
| `CPI`, `GDP` | `search_mentions` | `macro_topic` mentions with timestamp evidence |

Episode references are `SAMPLE-001` and `SAMPLE-002`; the `podcast_id` is
`sample`. Note that both the CLI and the MCP tools default to a different
podcast, so pass `--podcast sample` / `podcast_id="sample"` explicitly.

### What works here, and what does not

The sample corpus has no RSS feed, because it has no source to have a feed for.
That splits the read-only surface in two:

| Tool | Sample corpus | Why |
| --- | --- | --- |
| `search_transcripts` | works | reads the committed SQLite index |
| `search_mentions` | works | reads the committed SQLite index |
| `validate_transcript` | works | reads the committed transcript files |
| `rebuild_cache` | works | re-indexes the committed files, no network |
| `list_episodes` | **refuses** | feed-backed; the profile is not an RSS source |
| `get_episode` | **refuses** | feed-backed; the profile is not an RSS source |

The refusal is deliberate and explicit, not a crash: the profile declares
`source_type: synthetic`, which no ingestion path claims, so
`config.require_rss_profile` rejects it with a message naming the reason. An
MCP client gets a normal `ok: false` error envelope. Nothing tries to reach the
network.

Everything downstream of a feed is unavailable for the same reason:
`download_audio` has nothing to download, and `transcribe_episode` has no audio
to transcribe. The LLM tools (`semantic_summarize_episode` and the research and
stock-lens workflows) are not blocked by the corpus, but they need an API key
and an explicit cost acknowledgement, so they are not part of the no-setup path
this corpus exists for.

`search_mentions` returns `industry` and `macro_topic` mentions only. Mention
extraction is rule-based against a fixed vocabulary, and the `company` and
`stock_or_ticker` rules are lists of real, listed companies and their tickers.
The invented companies in this corpus match none of them, and putting a real
listed company into a corpus that is otherwise entirely fictional would be
worse than the gap. So a `mention_type="company"` query correctly returns
nothing here; try `mention_type="industry"` instead.

## MCP client configuration

Three snippets in [`mcp/`](mcp/), one per client. Each one launches
`corpus-ingest-mcp` over stdio; set the two `env` values to the sample-corpus
paths above to start against this corpus.

| File | Client | Where it goes |
| --- | --- | --- |
| [`mcp/claude_desktop_config.json`](mcp/claude_desktop_config.json) | Claude Desktop | merge into `%APPDATA%/Claude/claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) |
| [`mcp/mcp.json`](mcp/mcp.json) | Claude Code | save as `.mcp.json` in your project root, or use `claude mcp add` |
| [`mcp/codex_config.toml`](mcp/codex_config.toml) | Codex CLI | merge into `~/.codex/config.toml` |

## Prompts

[`prompts/agent-prompts.md`](prompts/agent-prompts.md) is a short set of prompts
to type at an agent once the server is connected. They cover the read-only
tools, the `confirm=false` boundary that every writing or spending tool sits
behind, and the product boundary this project refuses to cross -- no buy, sell
or hold recommendations, and no live market data. Each prompt names the tool a
correct agent should reach for, so they double as a quick check that the server
is wired up.

For the full evaluation suite, with expected behaviour and pass/fail criteria
per case, see [`docs/mcp-eval-prompts.md`](../docs/mcp-eval-prompts.md).

## Regenerating the corpus

```bash
python examples/generate_sample_corpus.py
```

It runs in a couple of seconds, needs no network, no audio, and no API key, and
it never touches the repository's own `data/`. It deletes and rebuilds
`sample-corpus/data/` so a re-run is a clean overwrite rather than a merge.

Only the transcripts are authored by hand, and they live in the generator as
literal text. Everything downstream -- the deterministic summaries, the mention
indexes, the SQLite cache -- is produced by calling the same core functions the
real pipeline calls, and the transcript files themselves are serialized by the
transcriber's own writer. That is the point: a hand-written fixture drifts from
the real schema the moment the pipeline changes, and an agent that learns the
wrong shape from a stale fixture is worse off than one with no fixture at all.

Regenerating produces byte-identical output except for three things, all
expected:

- the transcript JSON's `generated_at`, which is the current UTC time
- path fields inside the transcript JSON, which use the path separator of the
  operating system that generated them
- `data/cache/podcast_ingest.sqlite3`, which stamps each indexed episode with
  an `updated_at` time; it is derived data, and `rebuild_cache` recreates it
  from the committed files at any time

Edit the transcripts in `generate_sample_corpus.py` and re-run to change what
the corpus says. Keep it fictional.
