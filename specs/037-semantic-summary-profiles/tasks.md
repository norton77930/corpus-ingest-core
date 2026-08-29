# Tasks: Semantic Summary Profiles

**Feature**: 037-semantic-summary-profiles
**TDD**: RED before GREEN.
**Status**: Implemented, reviewed on both axes, and fully verified including the real end-to-end run (T029). Both reviews passed with nothing at High or Medium and no in-scope contradiction; six findings were fixed and the rest recorded as follow-ups. Final regression 24 failed / 1628 passed against the 24/1584 baseline: identical failure list, +44 new passing tests. All ten Completion Contract claims are PASS-current.

## Completion Contract

| Claim | Evidence |
| --- | --- |
| C1 Spec package + clarify | package + Session 2026-08-19 |
| C2 Registry holds both profiles as pure data | `tests/test_summary_profiles.py` |
| C3 `finance` output is a fixed point | prompts + rendered Markdown byte-equal to hardcoded literals |
| C4 `learning-notes` produces study-shaped output | prompt-capture test + one real run read by eye |
| C5 The protocol did not move | all five existing fakes pass **unmodified** |
| C6 The ack gate is intact and ordered | wrong-ack raises before profile resolution |
| C7 The disclaimer was never the gate | no-disclaimer summary passes `prohibited_advice`; advice-shaped one still fails |
| C8 Envelope frozen; downstream readers green | review / stock-lens / corpus-index / lineage suites |
| C9 Unknown profile fails loudly and early | refused at load, before any transcript read or LLM call |
| C10 Full verify | pytest / compileall against the 24/1584 baseline |

Non-goals (do not do them, even if they look adjacent): the 00-07 multi-document
sequence, a third profile, a per-run override, retrofitting `source_type`
validation, making `stock_lens_synthesis` profile-aware.

## Spec Kit sequence

`constitution -> specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement -> converge`

## Phase 1: Spec Kit

- [x] T001 Constitution: reviewed, no amendment. Principle VI needs an explicit
      argument rather than a silent pass — recorded in `plan.md`.
- [x] T002 Specify (`spec.md`), 18 FR / 4 user stories / 8 success criteria
- [x] T003 Clarify: field-vs-`source_type`, the frozen envelope, disclaimer safety,
      factory-vs-protocol seam, prompts-as-data, extractive scope, unknown values
- [x] T004 Plan + `data-model.md` + two checklists
- [x] T005 Tasks (this file)
- [x] T006 Analyze pass before any implementation — findings below

## Analyze findings (pre-implementation)

Seven, all resolved into the plan or into tasks below. Four were errors in this
package's own first draft; recording them because a plan that quietly self-corrects
teaches nothing.

1. **The plan named two test files that do not exist.** `tests/test_llm_provider.py`
   and `tests/test_config.py` were invented from the module names. The real
   surfaces are `tests/test_llm_provider_factory_boundary.py`,
   `tests/test_llm_ack_guard_contracts.py`, `tests/test_contracts.py`, and
   `tests/test_podcast_profile_source_type.py`. Corrected in `plan.md`.
2. **The plan named a CLI script that does not exist.** There is no
   `scripts/semantic_summarize_episode.py`; the entry point is
   `scripts/summarize_episode.py --mode semantic`. Corrected in `plan.md`.
3. **`create_provider` is not signature-pinned, but `api_cost_ack` is.**
   `tests/test_llm_provider_factory_boundary.py:78` asserts `api_cost_ack` is
   keyword-only with an empty default. A keyword-only `summary_profile` keeps it
   green; a positional parameter would not. Pinned as a constraint in T015.
4. **`semantic_summarize_episode` *is* signature-pinned**
   (`tests/test_contracts.py:30`), as is `summarize_episode` (`:22`). This is
   independent confirmation of FR-009 rather than a problem: the config-driven
   design keeps both pins green without editing them. Had the design taken a
   per-run argument, this pin would have been the first casualty.
5. **`docs/architecture.md:61` already claims ack runs "before profile … resolution".**
   The new summary-profile resolution must therefore also sit after the ack, or
   that sentence becomes false. The plan implied the ordering; it did not connect
   it to the existing documented claim. T015 asserts the order; T023 re-reads the
   sentence rather than assuming it still holds.
