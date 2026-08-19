# Implementation Plan: Semantic Summary Profiles

**Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)

## Summary

Move the five hardcoded finance prompt strings out of `llm_provider.py` and
`semantic_summarizer.py` into a pure-data registry keyed by profile name, add a
`summary_profile` field to `PodcastProfile` defaulting to `finance`, and thread
the resolved profile through `create_provider` so the
`SemanticSummaryProvider` protocol never changes. `learning-notes` is the second
profile and the proof that the seam is a seam. The rendered Markdown envelope is
a downstream contract and stays frozen; only prompt content and the 摘要限制
body vary.

## Constitution Check

Local artifacts, unchanged paths, unchanged evidence-timestamp discipline (I);
all logic in `src/podcast_ingest_core`, no CLI or MCP surface added (II); this
feature adds no side-effect workflow, and the one it touches keeps its existing
`force` gate (III); the LLM step stays opt-in and `require_exact_api_cost_ack`
keeps its position as the first statement of both `semantic_summarize_episode`
and `create_provider` (IV); both profiles require 不確定事項 and timestamp
traceability, so evidence stays separated from inference (V); no buy/sell/hold
surface is added, and `prohibited_advice` remains an active check on **both**
profiles (VI); no market data, no live provider (VII); no cache rebuild (VIII);
TDD, targeted tests before implementation (IX). **No constitution amendment.**

Principle VI deserves the explicit note rather than a silent pass. Dropping
本摘要不構成投資建議 from one profile *looks* like weakening the investment-safety
principle and is not: the principle is "no advice", the disclaimer is a courtesy
line, and the enforcing check (`matched_investment_advice_guard`) strips
disclaimers before it scans. The gate gets stronger in one narrow sense — a
summary can no longer appear compliant merely by carrying a disclaimer, because
one of the two profiles has none and must pass on its content alone.

Two contract touches are additive and backward-compatible, and are the parts
worth reviewing rather than assuming: `PodcastProfile` gains `summary_profile`
with a `"finance"` default, and `create_provider` gains a keyword-only
`summary_profile` with the same default. Existing profiles and existing call
sites MUST behave identically.

## Design Decisions

1. **A new field, not `source_type`.** `source_type` answers where content came
   from; the summary shape answers what the content is. The first X finance
   account or YouTube AI channel breaks the coupling, and it breaks it in a way
   that requires re-deriving every already-written summary. Two fields cost one
   dataclass attribute.
2. **The factory carries the profile; the protocol does not move.**
   `summarize_chunk` / `summarize_final` are faked at five sites. Passing the
   profile into `create_provider` leaves all five untouched, which is also the
   evidence that the protocol did not move — a test that had to be edited would
   prove the opposite. Building messages in `semantic_summarizer` and calling
   `provider.complete()` is the textbook-cleaner layering and was rejected: the
   fakes intercept at `summarize_*`, so it converts five working fakes into five
   rewrites for a layering improvement nothing in this repo needs yet.
3. **Prompts become data, in their own module.** `llm_provider.py` is transport —
   HTTP, auth, timeouts, the `api_cost_ack` gate. A frozen dataclass registry in
   `summary_profiles.py` with no imports beyond `dataclasses` and `.errors` can
   be tested without constructing a provider, without a network stub, and
   without an `api_cost_ack`. That testability is the actual reason, not tidiness.
4. **The envelope is frozen, and the freeze is asserted.** Four downstream
   readers depend on the rendered structure (`semantic_review_artifact.py:143`
   and `:151`, `stock_lens_synthesis.py:494`, `verified_research_lineage.py:820`).
   The profile varies the 摘要限制 *body* and nothing else structural. A test
   asserts the envelope for the `learning-notes` profile specifically, because
   that is the profile a future edit would break first.
5. **`finance` is pinned against literals, not against the implementation.** The
   regression test hardcodes today's prompt strings. Asserting
   `build_chunk_prompt(FINANCE, chunk) == _chunk_prompt(chunk)` would pass even
   if both drifted together; hardcoding is what makes 股癌's output a fixed point.
6. **Unknown values are refused at load.** This is deliberately *stricter* than
   how `source_type` is handled today: `config._parse_profile:86` accepts any
   `source_type` string, and enforcement lives at the RSS surfaces, which is why
   Spec 036's X surface could silently accept a typo until the review caught it.
   `summary_profile` has no downstream surface that would refuse it — an unknown
   value would either crash deep inside prompt building or, worse, fall back to
   finance silently. Load-time refusal is the only place that fails loudly and
   before it costs an API call. `source_type` is **not** retrofitted here; that
   asymmetry is recorded as a follow-up, not fixed in this scope.
7. **The extractive summariser follows the same field.** One field, two
   renderers, no second concept. It is sequenced last because it is the least
   consumed surface and its byte-equality requirement is the same shape as the
   semantic one.

## Registry Impact

**None.** No MCP tool is added; the registry stays at exactly 22 with Tools 1-22
unchanged in name, order, signature, and defaults.
`tests/test_mcp_tool_registry_contract.py` and the docs-count checker must stay
green **without modification** — if either needs editing, the change has drifted
out of scope.

## Project Structure

