# Requirements Checklist: Semantic Summary Profiles

Unchecked — v1 is not implemented. One box per FR in `spec.md`.

## The profile registry

- [ ] FR-001 `summary_profiles.py` holds the profiles as pure data (chunk system,
      chunk sections, chunk constraints, final system, final sections, final
      constraints, 摘要限制 body); imports nothing beyond the standard library
      and `.errors`
- [ ] FR-002 Exactly two profiles in v1: `finance` and `learning-notes`;
      `finance` reproduces the current prompt strings exactly
- [ ] FR-003 Lookup raises a named configuration error for an unknown profile,
      listing the known values; never falls back silently

## Selection

- [ ] FR-004 `PodcastProfile.summary_profile` defaults to `"finance"`
- [ ] FR-005 Every existing profile lacking the key parses and behaves identically
- [ ] FR-006 `load_podcast_profile` rejects an unknown value at load time, before
      any transcript read, provider construction, or `api_cost_ack` evaluation

## Threading

- [ ] FR-007 `create_provider` accepts the profile keyword-only with a `finance`
      default; `require_exact_api_cost_ack` remains its first statement
- [ ] FR-008 `SemanticSummaryProvider.summarize_chunk` / `summarize_final`
      signatures unchanged; all five existing fakes pass **unmodified**
- [ ] FR-009 `semantic_summarize_episode` reads `profile.summary_profile` and
      passes it to `create_provider`; gains no per-run profile argument
- [ ] FR-010 `_chunk_prompt` / `_final_prompt` driven by profile data; the
      finance rendering is string-equal to today's output

## Rendering

- [ ] FR-011 `_render_semantic_markdown` takes the 摘要限制 body from the profile;
      the `## 摘要限制` heading, the Metadata block, `Summary mode: {SUMMARY_MODE}`,
      and `## Chunk Summaries` are unchanged for every profile
- [ ] FR-012 The `learning-notes` limitation text states LLM provenance and
      timestamp traceability, and contains no investment disclaimer

## Shape of the learning-notes profile

- [ ] FR-013 Chunk prompt asks for 主要內容、觀念 / 方法 / 工具 / 名詞 / 人物 /
      產品 / 書籍、可引用片段、不確定事項
- [ ] FR-014 Final prompt asks, in order, for 本片主題與適合誰看、核心觀念、
      可操作步驟與實際用法、常見錯誤 vs 正確用法、值得記住的名詞與工具、
      可直接複用的 prompt 或範例片段、時間軸摘要、可驗證引用、不確定事項
- [ ] FR-015 Both profiles keep timestamp traceability and 不確定事項 as required

## Extractive summary (P2)

- [ ] FR-016 The 待 LLM 深度摘要 Prompt block follows the same profile; the
      finance rendering is byte-identical to today's

## Boundaries

- [ ] FR-017 No new dependency, no MCP tool, no change to summary artifact paths,
      canonical-name rules, or `SUMMARY_MODE`
- [ ] FR-018 `_PROVIDER_FACTORY_TOKEN` remains the only construction path