6. **`__init__.py:124` already exports `group_segments`**, so the plan's
   conditional "(export the registry lookup if the package exports peers)" is
   resolved: yes, export, matching Spec 036's precedent.
7. **The safety checklist asks for a test with no FR behind it** — "an
   advice-shaped learning-notes summary still fails `prohibited_advice`". This
   needs no new FR: the check reads rendered Markdown and never sees the profile,
   so profile-blindness is true by construction. It still needs T019, because
   "true by construction" is exactly what stops being true after a refactor, and
   this particular invariant is the one carrying Principle VI.

## Phase 2: Implement

### The registry

- [x] T007 RED `tests/test_summary_profiles.py`: `SUMMARY_PROFILES` has exactly
      `{"finance", "learning-notes"}`; `resolve_summary_profile()` returns
      finance; an unknown name raises with the invalid value **and** the known
      values in the message; the module imports no IO, network, or env.
      (Amended post-review: `None` no longer resolves to finance — only an
      absent key does. See Phase 4 fix 1.)
- [x] T008 RED (same file, separate test): every `finance` field equals a
      **hardcoded literal** copied from today's source. Not compared against
      `_chunk_prompt`; the literal is the point.
- [x] T009 RED: `learning-notes` chunk and final section lists match FR-013 and
      FR-014 in content and order; both profiles contain 不確定事項 and a
      timestamp-traceability constraint (FR-015); `learning-notes.limitation_lines`
      contains no investment disclaimer (FR-012).
- [x] T010 GREEN `src/corpus_ingest_core/summary_profiles.py`: frozen dataclass,
      two-entry mapping, `resolve_summary_profile`, error type in `.errors`.
      Imports limited to `dataclasses`, `typing`, and `.errors`.

### Selection

- [x] T011 RED `tests/test_podcast_profile_source_type.py`: a profile without the
      key gets `summary_profile == "finance"`; `summary_profile: learning-notes`
      parses; `summary_profile: leraning-notes` is refused at load with both
      values named; `summary_profile: 123` is **refused, not silently finance**
      (the `_optional_text` trap at `config.py:110-114`).
- [x] T012 GREEN `models.PodcastProfile.summary_profile = "finance"`, appended
      **after** `source_type` so positional construction keeps working;
      `config._parse_profile` validates the resolved value via
      `resolve_summary_profile`.

### Threading

- [x] T013 RED `tests/test_summary_profiles.py` or a provider test: `create_provider`
      accepts `summary_profile` keyword-only with a `finance` default; a wrong
      `api_cost_ack` raises **before** the profile is resolved (pass a wrong ack
      *and* an invalid profile; assert the ack error, not the profile error).
- [x] T014 RED: `_chunk_prompt` / `_final_prompt` built from a profile produce the
      finance strings unchanged, and the learning-notes strings for that profile.
- [x] T015 GREEN `llm_provider.py`: `create_provider` gains keyword-only
      `summary_profile`; `require_exact_api_cost_ack` stays the **first** statement;
      the provider holds the resolved profile; `summarize_chunk` / `summarize_final`
      signatures untouched; `_chunk_prompt` / `_final_prompt` read profile data.

### Rendering

- [x] T016 RED `tests/test_semantic_summarizer.py`: with a `learning-notes` profile
      and a fake provider, the rendered Markdown carries the learning-notes
      limitation body, carries **no** investment disclaimer, and still carries the
      frozen envelope — Metadata block, `Summary mode: semantic-llm`, `## 摘要限制`,
      `## Chunk Summaries`.
- [x] T017 RED: with the finance default and the same fake provider, the rendered
      Markdown is **byte-identical** to a literal expected document written into
      the test. Note the boundary: the `## 摘要限制` heading, its leading blank
      line, and its trailing blank line stay in the renderer; only the two body
      lines come from the profile.
- [x] T018 GREEN `semantic_summarizer.py`: read `profile.summary_profile`, pass it
      to `create_provider`, take the limitation body from the profile. No new
      parameter on `semantic_summarize_episode` (FR-009 — and
      `tests/test_contracts.py:30` will catch a slip).

### The Principle VI invariant

