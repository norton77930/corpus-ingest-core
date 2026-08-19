# Feature Specification: Semantic Summary Profiles

**Feature Branch**: `037-semantic-summary-profiles`
**Created**: 2026-08-19
**Status**: Draft — specification only. No implementation; `plan.md` and `tasks.md` are not yet written.

**Input**: Spec 036 made an X video a first-class corpus source, and the semantic summariser ran on it with no source-specific branching — which was the point, and which is also exactly the problem. The prompts are finance-shaped and hardcoded. An AI-teaching talk by an Anthropic engineer is currently summarised under the headings 市場觀點 / 台股觀點 / 美股觀點 / 總經觀點 / 廣告 / 業配段落, and the rendered Markdown asserts 本摘要不構成投資建議 over content that never mentions a security. The corpus can now ingest what the user actually learns from, but it still reports on it as if it were 股癌. Meanwhile a hand-written target shape already exists: the prototype's `output/03_full_summary.md`, `04_learning_notes.md`, and `07_final_study_guide.md` are the user's own design for AI-learning output, and Spec 036's Assumption 6 recorded them as target rather than as something to redesign.

## Clarifications

### Session 2026-08-19

- Q: What selects the shape — `source_type`, or a new field? → A: **A new `summary_profile` field on `PodcastProfile`.** `source_type` answers "where did this come from"; the summary shape answers "what is this content". Binding them would force a future X finance account onto learning notes and a future YouTube AI channel onto market commentary. Default `"finance"`, so every existing profile is unchanged.
- Q: Where does the finance shape actually live? → A: **Four hardcoded sites, all in one file.** `llm_provider.py:110` (chunk system message), `llm_provider.py:133` (final system message), `llm_provider.py:215` (chunk user prompt: 股票 / 產業), `llm_provider.py:235` (final user prompt: 市場觀點 / 台股觀點 / 美股觀點 / 總經觀點 / 廣告 / 業配段落). A fifth is the rendered disclaimer at `semantic_summarizer.py:439`. Nothing else in the semantic path is finance-shaped.
- Q: Can the rendered Markdown structure change per profile? → A: **No — the envelope is a downstream contract.** `semantic_review_artifact.py:143` checks the literal string `## Chunk Summaries`; `:151` checks `Summary mode: semantic-llm`, `Provider:`, `Model:`, `Transcript status:`; `stock_lens_synthesis.py:494` splits on `^##\s+Chunk Summaries\s*$` to isolate the final summary; `verified_research_lineage.py:820` rejects any `summary_mode` other than `semantic-llm`. The profile changes **what the LLM is asked to produce**, never the Metadata block, the `## Chunk Summaries` heading, or `SUMMARY_MODE`.
- Q: Is removing 本摘要不構成投資建議 safe for the review gate? → A: **Yes, and this is the one claim worth proving by test.** `report_safety.matched_investment_advice_guard` (`report_safety.py:125-141`) is a *prohibition detector*, not a disclaimer requirement: it calls `strip_safety_disclaimers` first and then searches `_PERSONALIZED_INVESTMENT_ADVICE_PATTERNS`. A summary containing no advice returns `None` → `prohibited_advice=pass`, whether or not a disclaimer is present. The `_SAFETY_DISCLAIMER_PATTERNS` tuple exists to stop a disclaimer from false-positiving, not to mandate one.
- Q: Which seam carries the profile to the prompts — change the provider protocol, or pass the profile into the factory? → A: **Into `create_provider`.** `SemanticSummaryProvider.summarize_chunk` / `summarize_final` are faked in five places (`tests/test_semantic_summarizer.py:71`, `tests/test_corpus_semantic_remediation_runner.py:979`, `tests/test_spec_018_closure.py:146` and `:405`). Adding a parameter to the protocol breaks all of them for no gain. Building the messages in `semantic_summarizer.py` and calling `provider.complete()` breaks them harder, because the fakes intercept at the `summarize_*` level. Passing the resolved profile into the factory leaves the protocol byte-identical.
- Q: Do the prompt strings belong in `llm_provider.py`? → A: **No — a new pure-data module.** `llm_provider.py` is transport (HTTP, auth, timeouts, the `api_cost_ack` gate). It holds the prompt text today only by accident. Moving the text into a data module with no imports beyond the standard library and the repo's own errors module makes the registry testable without constructing a provider, and keeps the transport module free of domain vocabulary.
- Q: Is the extractive summariser in scope? → A: **Yes, at P2.** `summarizer.py:255-268` renders a fixed 待 LLM 深度摘要 Prompt block listing 市場觀點 / 提到的公司 / 股票 / 產業 / 總經觀點 / 廣告段落. Leaving it means an AI-teaching episode's extractive summary carries a visibly wrong instruction block. It reads the same `summary_profile` field. It is P2 because the semantic path is what the operator actually consumes.
- Q: Does this spec build the prototype's 00–07 multi-document sequence? → A: **No.** Spec 036 put "a new artifact family for the study-guide document sequence" out of scope, and that stands. This spec reshapes the **existing single semantic summary**, borrowing the section vocabulary of `04_learning_notes.md` and `07_final_study_guide.md` compressed into one document. The multi-document sequence needs a new artifact family, new `corpus_index` families, and new canonical-path rules — a spec of its own.
- Q: What happens to an unknown `summary_profile` value? → A: **Refuse at profile load, naming the known values.** This mirrors what Spec 036 learned the hard way: its X surface accepted a typo'd `source_type` that the RSS surfaces refused, and the architecture review caught it as an in-scope contradiction. A discriminant that is not enforced is a defect, not a convenience.

