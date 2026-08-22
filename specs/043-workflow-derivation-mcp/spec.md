# Feature Specification: Workflow Derivation MCP Tool

**Feature Branch**: `043-workflow-derivation-mcp`

**Created**: 2026-08-22

**Status**: Draft — specification only. No implementation yet.

**Input**: Spec 042 shipped the `05`/`06` workflow derivation family with Core and a thin CLI, and closed with "No MCP tool; registry stays at 24". The capability therefore exists but no agent can reach it: an operator has to run `scripts/run_workflow_derivation.py` by hand. This spec appends Tool 25 so the derivation joins the same preview-then-confirm surface every other side-effect tool already uses.

## Clarifications

### Session 2026-08-22

Unlike Specs 040 and 041, this tool is **not** LLM-free, and that changes the envelope:

- `run_workflow_derivation` builds a provider and calls it, so the exact `api_cost_ack` gate applies. It is enforced at Core level in `llm_provider.require_exact_api_cost_ack`; Tool 25 passes the operator's value through and never re-implements or relaxes the check.
- Preview is zero-write **and zero-network**: it plans paths without constructing a provider. Tools 23 and 24 name `network_read=true` because they resolve public video metadata. Tool 25 must not copy that field's value.
- The MCP surface does not expose provider plumbing — `provider`, `model`, `base_url`, `api_key_env`, `reasoning_effort`, `read_timeout_seconds`. Those name credentials and endpoints that belong to the operator's environment, matching Spec 041 FR-011.
- The MCP surface does not expose `workflow_context`. Core accepts a path override, and the file it names is read and folded into an LLM prompt; over MCP that would be a read-any-file-and-send-it primitive. Tool 25 always uses `workflow_derivation.DEFAULT_CONTEXT_PATH` (`config/operator_workflow.yaml`).

## User Scenarios & Testing

### User Story 1 — Preview a derivation (Priority: P1)

An agent names a podcast and episode and receives a plan: the lecture directory it would read, the `05`/`06` paths it would write, anything it would reuse, and the warnings that apply.

**Acceptance Scenarios**:

1. `confirm=false` returns `ok`, `"dry_run": true`, `run_mode=preview`, `not_investment_advice=true`, and creates no files under `data/`.
2. Preview does not require `api_cost_ack`, because it constructs no provider.
3. Preview states `network_read=false`: no provider call, no metadata fetch.
4. An episode whose profile is not `learning-notes` returns a structured error envelope naming the required profile.

### User Story 2 — Confirm once (Priority: P1)

After accepting the plan, confirm writes `05_prompt_examples.md` and `06_apply_to_my_workflow.md` plus a metadata-only run report. Cache is not rebuilt.

**Acceptance Scenarios**:

1. Confirm without the exact `api_cost_ack` fails as a structured envelope before any provider is constructed.
4. Confirming a complete existing pair without `force` reuses it and needs no `api_cost_ack`, because Core
   reads the two files back instead of calling a provider. The tool MUST NOT add an ack requirement that
   Core does not have.
2. Confirm with the exact ack writes the pair and the report, and returns metadata only — no derived body text in the response.
3. A second confirm without `force` reuses rather than rewriting, and says so.

### User Story 3 — Append-only registry (Priority: P1)

Tool 25 appends after unchanged Tools 1–24. Live registry is exactly 25.

## Safety and Data Boundaries

- Preview is zero-write and zero-network.
- The exact `api_cost_ack` gate is Core's; Tool 25 forwards and never weakens it.
- No provider, model, endpoint, or credential parameter on the MCP surface.
- No `workflow_context` override on the MCP surface.
- No `.env` read, no live market API, no investment advice, no automatic cache rebuild.
- Response carries paths and counts, never derived body text or prompts.

## Requirements

- **FR-001**: MCP MUST expose `derive_workflow_bundle(podcast_id, episode_ref, confirm=false, force=false, api_cost_ack="")` as Tool 25.
- **FR-002**: Thin wrapper over `run_workflow_derivation`; no derivation logic in the tool module.
- **FR-003**: Preview envelope uses `tool_action_plan` with `run_mode=preview`, `network_read=false`, `not_investment_advice=true`.
- **FR-004**: Preview MUST write zero files and construct no provider.
- **FR-005**: Confirm MUST forward `api_cost_ack` unchanged and MUST NOT pre-check, transform, or default it.
- **FR-006**: The tool MUST NOT accept `provider`, `model`, `base_url`, `api_key_env`, `reasoning_effort`, `read_timeout_seconds`, or `workflow_context`.
- **FR-007**: Confirm persists a metadata-only JSON+Markdown report via the existing Spec 042 report path.
- **FR-008**: The preview envelope's `risks` name the cache-stale warning and the no-advice
  boundary, and every result carries `not_investment_advice=true`. Core adds the cache-stale
  warning only when the run would actually write, and the tool MUST pass its `warnings`
  through rather than synthesising its own.
- **FR-009**: New group module imported last by the `mcp_server` facade, leaving Tools 1–24 in their slots.
- **FR-010**: Registry, AST projection, deny adapter, and the Spec 029 descriptor snapshot resolve to 25.
- **FR-011**: Governed docs state 25 or mark older counts historical.
- **FR-012**: A missing lecture, a wrong `summary_profile`, and a missing workflow-context file each fail as structured envelopes, not raw exceptions.

## Success Criteria

- An agent can preview and then confirm a workflow derivation over MCP without a terminal.
- No agent-supplied value can select a provider, an endpoint, a credential source, or a file to read.
- Registry is exactly 25 with Tools 1–24 unchanged.
- Full pytest adds no non-Hermes failures.

## Out of Scope

Skill, live provider confirm in tests, batch or multi-episode derivation, Spec 038 lecture changes, Hermes live, and any relaxation of the `api_cost_ack` gate.
