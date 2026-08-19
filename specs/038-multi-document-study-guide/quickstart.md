# Quickstart: Multi-Document Study Guide

Validation only. Do not run a live LLM call until targeted tests and full pytest are green, and the operator asks for the real episode.

## Prerequisites

- Existing canonical `learning-notes` semantic summary
- Profile `summary_profile: learning-notes` (x-raytar already has this)
- Exact `api_cost_ack` only for confirmed generation

## Dry-run (always first)

```powershell
python scripts/run_study_guide_bundle.py --podcast x-raytar --episode 2071290493581840707
```

Expect `confirm: false`, `dry_run: true` or `run_mode: dry-run`, planned reads naming the `.semantic.md`, planned writes or reuses for the four files, zero new files under `data/study-guides/`.

## Confirm (operator-authorised)

```powershell
python scripts/run_study_guide_bundle.py --podcast x-raytar --episode 2071290493581840707 --confirm --api-cost-ack "<exact ack>"
```

Expect four files under `data/study-guides/x-raytar/2071290493581840707__<title_slug>/`. Then:

```powershell
python scripts/generate_corpus_index.py --podcast x-raytar
```

`study_guide` is `available` for that episode. gooaye's index is unchanged.

## Refuse cases

```powershell
python scripts/run_study_guide_bundle.py --podcast gooaye --episode EP678
```

Must refuse `learning-notes` requirement and write nothing.

## Cache

The run does not rebuild SQLite. Rebuild by hand only if the bundle must become searchable (v1 does not index study-guide body into FTS).