## User Scenarios & Testing

### User Story 1 — An AI-teaching Episode Is Summarised as Learning Notes (Priority: P1)

The operator runs the existing semantic summariser on an X episode and receives a study-shaped document — concepts, why each matters, how the speaker put it, how to apply it, wrong-versus-right usage, reusable snippets — instead of market commentary about content that contains no market.

**Why this priority**: This is the feature. Spec 036 delivered the pipeline; this delivers the output the pipeline exists to produce.

**Independent Test**: With `x-raytar` carrying `summary_profile: learning-notes`, `semantic_summarize_episode("x-raytar", "2071290493581840707", force=True)` produces a summary whose final section carries the learning-notes headings and contains none of 市場觀點 / 台股 / 美股 / 總經 / 業配.

**Acceptance Scenarios**:

1. **Given** a profile with `summary_profile: learning-notes`, **When** the semantic summariser runs, **Then** the chunk and final prompts sent to the provider are the learning-notes prompts, verified by capturing the messages at a fake provider.
2. **Given** the same run, **When** the Markdown is rendered, **Then** the 摘要限制 section carries the learning-notes limitation text and does **not** carry 本摘要不構成投資建議。
3. **Given** the produced summary, **When** `semantic_review_artifact` evaluates it, **Then** `prohibited_advice=pass`, `chunk_summaries=pass`, `metadata=pass`, and `timestamp_evidence=pass`.
4. **Given** the produced summary, **When** `generate_corpus_index` runs, **Then** the `semantic_summary` family is available exactly as before, because neither the path nor the canonical-name rule changed.

### User Story 2 — Every Existing Profile Is Byte-for-byte Unchanged (Priority: P1)

`gooaye` has no `summary_profile` key, receives the `finance` default, and produces the same prompts and the same rendered Markdown as before this change.

**Why this priority**: The repo's whole regression posture is "an existing episode's artifact is unchanged". A summary-shape change that silently altered 股癌's output would be a data-corruption event across every already-generated summary, and the verified-research-report chain reads those summaries.

**Acceptance Scenarios**:

1. **Given** a profile with no `summary_profile` key, **When** it is loaded, **Then** it parses and `summary_profile == "finance"`.
2. **Given** the `finance` profile, **When** the chunk and final prompts are built, **Then** they are string-equal to the current hardcoded prompts, asserted against literals written into the test rather than against the implementation.
3. **Given** an existing gooaye episode, **When** the semantic summariser runs against a fake provider returning fixed text, **Then** the rendered Markdown is byte-identical to the pre-change rendering, including 本摘要不構成投資建議。
4. **Given** `tests/test_semantic_summarizer.py:209`, which asserts the investment disclaimer, **Then** it still passes unmodified.

### User Story 3 — The Discriminant Is Enforced, Not Decorative (Priority: P2)

A profile naming a summary profile that does not exist is refused at load, with a message listing the known values.

**Why this priority**: Spec 036's `code-reviewer` and `architecture-reviewer` both flagged an unenforced discriminant as a real defect. Repeating it knowingly would be worse than the first time.

**Acceptance Scenarios**:

1. **Given** a profile with `summary_profile: leraning-notes` (typo), **When** it is loaded, **Then** it raises with a message naming both the invalid value and the known values.
2. **Given** an unknown value, **Then** it is refused at profile load — before any transcript read and before provider construction. It is refused *after* the exact `api_cost_ack` check, not before: the ack is the safety boundary and must never be masked or preceded by a config error. The guarantee that matters is that a config typo never costs an LLM call, and an ack comparison is a string comparison.

### User Story 4 — The Extractive Summary Stops Prescribing Market Commentary (Priority: P2)

The deterministic extractive summary's 待 LLM 深度摘要 Prompt block follows the same `summary_profile`.

**Acceptance Scenarios**:

1. **Given** `summary_profile: learning-notes`, **When** `summarize_episode_extractive` runs, **Then** the prompt block lists the learning-notes sections.
2. **Given** the `finance` default, **Then** the rendered extractive Markdown is byte-identical to today's.

## Safety and Data Boundaries

- **The rendered envelope is frozen.** The Metadata block keys, `SUMMARY_MODE = "semantic-llm"`, the `## Chunk Summaries` heading, and the `## 摘要限制` heading itself are downstream contracts (`semantic_review_artifact.py:143,151`; `stock_lens_synthesis.py:494`; `verified_research_lineage.py:820`). Only the *body text* under 摘要限制 and the *prompt content* vary by profile.
- **The `api_cost_ack` gate is untouched.** `require_exact_api_cost_ack` runs before provider construction in both `semantic_summarize_episode` and `create_provider`. Adding a profile argument to `create_provider` must not move, weaken, or bypass that guard, and must not create a second construction path around `_PROVIDER_FACTORY_TOKEN`.
- **No new dependency, no network change, no new artifact path.** Summaries keep landing at `storage.semantic_summary_asset_path`; canonical-path resolution and the `{episode_ref}__{title_slug}.semantic.md` naming are unchanged.
- **No investment advice, in either profile.** The `finance` profile keeps its disclaimer. The `learning-notes` profile omits it because the content carries no market claim to disclaim — and `prohibited_advice` remains an active check on both, since the detector never depended on the disclaimer.
- **Profile selection is config, not caller input.** The shape follows the source's registered profile. No MCP tool argument, no CLI flag, and no per-run override in v1 — a per-run override would let one episode's summaries disagree with each other at the same canonical path.
- This spec adds no MCP tool. The registry stays at 22 tools; the pinned-count chain running through the Hermes AST projection, the Spec 029 descriptor snapshot, the deny adapter, and the docs-count consistency check is not touched.

## Requirements

**The profile registry**

- **FR-001**: A new module MUST hold the summary profiles as pure data — per profile: the chunk system message, the chunk user-prompt section list and constraint lines, the final system message, the final user-prompt section list and constraint lines, and the 摘要限制 body text. It MUST import nothing beyond the standard library and the repo's own errors module.
- **FR-002**: The registry MUST define exactly two profiles in v1: `finance` and `learning-notes`. `finance` MUST reproduce the current prompt strings exactly.
- **FR-003**: The registry MUST expose a lookup that raises a named configuration error for an unknown profile, listing the known values.

