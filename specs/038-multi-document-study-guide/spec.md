# Feature Specification: Multi-Document Study Guide

**Feature Branch**: `038-multi-document-study-guide`
**Created**: 2026-08-19
**Status**: Implemented. Reviews addressed the dry-run/confirm reuse lie; MCP still 22.

**Input**: Spec 036 treated the prototype sequence `00_video_info.md` … `07_final_study_guide.md` as the user's design, not something to redesign. Spec 037 compressed `04` and `07` vocabulary into the existing single semantic summary and left the multi-document sequence out of scope. The real `learning-notes` run already showed why eight files cannot be one summarisation family: reusable-prompt examples were reconstructed from spoken description, and `05` / `06` are workflow derivations. This spec adds a new study-guide bundle — `00` + `03` + `04` + `07` only — generated from an existing `learning-notes` semantic summary.

## Clarifications

### Session 2026-08-19

- Q: Which of the eight prototype files are in v1? → A: **`00`, `03`, `04`, and `07` only.** `01` is already the transcript trio. `02` is translation and stays out. `05` and `06` are workflow derivations, not transcript summaries; treating them as the same family produces fabricated content. A future derivation family would need its own spec and operator-supplied workflow context.
- Q: Does this send the transcript to an LLM again? → A: **No.** The runner reads the existing canonical `learning-notes` semantic summary (plus local seed/audio metadata for `00`). Constitution Principle IV stays unamended: semantic summary remains the only path that may send transcript text to an LLM. Missing summary fails closed; the runner does not chain 015 or regenerate the summary.
- Q: One corpus family or four? → A: **One family, `study_guide`, four canonical files.** The family is available only when all four files exist and are readable. A partial set is `partial`, not available. Indexing four independent families would let a cover sheet look like a finished lecture.
- Q: Must semantic review have `passed`? → A: **No, not in v1.** The gate is a readable canonical `learning-notes` semantic summary on a profile whose `summary_profile` is `learning-notes`. Requiring review `passed` would chain 015 report paths. Unreviewed input is allowed; invented content is still forbidden.
- Q: What may `00` contain? → A: **Only facts already on the local seed and audio asset.** Title, identifiers, published time, duration, source selector, and audio file size/presence. It must not re-probe a source video, call a network, or invent codec/stream fields the seed does not have.
- Q: MCP tool? → A: **No.** Core plus a thin CLI. Registry stays at exactly 22. Exposure waits for a successor, on the 004 → 035 and 036 precedents.

## User Scenarios & Testing

### User Story 1 — An Operator Gets the Reading Sequence (Priority: P1)

The operator has a `learning-notes` episode whose semantic summary already exists. They ask for the study-guide bundle and receive four documents that match the prototype reading order: a cover sheet, a full summary, per-concept notes, and a final study guide.

**Why this priority**: This is the feature. Spec 037 proved the single-document shape; this delivers the sequence the user actually designed.

**Independent Test**: For `x-raytar` / `2071290493581840707` with an existing learning-notes semantic summary, one confirmed run writes four readable files whose section headings match `03` / `04` / `07` below, and a deterministic `00` that only repeats seed/audio facts.

**Acceptance Scenarios**:

1. **Given** a `learning-notes` profile and a readable canonical semantic summary, **When** the operator confirms the run, **Then** the four bundle files exist at the canonical paths and the `study_guide` family is `available`.
2. **Given** that same run, **When** `03` is read, **Then** it contains 影片主題, 核心觀念, 影片結構, 一句話總結, and 適合誰看, and does not contain 市場觀點 / 台股 / 美股 / 總經 / 業配.
3. **Given** that same run, **When** `04` is read, **Then** each concept uses 這個觀念是什麼 / 為什麼重要 / 影片中怎麼說 / 實際開發時怎麼用 / 錯誤用法 / 正確用法.
4. **Given** that same run, **When** `07` is read, **Then** it contains 背景知識, 核心重點, 白話說明, 常見錯誤, 30 秒版本總結, and 3 分鐘版本總結.
5. **Given** the produced `00`, **When** it is compared to the seed and audio asset, **Then** every factual claim in `00` is present on those local artifacts; no codec or stream field appears unless the seed already recorded it.

---

### User Story 2 — Dry-Run Tells the Truth and Writes Nothing (Priority: P1)