- [x] T019 RED `tests/test_semantic_summary_smoke_review.py`: a learning-notes-shaped
      summary with **no** disclaimer returns `prohibited_advice=pass`; the same
      summary with 立即買進 ACME added returns `prohibited_advice=fail`. Both
      profiles, same check, no escape hatch. Expected to pass on first run — record
      that it did, because a RED that never went red is evidence about the design,
      not a defect in the test.

### Extractive (P2)

- [x] T020 RED `tests/test_summarizer.py`: the 待 LLM 深度摘要 Prompt block follows
      the profile; the finance block — heading, leading blank, body, trailing blank —
      is asserted byte-identical **as a block inside the document**, not as
      whole-document equality. The moved boundary is what that covers.
- [x] T021 GREEN `summarizer.py` reads `extractive_prompt_lines` from the profile.

### Wiring and contracts

- [x] T022 `config/podcasts.yaml`: `x-raytar` gains `summary_profile: learning-notes`;
      `gooaye` gains **nothing**. Update `tests/test_contracts.py:12-31` to assert
      `gooaye.summary_profile == "finance"` and
      `x-raytar.summary_profile == "learning-notes"` — a deliberate contract update
      in the same commit. Export `resolve_summary_profile` and the profile constants
      from `__init__.py`, matching the `group_segments` precedent at `:124`.
- [x] T023 Docs: `docs/architecture.md` (summariser line at `:28`; re-read `:61`'s
      "ack before profile resolution" claim and confirm it still holds),
      `docs/verification-matrix.md` (add `tests/test_summary_profiles.py`),
      `specs/README.md` (037 entry + capability package line).

## Phase 3: Verify

- [x] T024 Targeted: `tests/test_summary_profiles.py`,
      `tests/test_podcast_profile_source_type.py`, `tests/test_semantic_summarizer.py`,
      `tests/test_summarizer.py`
- [x] T025 Unmodified-must-pass: `tests/test_llm_provider_factory_boundary.py`,
      `tests/test_llm_ack_guard_contracts.py`, `tests/test_contracts.py`,
      `tests/test_mcp_tool_registry_contract.py`. If any needs editing beyond
      T022's declared contract update, the change has drifted out of scope.
- [x] T026 Fakes-unmodified evidence: `tests/test_corpus_semantic_remediation_runner.py`,
      `tests/test_spec_018_closure.py`, `tests/test_semantic_summary_smoke_review.py`
- [x] T027 Full regression `python -m pytest -q --tb=no -ra` against the
      **24 failed / 1584 passed** baseline; any new failure outside that list is a
      defect in this change
- [x] T028 `python -m compileall src scripts`
- [x] T029 End-to-end acceptance: one real `--mode semantic --force` run on
      `x-raytar/2071290493581840707`, then `generate_corpus_index` for both
      podcasts. Read the produced summary and judge by eye what no assertion can —
      whether it reads as study material or as market commentary with the nouns
      swapped. A summary that passes every test and still reads like 股癌 means the
      prompt is wrong, not the tests.

## Phase 4: Review (R1)

- [x] T030 `code-reviewer` — error-handling paths (unknown profile, non-string
      value, ack ordering) and the byte-equality regression claim
- [x] T031 `architecture-reviewer` — the additive interface changes
      (`PodcastProfile.summary_profile`, `create_provider`), the factory-versus-
      protocol seam, and whether the frozen envelope is genuinely enforced rather
      than merely documented
- [x] T032 Address findings, re-verify, record outcomes here


## Analyze finding 8 (found during implementation, not before)

**The five protocol fakes were the wrong count for the affected surface.** FR-008's
claim held exactly as written — `summarize_chunk` / `summarize_final` never moved
and all five fakes passed unmodified. But `tests/test_corpus_semantic_remediation_runner.py:987`
stubs **`create_provider` itself** with a signature that pins its exact keyword
list, and the analyze pass enumerated protocol fakes without enumerating factory
stubs. The full regression caught it as `executed` -> `failed`.

Fixed as a deliberate contract update in the same commit: the stub takes
`summary_profile` and now asserts it arrives as `"finance"` for gooaye, so the
edit strengthens the evidence rather than silencing the failure. The other two
`create_provider` monkeypatches (`tests/test_episode_verified_research_report_workflow_runner.py:251-253`)
are `*args, **kwargs` refusal stubs and were unaffected.