**Selection**

- **FR-004**: `PodcastProfile` MUST gain a `summary_profile: str` field defaulting to `"finance"`.
- **FR-005**: Every existing profile lacking a `summary_profile` key MUST parse and behave exactly as before.
- **FR-006**: `load_podcast_profile` MUST reject an unknown, non-string, or explicitly-null `summary_profile` at load time, before any transcript read and before provider construction. It MUST NOT precede the exact `api_cost_ack` check — see FR-007. An absent key is the only input that resolves to the default.

**Threading**

- **FR-007**: `create_provider` MUST accept the resolved summary profile and MUST default it to `finance`, so existing callers stay source-compatible. The `api_cost_ack` guard MUST remain its first statement.
- **FR-008**: `SemanticSummaryProvider`'s `summarize_chunk` and `summarize_final` signatures MUST NOT change; the five existing test fakes MUST keep working unmodified.
- **FR-009**: `semantic_summarize_episode` MUST read `profile.summary_profile` and pass it to `create_provider`. It MUST NOT gain a per-run profile argument.
- **FR-010**: `_chunk_prompt` and `_final_prompt` MUST be driven by the profile data rather than by literals, and the finance rendering MUST be string-equal to today's output.

**Rendering**

- **FR-011**: `_render_semantic_markdown` MUST take the 摘要限制 body from the profile. The heading `## 摘要限制`, the Metadata block, `Summary mode: {SUMMARY_MODE}`, and the `## Chunk Summaries` heading MUST be unchanged for every profile.
- **FR-012**: The `learning-notes` limitation text MUST state that the summary is LLM-generated from the transcript and that conclusions should be traced back to timestamp evidence. It MUST NOT contain an investment disclaimer.

**Shape of the learning-notes profile**

- **FR-013**: The chunk prompt MUST ask for: 主要內容、提到的觀念 / 方法 / 工具 / 名詞 / 人物 / 產品 / 書籍、可引用片段、不確定事項.
- **FR-014**: The final prompt MUST ask for, in order: 本片主題與適合誰看、核心觀念（每個觀念含「是什麼 / 為什麼重要 / 影片中怎麼說」）、可操作步驟與實際用法、常見錯誤用法 vs 正確用法、值得記住的名詞與工具、可直接複用的 prompt 或範例片段、時間軸摘要、可驗證引用、不確定事項.
- **FR-015**: Both profiles MUST keep the evidence discipline: every claim traceable to a transcript timestamp, and 不確定事項 as a required section. Evidence rules are repo policy, not a finance convention.

**Extractive summary (P2)**

- **FR-016**: `summarizer.py`'s 待 LLM 深度摘要 Prompt block MUST follow the same `summary_profile`, and the `finance` rendering MUST be byte-identical to today's.

**Boundaries**

- **FR-017**: No new runtime dependency, no MCP tool, no change to summary artifact paths or canonical-name rules, and no change to `SUMMARY_MODE`.
- **FR-018**: The `_PROVIDER_FACTORY_TOKEN` direct-construction guard MUST remain the only construction path.

## Success Criteria

- An X episode's semantic summary reads as study material — concepts, why they matter, how to apply them, wrong-versus-right usage — with zero occurrences of 市場觀點 / 台股 / 美股 / 總經 / 業配 in the rendered document.
- The same episode's summary contains no investment disclaimer, and `semantic_review_artifact` still returns `prohibited_advice=pass`, proving the disclaimer was never the gate.
- A gooaye episode's rendered semantic Markdown is byte-identical before and after the change, for the same fake-provider input.
- The `finance` chunk and final prompts are asserted string-equal to the pre-change literals by a test that hardcodes them, so a future edit to the registry cannot silently drift 股癌's output.
- All five existing `SemanticSummaryProvider` fakes pass unmodified, evidencing that the protocol did not change.
- A profile with an unknown `summary_profile` is refused at load, and the refusal happens before any provider construction or `api_cost_ack` evaluation.
- `generate_corpus_index` reports the `semantic_summary` family for the X episode exactly as it did after Spec 036.
- Full repository regression shows no new failure outside the pre-existing blocked chain (24 failed / 1584 passed as of 2026-08-19).