The default call plans the four writes, names the source summary it would read, and writes nothing. It does not call an LLM.

**Why this priority**: Principle III. Spec 036 shipped a plan that claimed a write it would not perform; that class of lie is forbidden here.

**Independent Test**: `confirm=false` against a fixture episode returns planned read/write paths and performs zero filesystem writes and zero provider calls.

**Acceptance Scenarios**:

1. **Given** a ready episode, **When** dry-run runs, **Then** the plan lists the source summary path, the four planned write paths, and that cache will not be rebuilt.
2. **Given** a ready episode whose four files already exist and would be reused, **When** dry-run runs, **Then** the plan says reuse, not write.
3. **Given** any dry-run, **When** the tree is compared before and after, **Then** it is identical, including no `.part` files.
4. **Given** dry-run, **When** stdout is inspected, **Then** it is metadata-only JSON: no summary body, no prompt, no secret, no transcript.

---

### User Story 3 — The Wrong Profile and the Missing Summary Fail Closed (Priority: P1)

A finance episode, an unknown episode, or a learning-notes episode with no semantic summary is refused before any LLM work and before any write.

**Why this priority**: gooaye's artifacts are a pinned fixed point. A study-guide path that accepted finance input would either invent learning notes from market commentary or send the wrong document class into a learning-shaped prompt.

**Independent Test**: Three fixture cases — finance profile, missing summary, missing profile — each raise a named error, write zero files, and make zero provider calls.

**Acceptance Scenarios**:

1. **Given** a profile whose `summary_profile` is `finance` (including gooaye's default), **When** the runner is invoked, **Then** it refuses, naming `learning-notes` as the required profile, and writes nothing.
2. **Given** a `learning-notes` profile with no canonical semantic summary, **When** the runner is invoked, **Then** it refuses with a missing-source error and does not call 015, download, or transcribe.
3. **Given** a typo'd `podcast_id` or `episode_ref`, **When** the runner is invoked, **Then** it refuses at the existing identity validators.

---

### User Story 4 — Evidence Stays Bound to the Source Summary (Priority: P2)

Claims in `03` / `04` / `07` that assert what the speaker said carry timestamps that already appear in the source semantic summary. Content the summary does not support is listed under 不確定事項, not written as fact. The runner never invents Claude Code / Codex / Copilot / Skill / CLAUDE.md workflow advice (`06` material) or a catalogue of daily engineering prompts that the summary did not already reconstruct (`05` material).

**Why this priority**: This is the fabrication trap. The single-document run already admitted that reusable prompts were reconstructed; a multi-document runner that "completes" `05` / `06` would undo that honesty.

**Independent Test**: A fixture summary that lacks any reusable-prompt section produces a `07` whose prompt-template section is either absent or explicitly under 不確定事項, and contains none of Claude Code / Codex / Copilot / CLAUDE.md / Skill as operator-workflow advice.

**Acceptance Scenarios**:

1. **Given** a source summary whose 不確定事項 says reusable prompts were reconstructed, **When** the bundle is produced, **Then** `03` / `04` / `07` preserve that uncertainty rather than promoting the reconstruction to verbatim quotation.
2. **Given** a source summary with no mention of the operator's coding tools, **When** the bundle is produced, **Then** none of `03` / `04` / `07` instruct the reader how to apply the talk to Claude Code, Codex, Copilot, CLAUDE.md, or a Skill.
3. **Given** any produced bundle, **When** `prohibited_advice` is evaluated on `03` / `04` / `07`, **Then** each returns pass.

---

### Edge Cases

- Already-complete bundle and `force=false`: reuse all four files, no LLM call, report reused.
- Partial bundle (some of the four files present): not treated as available; confirmed run with `force=false` refuses or replaces the whole bundle atomically — it must not leave a mixed old/new set.
- Source summary exists but is unreadable or larger than the existing semantic-summary read cap: refuse, write nothing.
- Source summary is finance-shaped (has 市場觀點) even if the profile claims `learning-notes`: refuse. The profile and the document class must agree.
- Confirmed run without exact `api_cost_ack`: refuse before provider construction and before any write.
- Dry-run must not evaluate `api_cost_ack` as a reason to fail a ready plan: ack is required only for confirmed LLM work.
- Operator repeats a confirmed run against the same episode: no duplicate identity; second run reuses unless `force=true`.
- gooaye corpus index and gooaye search results are unchanged across a successful `x-raytar` bundle write.

### Safety and Data Boundaries

- **Input boundary**: the canonical `learning-notes` semantic summary plus local seed and audio metadata. Not the transcript, not RSS, not a live URL, not `.env` values in any output.
- **LLM opt-in**: confirmed generation of `03` / `04` / `07` requires exact `api_cost_ack` before provider construction. `00` is deterministic and does not itself justify an LLM call; if `03`/`04`/`07` already exist and will be reused, no LLM call occurs.
- **Dry-run first**: default is `confirm=false`; zero writes, zero provider calls. The plan must describe the action that confirmed mode would actually take (write vs reuse).
- **No transcript egress**: this feature must not send transcript text to an LLM. Principle IV is unchanged.
- **Secret boundary**: `.env`, API keys, tokens, and provider secrets are not read for documentation, not printed, not written to artifacts, and not returned in CLI JSON.
- **No investment advice**: `prohibited_advice` remains an active check on generated Markdown. No buy/sell/hold, target price, guaranteed return, or personalized recommendation.
- **No live market API.** External status is not involved.
- **Manual cache rebuild**: the run does not rebuild SQLite cache; the response warns that cache may be stale.
- **No MCP tool.** Registry remains exactly 22 reviewed tools.
- **Finance / gooaye isolation**: this runner refuses non-`learning-notes` profiles. It does not change semantic-summary paths, the frozen envelope, or finance prompts.

## Requirements

### Functional Requirements

**Taxonomy**

- **FR-001**: v1 MUST produce exactly four documents per episode: cover (`00`), full summary (`03`), learning notes (`04`), and final study guide (`07`).
- **FR-002**: v1 MUST NOT produce, index, or accept as in-family the prototype files `01`, `02`, `05`, or `06`.
- **FR-003**: `05` / `06` content (operator-workflow application, catalogues of daily engineering prompts not present in the source summary) MUST NOT appear in `03`, `04`, or `07` as if it were lecture evidence.

**Source and profile**

- **FR-004**: The runner MUST require `summary_profile == learning-notes` and MUST refuse any other value, naming the required profile.
- **FR-005**: The runner MUST read the existing canonical semantic summary for that episode and MUST refuse when it is missing, unreadable, or not learning-notes-shaped. It MUST NOT generate, regenerate, or request a semantic summary.
- **FR-006**: The runner MUST NOT read the transcript file or send transcript text to a provider.
- **FR-007**: Semantic review `passed` is NOT a v1 precondition.

**Cover (`00`)**

- **FR-008**: `00` MUST be assembled deterministically from the local episode seed and audio asset metadata only.
- **FR-009**: `00` MUST NOT call a network, MUST NOT probe a source video, and MUST NOT invent stream/codec fields absent from those local artifacts.

**Generated lecture files**

- **FR-010**: `03` MUST use this section set, in order: 影片主題, 核心觀念, 影片結構, 一句話總結, 適合誰看, 不確定事項.
- **FR-011**: `04` MUST present each concept with 這個觀念是什麼, 為什麼重要, 影片中怎麼說, 實際開發時怎麼用, 錯誤用法, 正確用法, and a bundle-level 不確定事項.
- **FR-012**: `07` MUST include 背景知識, 核心重點, 白話說明, 常見錯誤, 30 秒版本總結, 3 分鐘版本總結, and 不確定事項. A reusable-prompt section MAY appear only when the source summary already contains one, and MUST keep that section's reconstruction/uncertainty labelling.
- **FR-013**: Every speaker-attributed claim in `03` / `04` / `07` MUST carry a timestamp that already appears in the source semantic summary. Claims the source does not support MUST go under 不確定事項. The runner MUST NOT add external corrections (model version numbers, product facts, tool schemas) that the source summary did not already record.

**Family, paths, and index**

- **FR-014**: Canonical paths MUST come from `storage`, never hand-composed. Filename identity MUST reuse the existing episode-ref + title-slug rule so a third title provenance is not introduced.
- **FR-015**: `corpus_index` MUST gain exactly one new family, `study_guide`. Status is `available` only when all four canonical files exist and are readable; otherwise `missing` or `partial`.
- **FR-016**: A confirmed write of the bundle MUST be atomic across the four files: success leaves all four new (or all four reused); failure leaves the previous complete set or nothing, never a mixed generation.

**Workflow contract**

- **FR-017**: `confirm=false` MUST return a truthful action plan (planned reads, planned writes or reuses, step order, ack requirement, cache warning) and MUST perform zero writes and zero provider calls.
- **FR-018**: Confirmed generation of `03` / `04` / `07` MUST require exact `api_cost_ack` as the first gate, before provider construction. The `_PROVIDER_FACTORY_TOKEN` construction path MUST remain the only provider construction path. `SemanticSummaryProvider.summarize_chunk` / `summarize_final` signatures MUST NOT change.
- **FR-019**: CLI stdout/stderr MUST be metadata-only. No summary body, no prompt, no transcript, no secret values.
- **FR-020**: The run MUST NOT rebuild the SQLite cache and MUST warn that cache may be stale.
- **FR-021**: v1 MUST add no MCP tool, no new runtime dependency, and no change to the semantic-summary envelope (`## Chunk Summaries`, Metadata block, `SUMMARY_MODE`).
- **FR-022**: A finance-profile episode's existing artifacts MUST remain byte-identical; generating a study-guide bundle for a `learning-notes` episode MUST NOT modify any other `podcast_id`.

### Key Entities

- **Study-guide bundle**: one episode's four canonical Markdown files, one corpus family.
- **Cover document (`00`)**: deterministic local metadata sheet.
- **Full summary (`03`)**: evidence-bound lecture summary derived from the semantic summary.
- **Learning notes (`04`)**: per-concept notes derived from the semantic summary.
- **Final study guide (`07`)**: compressed recap derived from the semantic summary.
- **Source semantic summary**: the existing canonical `.semantic.md` for a `learning-notes` episode; the only LLM-origin input.
- **Run report**: metadata-only record of dry-run or confirmed execution, including reuse vs write and the cache warning.

## Success Criteria

- An operator with an existing learning-notes semantic summary can obtain the four-document reading sequence without hand-editing files and without sending the transcript to an LLM again.
- The four files are either all present and readable (family available) or the family is not reported available. A cover sheet alone never counts as a finished lecture.
- `05` / `06` material is absent from the produced files unless it already appears, labelled uncertain, in the source summary.
- A finance / gooaye episode is refused; its on-disk artifacts are unchanged.
- Dry-run writes zero files and calls no provider, and a dry-run plan that would reuse existing files says reuse.
- Confirmed execution without exact acknowledgement does not construct a provider and does not write.
- Full repository regression shows no new failure outside the pre-existing blocked Hermes chain (24 failed / 1628 passed as of 2026-08-19).
- The reviewed MCP registry remains exactly 22 tools.

## Assumptions

1. The prototype sequence is the user's design. v1 realises the evidence-bound subset (`00`/`03`/`04`/`07`), not a redesign of those four, and not a completion of the eight.
2. Spec 037's single semantic summary remains the source of truth for what the model already extracted. This spec reshapes and splits that evidence; it does not re-transcribe or re-summarise the audio.
3. One LLM pass that emits a structured three-document body (plus deterministic `00`) is in scope; three independent LLM calls are not required. Cost shape is smaller than a second transcript-chunking pass.
4. `stock_lens_synthesis` and verified-research lineage continue to read only the semantic summary. The new bundle is not a lineage input in v1.
5. Existing summaries and existing bundles are not migrated. `force=true` is how an operator replaces a bundle.
6. Translation (`02`) and grouped-transcript persistence (`01`) remain out of scope, matching Spec 036 (groups are computed on demand) and Spec 037 (no translation).
7. Principle IV's sentence that semantic summary is the only transcript-to-LLM path remains true after this spec. No constitution amendment.

## Out of Scope (v1)

- Prototype files `01`, `02`, `05`, `06`, and any "apply to my workflow" derivation family.
- Sending transcript text to an LLM, or amending Principle IV.
- Regenerating or reviewing the semantic summary (015 / 018 chaining).
- Requiring semantic review `passed`.
- MCP exposure.
- A third summary profile, a per-run profile override, or YouTube / `source_type` index→plan→runner propagation.
- Making `stock_lens_synthesis` or verified-research lineage consume the new bundle.
- Persisting 30–90s transcript groups.
- Automatic cache rebuild, live market API, investment advice, Hermes work, and the `gb10` profile cleanup.