The lesson generalises: "which fakes break" is a question about every seam the
change crosses, not about the one seam the design chose to preserve.

## Verification outcomes

| Task | Result |
| --- | --- |
| T024 targeted | 69 passed (`test_summary_profiles` 24, `test_semantic_summarizer`, `test_summarizer`, `test_contracts`) |
| T025 unmodified-must-pass | 32 passed; `test_llm_provider_factory_boundary`, `test_llm_ack_guard_contracts`, `test_mcp_tool_registry_contract` green **without modification** |
| T026 fakes-unmodified | green after finding 8's declared stub update; all five protocol fakes unmodified |
| T027 full regression | **24 failed / 1620 passed** vs the 24/1584 baseline — identical failure list (the pre-existing Hermes blocked chain), +36 new passing tests, zero new failures |
| T028 compileall | clean |
| T019 | **passed on first run, as predicted.** The RED never went red because `matched_investment_advice_guard` is profile-blind by construction. Recorded as evidence about the design, not as a defective test. |

### The gooaye byte-equality claim, actually tested

`generate_corpus_index --podcast gooaye` produced a different hash than the file
already on disk (`de3c7de…` -> `4ffd557…`), which reads exactly like the
regression this spec exists to prevent. It is not. Control experiment: the
changes were stashed, the index regenerated with pre-change code, and the hash
was `4ffd557…` — **identical to the post-change output**. The on-disk file was
simply stale from an earlier session. `x-raytar`'s index hash was unchanged
throughout (`c893539…`).

Reasoning alone would have been enough to dismiss it (`corpus_index` imports
`storage`, `models`, `semantic_review_artifact`, and `semantic_summary_identity`,
never `config`, and never reads a `PodcastProfile`). It was tested anyway,
because "byte-for-byte unchanged" is a claim this package put in its own success
criteria, and a claim defended by argument is not evidence.

## Blocked

- **T029 (resolved).** The first two attempts failed on read timeout at 120 s and
  300 s, and this package recorded that as endpoint unavailability. That
  attribution was wrong, and the evidence to disprove it was already on disk.
  The successful run earlier the same day wrote its own model name into the
  artifact it produced — `Model: PRO4500` — while `.env` still carries
  `MODEL=GB10` from 2026-06-30 and the failing runs passed no `--model`. A
  `GET /v1/models` probe returns `['GB10', 'PRO4500']` instantly, so the host,
  the API, and the credential were all fine; `GB10` simply does not answer
  inference. Its last successful use was 2026-07-01. Re-run with
  `--model PRO4500`: 7 chunks, 49 timestamp evidences, 50,059 bytes.

  The lesson is not about the endpoint. A timeout was attributed to a service
  without checking what the last success had recorded about itself, and the
  artifact format this repo already writes — provider and model in every
  summary's Metadata block — existed precisely to answer that question.

(T030-T032 were pending when this section was first written. A self-review of the
diff ran first and produced four fixes — `__all__` ordering, import ordering in
`summarizer.py`, passing the resolved canonical profile name rather than the raw
config string, and a missing test for the empty-transcript render branch. Both
reviews have since run; see below. Self-review is not recorded as a review.)

## Phase 4 outcome: both review axes passed

**`architecture-reviewer`: sound, nothing would block.** It also corrected an
argument this package had conceded too easily. `plan.md` Design Decision 3 half-
apologised for leaving prompt assembly in a transport module; the review found
`llm_provider.py` now holds strictly *less* domain responsibility than before —
pre-change it owned the finance vocabulary itself, post-change it owns only
structural assembly over opaque profile fields. It also judged the "five fakes"
argument to be a protocol argument in disguise rather than a test-shaped
constraint: the fakes sit at `summarize_chunk`/`summarize_final` because that
*is* the interface, so relocating message-building would be a protocol redesign
of an exposed interface with five consumers and no functional need.

**`code-reviewer`: the declared claim holds, no in-scope contradiction.** It
stated its own verification limit rather than asserting past it — with no git
access it could not diff the registry against HEAD, so it confirmed byte-equality
through three independent witnesses instead. The strongest is one this package
had not thought to use: **artifacts on disk written by the pre-change code**.
`data/summaries/gooaye/EP687__EP687.semantic.md:17-21` matches `limitation_lines`
exactly including the heading/blank-line boundary, and
`data/summaries/gooaye/EP687__EP687.md:160-173` matches `extractive_prompt_lines`
exactly. It named the residual honestly: four fields have no witness older than
this working tree except `data-model.md`'s pre-implementation transcription.