```text
specs/037-semantic-summary-profiles/
src/podcast_ingest_core/summary_profiles.py     (new: frozen registry, pure data + lookup)
src/podcast_ingest_core/models.py               (PodcastProfile.summary_profile)
src/podcast_ingest_core/config.py               (_parse_profile validates the value)
src/podcast_ingest_core/errors.py               (reuse or add the config error type)
src/podcast_ingest_core/llm_provider.py         (prompts read from the registry; factory takes the profile)
src/podcast_ingest_core/semantic_summarizer.py  (resolve profile -> factory; 摘要限制 body from the profile)
src/podcast_ingest_core/summarizer.py           (extractive prompt block from the profile)
src/podcast_ingest_core/__init__.py             (export the registry lookup if the package exports peers)
config/podcasts.yaml                            (x-raytar: summary_profile: learning-notes)
tests/test_summary_profiles.py                  (new: registry, lookup, unknown-value refusal,
                                                 finance prompts pinned to hardcoded literals)
tests/test_semantic_summarizer.py               (learning-notes rendering; finance byte-equality)
tests/test_podcast_profile_source_type.py       (profile-field tests live here since Spec 036)
tests/test_summarizer.py                        (extractive block per profile)
tests/test_contracts.py                         (deliberate contract update — see below)
docs/architecture.md, docs/verification-matrix.md, specs/README.md
```

There is no `tests/test_llm_provider.py` and no `tests/test_config.py`; a first
draft of this plan named both and neither exists. The real surfaces are
`tests/test_llm_provider_factory_boundary.py` (which must stay green
**unmodified**) and profile parsing, which is covered by `tests/test_contracts.py`
and `tests/test_podcast_profile_source_type.py`.

`tests/test_contracts.py` is called out because Spec 036 was bitten by exactly
this file. Grepped before planning rather than during implementation, it pins
three things that matter here:

- `:12-31` — the exact profile set `{"gooaye", "x-raytar"}` and each profile's
  field values. Adding `summary_profile` does not break it, because it asserts
  named fields rather than a field set. Asserting the new field there is a
  deliberate contract update and lands in the same commit.
- `:22` and `:30` — `summarize_episode` and `semantic_summarize_episode` have
  their exact parameter lists pinned via `inspect.signature`. This is
  independent confirmation of FR-009: a per-run profile argument would break a
  pinned contract, and the config-driven design keeps both pins green untouched.
- `create_provider` is **not** in that pinned list, but
  `tests/test_llm_provider_factory_boundary.py:78` pins `api_cost_ack` as
  keyword-only with an empty default. A keyword-only `summary_profile` keeps it
  green; a positional one would not.

## Risks

- **Silent drift of 股癌's summaries is the only severe risk here.** Every
  already-published verified research report descends from a semantic summary.
  A prompt that changes by one character changes future summaries for a corpus
  the repo treats as an evidence chain. Mitigation is byte-equality against
  hardcoded literals, and it is a gate, not a nice-to-have.
- **The `api_cost_ack` guard sits in the function being edited.**
  `create_provider` gains a parameter, and `require_exact_api_cost_ack` is its
  first statement. Adding a parameter is not supposed to move a guard, which is
  exactly why unmoved guards get missed in review. A test asserts that
  `create_provider` with a wrong ack raises **before** any profile lookup runs,
  so an invalid profile name cannot mask or precede the ack failure.
- **`stock_lens_synthesis` is profile-blind.** It splits any semantic summary on
  `## Chunk Summaries` and treats the first half as market-shaped prose. Nothing
  points it at a learning-notes summary today, and this change does not point it
  there — but it is now *possible* in a way it was not before, and it is
  recorded rather than discovered.
- **`_optional_text` swallows non-strings.** `config._parse_profile` resolves
  `source_type: 123` to the default rather than raising. The same helper will
  read `summary_profile`, so validation must run on the *resolved* value and a
  non-string must not quietly become `finance`.
- **Scope creep toward the multi-document sequence.** The prototype's 00-07 docs
  are seductive and out of scope. The line: this spec changes what the LLM is
  asked for inside one existing artifact. Any new file, family, or path is drift.

## Verification

```powershell
python -m pytest tests/test_summary_profiles.py tests/test_podcast_profile_source_type.py -q
python -m pytest tests/test_semantic_summarizer.py tests/test_summarizer.py -q
python -m pytest tests/test_llm_provider_factory_boundary.py tests/test_llm_ack_guard_contracts.py -q
python -m pytest tests/test_semantic_summary_smoke_review.py tests/test_corpus_semantic_remediation_runner.py tests/test_spec_018_closure.py -q
python -m pytest tests/test_mcp_tool_registry_contract.py tests/test_contracts.py -q
python -m pytest -q --tb=no -ra
python -m compileall src scripts
```

Baseline to beat: **24 failed / 1584 passed**, the pre-existing blocked chain
recorded at the close of Spec 036. Any new failure outside that list is a defect
in this change.

End-to-end acceptance, run once after the unit gates pass. It costs one LLM call
and requires the exact `api_cost_ack`:

```powershell
python scripts/summarize_episode.py --podcast x-raytar --episode 2071290493581840707 `
  --mode semantic --force --api-cost-ack "<exact ack>"
python scripts/generate_corpus_index.py --podcast x-raytar      # semantic_summary family still available
python scripts/generate_corpus_index.py --podcast gooaye        # byte-identical to baseline
```

Read the produced summary and confirm by eye what no assertion can: that it
reads as study material rather than as market commentary with the nouns swapped.
