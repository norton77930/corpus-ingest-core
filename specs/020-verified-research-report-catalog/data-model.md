# Data Model: Verified Research Report Catalog

## Canonical locator and directory layout

A locator has exact safe identifier fields:

| Field | Rule |
| --- | --- |
| `podcast_id` | Nonempty exact safe identifier; no path separator, dot segment, absolute path, URI, or wildcard |
| `episode_ref` | Nonempty exact safe identifier with the same path restrictions |
| `source_digest` | Exactly lowercase `[a-f0-9]{64}` |

The only accepted version directory name is `v1-{source_digest}`, equivalent to `v1-[a-f0-9]{64}`.

```text
data/research-reports/{podcast_id}/{episode_ref}/v1-{source_digest}/
  report.json
  report.md
  manifest.json
```

Public data uses the locator and `report_version`; it never returns source paths or absolute paths.

## Safe metadata projection

List/search may expose only validated scalar values from a parsed manifest:

| Public field | Manifest source | Validation / use |
| --- | --- | --- |
| `podcast_id`, `episode_ref` | `episode_identity` | Exact match to directory locator |
| `report_version`, `source_digest` | top-level fields | Must match canonical directory |
| `schema_version` | top-level field | Exact supported schema |
| `include_fixture_verification` | `assembly_options` | Boolean only |
| `stock_query_present` | `assembly_options.stock_query` | Boolean presence only; never query value |
| `semantic_review_status` | `quality_gates` | Must be scalar `passed` for eligible summary |
| `not_investment_advice` | `quality_gates` | Boolean only |

Search normalizes a nonblank query by Unicode casefold and whitespace collapse, then matches it against casefolded values of `podcast_id`, `episode_ref`, `report_version`, and `source_digest` only. It never indexes manifest path, lineage, source artifacts, bundle file metadata, arbitrary manifest text, report body, or transcript body.

## List and search page

| Field | Meaning |
| --- | --- |
| `items` | Sanitized eligible bundle summaries, deterministic order |
| `limit` | Applied integer in `1..100`; default `50` |
| `returned_count` | Number of returned items |
| `catalog_root_status` | `missing` or `available`; no path value |
| `traversal_status` | `complete` or bounded `incomplete` with category-only reason |

An entry cap of 1,000 applies separately at each enumerated level. Traversal is root → direct podcast children → direct episode children → direct version children only. No recursive glob is allowed.

## Inspect verdict

| Field | Meaning |
| --- | --- |
| `locator` | Exact public locator (no filesystem path) |
| `bundle_self_consistency_status` | `valid`, `invalid`, or `not_found` |
| `checks` | Bounded named booleans/categories: containment, canonical_version, exact_file_set, manifest_schema, identity, report_json_integrity, report_markdown_integrity |
| `source_currentness_status` | Always `not_evaluated` |
| `safe_metadata` | Projection above, only when parsed and safe |
| `not_investment_advice` | Boolean when safely derived; otherwise omitted |

`valid` requires exactly `report.json`, `report.md`, and `manifest.json`, all regular in-root non-reparse files; JSON manifest object; `schema_version == REPORT_SCHEMA_VERSION == "latest-episode-verified-research-report-v1"` from `src/corpus_ingest_core/verified_research_report.py`; manifest locator equals directory locator; `report_version == "v1-{source_digest}"`; report JSON identity equals locator; and SHA-256/size of both report files equals `manifest.bundle_files` metadata. `manifest.json` is capped at 1 MiB and each report snapshot at 16 MiB; an exceeded bound is invalid. It does not validate report narrative content, source artifacts, lineage, or freshness.

## Rejected data

Symlink, junction, special file, resolved out-of-root path, malformed JSON, unsupported schema, noncanonical names, extra/missing files, unsafe scalar text, or failed integrity check is not an eligible list/search item. Inspect returns only its bounded category; it returns no raw manifest.
