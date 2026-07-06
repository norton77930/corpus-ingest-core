# Feature Specification: LLM Safety Synthesis Smoke Review

**Feature Branch**: `006-llm-safety-synthesis-smoke-review`
**Created**: 2026-06-30
**Status: Backfilled / As-built**

**Input**: Existing implemented behavior for semantic summaries, OpenAI-compatible
provider calls, LLM profiles, local `.env` loading, stock lens synthesis, raw
debug output, LLM smoke CLI, safety eval docs, and deterministic smoke review.

## Spec Kit workflow record

- `$speckit-constitution`: reviewed Phase 7C constitution, no amendment.
- `$speckit-specify`: this file records as-built LLM safety requirements.
- `$speckit-clarify`: no high-impact ambiguity; current code/tests/docs are source of truth.
- `$speckit-plan`: design artifacts are captured in this package.
- `$speckit-checklist`: requirements quality checklist is in `checklists/requirements.md`.
- `$speckit-tasks`: retrospective trace tasks are in `tasks.md`.
- `$speckit-analyze`: checked consistency across spec, plan, and tasks.
- `$speckit-implement`: docs/spec/tests only; no runtime change.
- `$speckit-converge`: package covers the current LLM safety and review scope.

## User Scenarios & Testing

### User Story 1 - Run optional semantic summary safely (Priority: P1)

Users can opt into semantic summary only after exact acknowledgement of external
LLM, transcript transfer, and cost risk.

**Independent Test**: `test_semantic_summarizer.py`.

### User Story 2 - Generate stock lens synthesis safely (Priority: P2)

Users can generate LLM-assisted synthesis from Phase 6F stock lens JSON only,
with post-output guard and no raw transcript input.

**Independent Test**: `test_stock_lens_synthesis.py`.

### User Story 3 - Smoke test and review LLM output (Priority: P3)

Users can run OpenAI-compatible smoke validation and then generate deterministic
review reports without another LLM call.

**Independent Test**: `test_research_llm_smoke.py` and
`test_research_llm_smoke_review.py`.

## Functional Requirements

- **FR-001**: LLM calls MUST require exact `api_cost_ack` before provider construction.
- **FR-002**: Stock lens synthesis MUST use `phase-6f-stock-lens-json-only` by default and MUST NOT read raw transcript.
- **FR-003**: Provider config MUST not expose `.env`, API key, token, or secret values.
- **FR-004**: LLM profiles MUST store provider metadata only, not secret values.
- **FR-005**: Local `.env` loading MUST preserve PowerShell env precedence and avoid printing values.
- **FR-006**: Raw LLM output debug logs MUST be opt-in and outside formal artifacts.
- **FR-007**: Prohibited advice guard MUST reject buy/sell/hold, target price, and guaranteed return output.
- **FR-008**: Smoke review MUST read existing artifacts only and make no LLM call.
- **FR-009**: Phase 6U Semantic Summary Smoke Validation MUST provide `run_semantic_summary_smoke.py` and `review_semantic_summary_smoke.py` for dry-run-first transcript transfer validation.
- **FR-010**: Semantic summary smoke and direct semantic CLI execution MUST require exact `api_cost_ack`, keep no raw transcript stdout, make no MCP tool changes, use no live market API, and provide no investment advice.
- **FR-011**: Phase 6U.1 semantic review guard MUST avoid false positive failures for transcript-derived speaker buy/hold descriptions while still rejecting direct trade advice, target price, and guaranteed return language.
- **FR-012**: Confirmed semantic smoke MUST emit non-secret stderr progress while keeping stdout as JSON.
- **FR-013**: Phase 6V stock lens synthesis MAY include reviewed semantic context only when explicitly enabled; default input remains `phase-6f-stock-lens-json-only`, and enabled input MUST be marked `phase-6f-stock-lens-json-plus-reviewed-semantic-summary`.
- **FR-014**: Phase 6V.1 research LLM smoke review MUST enforce boundary/context consistency: JSON-only artifacts have no semantic context, and reviewed semantic artifacts include non-empty `source_semantic_context` entries with `review_status=passed` and content.

## Safety and Data Boundaries

- Semantic summary may transfer transcript text only after acknowledgement.
- Stock lens synthesis does not read raw transcript. By default it does not read `.semantic.md`; Phase 6V may read only review-passed semantic summary metadata/final summary context when explicitly enabled.
- Phase 6V.1 review gate boundary/context consistency checks do not call an LLM, read `.env`, fetch live market data, change MCP tools, or rewrite historical review reports.
- no live market API is used by this package.
- no investment advice is allowed.
- Review artifacts are eval/review only and do not read `.env`.

## Success Criteria

- **SC-001**: Existing LLM provider, profile, local env, synthesis, smoke, and review tests pass.
- **SC-002**: Missing acknowledgement rejects before writing artifacts.
- **SC-003**: Review gate detects obvious secret, traceback, raw transcript, or prohibited advice leakage.

## Assumptions

- OpenAI-compatible provider behavior is optional and user-configured.
- GB10 smoke is a manual provider validation path, not a direct Codex-session backend.
