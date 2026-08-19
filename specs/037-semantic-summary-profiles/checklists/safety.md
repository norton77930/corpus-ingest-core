# Safety Checklist: Semantic Summary Profiles

Unchecked — v1 is not implemented. Each box is a gate for Phase 2/3.

## The regression gate (this feature's real danger)

- [ ] A gooaye episode's rendered semantic Markdown is **byte-identical** before
      and after, for the same fake-provider input
- [ ] The extractive summary's rendered Markdown is byte-identical for the
      finance default
- [ ] Finance chunk and final prompts asserted string-equal to **hardcoded
      literals** in the test, not to the implementation
- [ ] `tests/test_semantic_summarizer.py:209` (投資免責聲明) passes unmodified
- [ ] Every already-published verified research report's lineage stays valid:
      `SUMMARY_MODE` unchanged, `summary_mode == "semantic-llm"` still true

## The LLM and secret boundary

- [ ] `require_exact_api_cost_ack` remains the first statement of both
      `create_provider` and `semantic_summarize_episode`
- [ ] A wrong `api_cost_ack` raises **before** the profile is resolved, so an
      invalid profile name can never precede, mask, or substitute for an ack failure
- [ ] `_PROVIDER_FACTORY_TOKEN` remains the only construction path;
      `tests/test_llm_provider_factory_boundary.py` passes **without modification**
- [ ] No `.env` read, no API key, token, or provider config in any prompt, log,
      error message, or rendered summary
- [ ] `summary_profiles.py` performs no IO, no network, no env read

## Investment safety (Principle VI)

- [ ] `prohibited_advice` remains an active check on **both** profiles
- [ ] A learning-notes summary with no disclaimer returns `prohibited_advice=pass`
      — proving the check never depended on the disclaimer
- [ ] A learning-notes summary that *does* contain advice-shaped text still
      returns `prohibited_advice=fail` — proving the profile is not an escape hatch
- [ ] The finance profile keeps 本摘要不構成投資建議 exactly as today
- [ ] No buy/sell/hold, target price, guaranteed return, or personalized
      recommendation surface is added by either profile

## Evidence separation (Principles I and V)

- [ ] Both profiles require timestamp traceability and a 不確定事項 section
- [ ] The learning-notes constraint forbids content the transcript does not
      contain, so inference never enters as evidence

## Contract and blast radius

- [ ] The rendered envelope is unchanged for every profile: Metadata block,
      `## 摘要限制` heading, `Summary mode: semantic-llm`, `## Chunk Summaries`
- [ ] All four downstream readers stay green: `semantic_review_artifact`,
      `stock_lens_synthesis`, `corpus_index`, `verified_research_lineage`
- [ ] Registry stays at exactly 22 tools; `tests/test_mcp_tool_registry_contract.py`
      passes **without modification**
- [ ] No new summary path, no new artifact family, no new file on disk
- [ ] `semantic_summarize_episode` and `summarize_episode` signature pins at
      `tests/test_contracts.py:22` and `:30` stay green **without modification**
- [ ] No new runtime dependency in `pyproject.toml`

## Failing loudly

- [ ] An unknown `summary_profile` is refused at profile load — before any
      transcript read or LLM call, so a config typo costs nothing
- [ ] A non-string `summary_profile` (e.g. `123`) does not silently resolve to
      `finance` via `_optional_text`
- [ ] The refusal message names both the invalid value and the known values