### Fixed in response (six)

1. **Explicit YAML null silently meant finance** (code review, Low; the one
   reachable silent path left, and at the margin of this package's own "an
   unenforced discriminant is a defect" doctrine). `resolve_summary_profile` now
   takes an `UNSET` sentinel: an absent key is the only input that resolves to
   the default, and `summary_profile:` is refused. Tested at both the registry
   and config layers.
2. **`data-model.md` described the opposite of what shipped** — it said
   `_parse_profile` reads via `_optional_text` then validates, and that mechanism
   would *not* have prevented the `123 -> None -> finance` trap it claimed to
   prevent. Rewritten to describe the implemented mechanism and why.
3. **`data-model.md` named a non-existent error type** (`SummaryProfileConfigError`
   versus the shipped `UnknownSummaryProfileError`). Corrected.
4. **`spec.md` FR-006 and User Story 3 claimed refusal precedes `api_cost_ack`
   evaluation**, which the implementation deliberately does not do — the ack is
   the safety boundary and must never be masked by a config error. Both rewritten
   to state the implemented order and the guarantee that actually matters: a
   config typo never costs an LLM call, and an ack check is a string comparison.
5. **Untested factory branch** — `create_provider` with a *correct* ack and an
   unknown profile raises `UnknownSummaryProfileError`, not `LLMProviderConfigError`.
   Unreachable through the real pipeline, but it was the one new branch with no
   test. Now covered, error type documented.
6. **Heading-injection invariant** (architecture review, follow-up; pulled
   forward). Nothing forbade a profile body line from starting with `#`. A
   `## Chunk Summaries` line inside a limitation block would truncate
   `stock_lens_synthesis.py:494`'s `maxsplit=1` split and confuse
   `semantic_review_artifact.py:143`. A registry invariant test now covers every
   profile, converting the freeze from construction-plus-convention to
   construction-plus-invariant. The review suggested doing this when a third
   profile arrives; doing it now costs five lines and removes the dependency on
   remembering.

Also removed: a dead `isinstance(name, bool)` clause (`not isinstance(name, str)`
already rejects bools), and T020's wording, which overstated its assertion as
whole-document equality when it asserts a block inside the document.

### Accepted, not fixed (follow-ups)

- **`stock_lens_synthesis` is profile-blind** and the only thing keeping it off a
  learning-notes summary is operator discipline, not code (`:62` accepts any
  `podcast_id`, never loads a profile). Both reviews raised it independently.
  The architecture review's framing is the one to keep: a load-time
  `summary_profile == finance` gate at the lens entry costs one profile lookup,
  and *stops being optional at five profiles*.
- **The default literal is duplicated** — `models.py:22` hardcodes `"finance"`
  while `summary_profiles.py:21` defines `DEFAULT_SUMMARY_PROFILE`. Two edits if
  it ever changes, and `test_unconfigured_profile_resolves_to_finance` would
  catch only one. Left as-is to keep `models.py` dependency-free.
- **`source_type` load-validation retrofit** — `config.py:87` still accepts any
  string, so two adjacent lines in `_parse_profile` now hold opposite
  philosophies. The asymmetry is principled (`source_type` has a downstream
  enforcement surface in `require_rss_profile`; `summary_profile` has none), and
  the architecture review explicitly said not to reopen for it.
- **Triple resolution round-trip** — `config.py` -> `semantic_summarizer.py:66`
  -> degraded to a string at `:148` -> re-resolved at `llm_provider.py:109`. All
  O(1) dict lookups; the string-typed factory parameter is the price of source
  compatibility. Cosmetic.
- **Whitespace-padded values** (`" finance "`) are accepted and canonicalised.
  Harmless, untested.

### Final verification after the review fixes

`python -m pytest -q --tb=no -ra` -> **24 failed / 1628 passed / 14 skipped**.
Same 24 failures as the 24/1584 baseline (the pre-existing Hermes blocked chain);
+44 new passing tests across the feature. `python -m compileall src scripts`
clean. T029 remains blocked on the unresponsive endpoint and remains unclaimed.
