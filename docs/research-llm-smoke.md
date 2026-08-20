# Research LLM Smoke

Phase 6O validates whether the existing research workflow can produce a useful LLM-assisted research draft.

This is a smoke and review harness, not a new research capability. It uses the existing OpenAI-compatible provider path for real LLM calls and uses Codex manual review to judge artifact quality. There is no direct Codex-session backend inside the repo.

## Boundary

- Real LLM runtime: OpenAI-compatible smoke via `/chat/completions`.
- Codex role: Codex manual review of prompts, artifacts, and quality notes.
- Stock lens synthesis input: Phase 6F stock lens JSON only by default; Phase 6V can opt into reviewed semantic context.
- Semantic summary input: transcript text, only when explicitly requested.
- External data: no live market data lookup.
- Safety: exact `api_cost_ack`, no investment advice, no target price, no guaranteed return.

## Environment

Set provider configuration outside the repo. The recommended local flow is a `.env` file in the repo root; `.env` is ignored by git and must not be committed.

```text
API_KEY=your-api-key
MODEL=your-model
BASE_URL=https://api.openai.com/v1
```

The smoke CLI loads `.env` by default. Use `--env-file path\to\.env` to choose a different file, or `--no-env-file` to disable local env loading. PowerShell session environment variables take precedence over `.env`. The CLI may report `env_file_loaded`, `env_file_path`, and loaded env var names, but it does not print env var values.

`MODEL` and `BASE_URL` are the preferred names. If they are missing, the provider still accepts the legacy `OPENAI_MODEL` and `OPENAI_BASE_URL` compatibility fallback.

LLM profiles live in `config/llm_profiles.yaml`. Profiles store provider metadata only: provider name, model, base URL, and API key environment variable name. They must not contain API key, token, or secret values.

For the local PRO4500 profile:

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --llm-profile pro4500
```

The committed `pro4500` profile uses `api_key_env: API_KEY`, so the key can live in `.env` as `API_KEY=...`. The committed `gb10` profile is unavailable: loading it fails closed and names `pro4500` as the replacement.

CLI flags override profile values, so `--model`, `--base-url`, or `--api-key-env` can still be used for one-off tests.

## Dry-run

Dry-run first. This lists planned workflow steps, LLM risks, cost/data-transfer risks, expected artifact paths, and the exact acknowledgement.

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --model your-model
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --llm-profile pro4500
```

By default, the smoke workflow includes stock lens synthesis and fixture external data verification. It does not include semantic summary unless `--include-semantic-summary` is passed.

## Confirmed Smoke

Confirmed execution requires the exact acknowledgement string:

```text
I understand this may call an external LLM API, send transcript text outside this machine, and incur costs.
```

Run stock lens synthesis smoke:

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --model your-model --force
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --llm-profile pro4500 --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --force --debug-llm-output
```

Run semantic summary plus stock lens synthesis smoke only when you accept transcript transfer:

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --confirm --include-semantic-summary --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --model your-model --force
```

## Phase 6U Semantic Summary Smoke

Phase 6U validates the direct semantic summary LLM path. This path can send transcript text outside this machine only after exact `api_cost_ack`.

Dry-run lists transcript validation status, planned reads/writes, provider metadata, transcript transfer risk, cost risk, and the required acknowledgement. It does not call the LLM, write artifacts, read API key values, or print raw transcript text.

```powershell
python scripts/run_semantic_summary_smoke.py --podcast gooaye --episode EP672 --llm-profile pro4500
python scripts/run_semantic_summary_smoke.py --podcast gooaye --episode EP672 --llm-profile pro4500 --confirm --force --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
python scripts/review_semantic_summary_smoke.py --podcast gooaye --episode EP672
```

The semantic summary review command is deterministic. It reads the existing `.semantic.md`, checks timestamp evidence, chunk summaries, metadata, secret / traceback / raw transcript dump markers, and prohibited advice. It does not call an LLM, read `.env`, fetch live market data, change MCP tools, rebuild cache, or provide investment advice. CLI output keeps no raw transcript stdout and does not expose secret values.

