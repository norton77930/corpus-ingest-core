# Gooaye Research System Quickstart

This quickstart assumes an episode already has a valid transcript. It is for local manual validation after Phase 7A and keeps the same safety boundary as Phase 6T.

## Local LLM Configuration

Use `.env` for local CLI convenience only. `.env` must not be committed.

```text
API_KEY=your-local-key
MODEL=PRO4500
BASE_URL=https://api.example.com/v1
```

The `pro4500` profile in `config/llm_profiles.yaml` stores provider metadata only. The committed `gb10` profile is unavailable and fails closed. Do not store API key values in YAML or docs.

## Deterministic Workflow Dry-run

```powershell
python scripts/run_research_workflow.py --podcast gooaye --episode EP672 --stock 台積電 --include-external-data-verification --include-stock-lens-synthesis
```

Dry-run lists planned reads/writes, optional LLM risk, fixture verification, cache stale warning, and required acknowledgement. It writes nothing.

## Confirmed Stock Lens Synthesis Smoke

Use the exact acknowledgement string when running confirmed LLM steps:

```text
I understand this may call an external LLM API, send transcript text outside this machine, and incur costs.
```

```powershell
python scripts/run_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電 --llm-profile pro4500 --confirm --force --debug-llm-output --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

The smoke command uses stock lens synthesis by default. It sends Phase 6F stock lens JSON only, not raw transcript. Semantic summary remains opt-in because it can send transcript text.

## Phase 6T Review Gate

After confirmed smoke, run the deterministic Phase 6T review gate:

```powershell
python scripts/review_research_llm_smoke.py --podcast gooaye --episode EP672 --stock 台積電
```

The review gate reads existing synthesis artifacts and writes timestamped review reports. It makes no LLM call, performs no `.env` read, uses no live market API, and preserves no investment advice boundaries.

## Acceptance Check

- Review status is `passed`, or any `warn` / `failed` item is understood before prompt tuning.
- Direct podcast evidence, inferred research leads, and external status remain separated.
- `not_requested`, `not_fetched`, and `data_date=null` are not presented as market facts.
- No buy/sell/hold recommendation, target price, guaranteed return, or personalized investment advice appears.
