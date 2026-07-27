# Quickstart Validation: Source Revalidation

## Preconditions

Use local filesystem fixtures only. No production source, network, `.env`, provider, cache, output path, or write operation is required.

## Focused scenarios

1. Exact valid locator with unchanged bundle, lineage, and canonical sources returns all passed checks and `current`.
2. Missing/invalid bundle returns bundle failure with downstream `not_evaluated`; fail-if-called lineage/source readers prove no out-of-bundle read.
3. Invalid assembly options, missing/stale lineage, published-lineage mismatch, role/hash/size/canonical-path mutation, digest mismatch, and source replacement race fail closed.
4. Fixture/snapshot/manifest hostile-path sentinels prove canonical-before-read: hostile paths never dereferenced.
5. CLI forwards exactly three inputs once; Tool 18 is append-only and Tools 1–17 unchanged.
6. Writer/network/LLM/cache spies and before/after tree snapshots prove read-only/offline/zero-write.

## Commands during implementation

```powershell
python -m pytest tests/test_spec_021_verified_research_report_source_revalidation_docs.py -q
python -m pytest tests/test_verified_research_report_source_revalidation.py tests/test_verified_research_report_source_revalidation_cli.py -q
```

No invocation accepts latest, batch, output, confirm, acknowledgement, provider, or network flags. Results expose no raw manifest, absolute paths, stock query, or investment advice.