Phase 6U.1 narrows the semantic review guard to avoid false positive failures on transcript-derived descriptions such as a speaker saying they bought or held something in the past. Direct advice remains prohibited. Confirmed semantic smoke writes stderr progress for chunk count, chunk start/done, and final summary start/done; stdout remains JSON and progress never includes raw transcript text, prompts, API keys, or LLM response content.


## Phase 6V Reviewed Semantic Context

Phase 6V lets stock lens synthesis optionally include reviewed semantic summary context. The default remains Phase 6F stock lens JSON only. Add `--include-semantic-context` only after the relevant `.semantic.md` has a latest passed semantic review report.

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --llm-profile pro4500 --confirm --force --include-semantic-context --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
python scripts/generate_stock_lens_synthesis_report.py --podcast gooaye --stock 台積電 --llm-profile pro4500 --confirm --force --include-semantic-context --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

When context is included, the LLM input boundary is `phase-6f-stock-lens-json-plus-reviewed-semantic-summary`. The context is compact: metadata plus final summary only, with `## Chunk Summaries` excluded. It is reviewed LLM intermediate context, not raw transcript evidence, not external market data, and not a live market fact. Phase 6V makes no MCP tool changes, reads no `.env` values, fetches no live market API, and preserves no investment advice. Phase 6V.1 aligns the deterministic review gate with boundary/context consistency: JSON-only artifacts must have no semantic context, while reviewed semantic artifacts must include non-empty, review-passed semantic context.
## Debug Raw LLM Output

Use `--debug-llm-output` only when diagnosing a provider response. It writes the stock lens synthesis raw LLM output to `evals/research-llm-smoke/raw/`, which is ignored by git via `evals/**/raw/`. The raw file is not a formal artifact and may contain text rejected by the investment-advice guard.

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --confirm --debug-llm-output --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs." --model your-model --force
```

## Codex Manual Review

After a confirmed smoke run, ask Codex to review the generated artifacts, especially:

- `data/stock-lens/{podcast_id}/{stock}.stock-lens.json`
- `data/stock-lens/{podcast_id}/{stock}.stock-lens-synthesis.md`
- optional `data/summaries/{podcast_id}/*.semantic.md`

Review criteria:

- Podcast evidence / inference / external status separation is clear.
- `not_fetched` and `not_requested` are not presented as market facts.
- Inferred candidates remain research leads, not podcast mentions.
- Gooaye Lens dimensions are covered.
- No buy/sell/hold, target price, guaranteed return, or market recommendation appears.

Record the review in `evals/research-llm-smoke/phase-6o-llm-smoke-template.md`.

## Deterministic Review Gate

Phase 6T adds a deterministic review report after confirmed smoke. It reads existing synthesis artifacts and writes timestamped reports under `evals/research-llm-smoke/reports/`.

```powershell
python scripts/review_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電
```

The review gate checks the stock lens synthesis input boundary, no-investment-advice flag, obvious secret or traceback leaks, prohibited advice patterns, external boundary wording, and evidence / inference / external status separation. Phase 6V.1 accepts the default `phase-6f-stock-lens-json-only` boundary only when no semantic context is present, and accepts `phase-6f-stock-lens-json-plus-reviewed-semantic-summary` only when `source_semantic_context` is non-empty and every entry has `review_status=passed` with content. It is a heuristic quality gate and does not replace manual review. It does not call an LLM, read `.env`, fetch external market data, or rewrite smoke artifacts.

## Common Failures

- Missing model: set `MODEL` in `.env` or pass `--model`. Legacy `OPENAI_MODEL` is still accepted as a fallback.
- Missing API key: set `API_KEY` in `.env` or pass `--api-key-env` for another env var name.
- pro4500 profile missing API key: set `API_KEY`; do not put the key in `config/llm_profiles.yaml`.
- gb10 profile unavailable: use `--llm-profile pro4500`.
- Wrong acknowledgement: copy the exact `api_cost_ack` string.
- Missing stock lens source: run workflow dry-run first and inspect planned writes.
- Review gate failed: inspect the `.review.md` check table before tuning the prompt or guard.
- Cache stale: run `python scripts/rebuild_cache.py --podcast gooaye --force` manually after artifacts are generated.