## Assumptions

1. **The envelope really is the contract.** Verified by grep across `src/`, `tests/`, `scripts/`, and `docs/`: the only structural readers of the semantic Markdown are `semantic_review_artifact` (two literal checks), `stock_lens_synthesis:494` (one regex split), `corpus_index` (existence and readability only — it never parses the body), and `verified_research_lineage:820` (`summary_mode`). Nothing reads a finance section heading.
2. **The disclaimer is decorative for the gate.** `matched_investment_advice_guard` strips disclaimers before scanning. Confirmed by reading `report_safety.py:125-141` and the smoke-review tests at `tests/test_semantic_summary_smoke_review.py:362-497`, which feed it disclaimer-plus-advice strings precisely to prove the strip is not an escape hatch.
3. **The five fakes are the real compatibility surface.** They are why the factory seam beats the protocol seam. Listed with file and line in the Clarifications.
4. **`stock_lens_synthesis` would read a learning-notes summary as its "final summary" half if ever pointed at one.** It splits on `## Chunk Summaries` without checking the profile. This is not a defect introduced here — the stock lens is only ever invoked for finance episodes — but it is a latent cross-profile assumption and belongs in the follow-up list, not in this scope.
5. **The prototype's section vocabulary is the user's design, not a proposal.** `04_learning_notes.md` uses 這個觀念是什麼？/ 為什麼重要？/ 影片中怎麼說？/ 實際開發時怎麼用？/ 錯誤用法 / 正確用法, and `07_final_study_guide.md` adds 30 秒版本總結 / 3 分鐘版本總結. FR-014 compresses that into one document rather than reinterpreting it.
6. **A one-document summary cannot carry the whole 00–07 sequence.** `05_prompt_examples.md` and `06_apply_to_my_workflow.md` are workflow-specific derivations, not summarisation of the transcript; forcing them into the semantic summary would make the LLM invent content the transcript does not contain, which the repo's evidence rule forbids. They are the reason a multi-document spec is a separate spec.
7. **Existing summaries on disk are not regenerated.** `summary_path.exists() and not force` short-circuits. An operator who wants the new shape for an already-summarised episode passes `force=True` and pays for the call. No migration, no backfill.
8. **Cost is unchanged in shape.** Same chunking, same number of calls, same model; prompt length differs by a few dozen tokens per call.

## Out of Scope (v1)

- **The multi-document study-guide sequence** (`00_*.md` .. `07_*.md`). It needs a new artifact family, new `corpus_index` families, and new canonical-path rules — a spec of its own, and the natural successor if the single-document shape proves insufficient.
- **A third profile.** No `news`, no `interview`, no `technical-deep-dive` until a real source needs one. Two profiles are what it takes to prove the seam is a seam and not a rename.
- **A per-run or per-episode profile override** (CLI flag, MCP argument, or `semantic_summarize_episode` parameter). One canonical summary path, one shape.
- **Translating the summary.** The corpus stores source-language transcripts; the summary language stays as it is today.
- **Making `stock_lens_synthesis` profile-aware.** Recorded as Assumption 4; it is a follow-up.
- **The `source_type` → index → plan → runner propagation seam** left open by Spec 036 (`specs/036-x-video-corpus-ingestion/tasks.md:404-411`). It is real, and it is the next *source* spec's job, not this one's. This spec touches no runner.
- **Retro-fitting the profile onto the deterministic research, entity-extraction, industry-mapping, or episode-intelligence modules.** They read only `profile.display_name` and are finance-purpose by design.
