# Research: Corpus Episode Completion Workflow Runner

## Decision: Add a coordinator without expanding existing public runners

**Rationale**: 013–015 already own intake, deterministic progression, and
semantic remediation. Feature 016 needs to compose those capabilities under one
human-controlled entry point, not redefine their standalone contracts. A new
Core coordinator can reuse their public executors and small package-private
preview seams while keeping every existing signature, report, schema, and CLI
stable.

**Alternatives considered**:
- Extend 014 through semantic work: rejected because 014's no-LLM four-stage
  contract is implemented and guarded.
- Extend 015 backward through intake/transcription: rejected because 015 is an
  explicit-episode semantic-only capability.
- Build a generic orchestration framework: rejected as unnecessary abstraction
  for one bounded workflow.

## Decision: Preview latest, confirm only the canonical episode reference

**Rationale**: `latest` is useful for operator discovery, but feed ordering can
change between preview and confirmation. The dry-run resolves `latest` through
the existing 013 selector path and returns one canonical episode reference.
Confirmed requests reject `latest` and require that canonical reference,
making the approved target stable and auditable.

**Alternatives considered**:
- Allow confirmed `latest`: rejected because a newly published episode could
  silently replace the approved target.
- Ban `latest` entirely: rejected because safe preview can resolve it without
  authorizing a side effect.

## Decision: Reject confirmed next and recompute exact action equality

**Rationale**: `action=next` is a preview convenience, not an authorization.
Confirmed execution requires one explicit executable action. The coordinator
rebuilds fresh state and compares the selected action to the requested action;
any drift returns `rejected` with zero executor calls and does not fall forward
to the newly selected action.

**Alternatives considered**:
- Let confirmed `next` choose at runtime: rejected because it authorizes an
  unknown side effect.
- Execute the new state after drift: rejected because the human approved a
  different action.

## Decision: Resolve once and reuse one in-memory 008/009 snapshot pair

**Rationale**: Unseeded state can be selected from the existing 013 dry-run and
safe seed existence check. A seeded episode needs exactly one private 008 index
build and one 009 plan build. The same snapshot is reused across deterministic
and semantic classification, avoiding inconsistent rescans and preserving
strict zero-file preview.

**Alternatives considered**:
- Read persisted index/plan reports: rejected because stale sentinels must not
  become stage truth.
- Call public 008/009 generators: rejected because they persist files.
- Build a second snapshot for semantic classification: rejected because the two
  ladders could observe different state and double scan cost.

## Decision: Extract narrow package-private preview seams from 014 and 015

**Rationale**: 014 already maps 012/011/010 preview results to deterministic
workflow stages, and 015 already reduces transcript/semantic artifact state.
Extract package-private helpers that accept an already-resolved canonical
episode and caller-supplied index/plan snapshot. Existing public functions
delegate to these helpers; their signature, standalone refresh behavior, and
result types remain unchanged. The 014 seam has a private strict
semantic-handoff mode for 016: after audio/transcription are complete it
requires transcript status to be exact `valid`, bounds deterministic preview
to one row, and ignores only semantic-summary/semantic-review blockers after
all non-semantic work is complete. Public 014 does not enable this mode.

**Alternatives considered**:
- Duplicate reducers in 016: rejected because stage rules would drift.
- Add public snapshot parameters: rejected because it broadens existing public
  contracts for one internal composition need.

## Decision: Validate semantic acknowledgement before every observation surface

**Rationale**: Confirmed semantic summary may transfer transcript content and
incur cost. The exact acknowledgement must be checked immediately after bounded
request normalization, before RSS/feed access, snapshot building, profile or
`.env` loading, credential lookup, endpoint/provider construction, progress
callbacks, executor calls, or report path/writer work. Core enforces the guard;
CLI provides an earlier wrapper guard before its confirmed-only config loader.

**Alternatives considered**:
- Reuse the stage runner's later guard only: rejected because 016 would already
  have read feed/snapshot/config state.
- Load defaults before acknowledgement: rejected because invalid consent must
  observe no secret-bearing configuration.
- Apply acknowledgement to semantic review: rejected because review is local
  and deterministic.

## Decision: Dispatch one existing runner and stop

**Rationale**: After exact selection equality, map actions to the established
public runners: 013 intake, 012 audio download, 011 local transcription, 010
deterministic remediation, and 015 semantic summary/review with the explicit
same action. Attempt exactly one call, map its bounded result or exception
category, write the 016 report, and stop. A runner may independently reject,
block, fail, or reuse after its own fresh checks; 016 records that terminal
outcome and never tries another stage. The 010 call fixes `max_actions=1` so a
confirmed deterministic action cannot execute multiple remediation rows.

**Alternatives considered**:
- Call lower-level executors directly: rejected because it bypasses existing
  runner contracts and safety checks.
- Continue to the next stage after success/reuse: rejected because one approval
  authorizes one action.
- Retry or compensate after failure: rejected because v1 has no retry or
  rollback policy.

## Decision: Keep 016 reports latest, confirmed-only, and metadata-only

**Rationale**: Valid confirmed attempts write a deterministic latest JSON and
Markdown pair under the podcast corpus root using the repository's per-file
atomic `.part` replacement pattern. Reports omit `generated_at`, URLs,
content bodies, raw responses, secrets, and exception messages. Dry-run,
invalid input, invalid acknowledgement, and drift before report allocation
write nothing.

**Alternatives considered**:
- Persist previews: rejected by strict zero-file behavior.
- Add timestamped history: rejected because 016 is a latest coordinator report;
  existing stage artifacts retain their own audit history.
- Transactionally roll back a completed stage if report writing fails: rejected
  because it would cross artifact ownership and risk deleting valid output.

## Decision: Add one dedicated safe MCP tool and preserve envelope conventions

**Rationale**: The approved agent surface needs one reviewed stdio tool named
`run_corpus_episode_completion_workflow`. It mirrors bounded Core inputs,
omits the callback, never loads `.env`, and returns the repository's existing
success/dry-run/error envelope shapes. Structured blocked/rejected/failed Core
results remain successful calls whose data explains the outcome. Only invalid
or uncontained command errors produce a fixed category-only error envelope.
The exact registry guard changes from 12 to 13; all existing tool schemas stay
unchanged.

**Alternatives considered**:
- Reuse a sequence of existing tools: rejected because it moves stage selection
  and single-action enforcement into the agent.
- Add remote HTTP MCP: rejected because auth, TLS, deployment, and remote secret
  policy require a separate feature.
- Return raw exception strings: rejected by the no-leak boundary.

## Decision: Put the human conversation in a portable Agent Skill

**Rationale**: The portable skill describes preview → explain → ask → wait →
confirm exact action → report → stop. It treats missing, ambiguous, and negative
answers as no approval. When the MCP tool is missing it reports setup failure
and forbids terminal, CLI, another tool, scheduler, or autonomous-loop fallback.
Core remains the hard security boundary because skills are instructions, not
enforcement.

**Alternatives considered**:
- Put conversational prose in the MCP tool: rejected because tools return state
  while agents own dialogue.
- Add Codex-only plugin packaging: rejected because the requested artifact is a
  portable skill plus MCP server.
- Add Hermes Agent/OpenClaw setup fixtures: rejected by the approved 016 scope;
  client-specific integration can follow later.

## Decision: Validate Codex without real corpus/provider side effects

**Rationale**: Automated tests validate Skill metadata/protocol, exact MCP
registration, wrapper selection, and absence of fallback/autonomous wording.
The final Codex smoke uses a fresh session and a deliberately safe dry-run or
invalid bounded selector so discovery and tool choice can be observed without
reading real transcript data, loading real `.env`, calling a provider, or
writing corpus artifacts.

**Alternatives considered**:
- Use a real episode/provider: rejected because it may expose local data and
  incur cost.
- Claim Hermes Agent/OpenClaw live compatibility from format inspection:
  rejected because those clients are not installed or verified in 016.

## Decision: Preserve confirmed runner refresh compatibility without extra rebuilds

**Rationale**: Existing confirmed 010-012 public runners intentionally refresh
and persist 008/009 before selecting/executing their stage. Calling those
unchanged public contracts means 016 confirmed mode inherits that
pre-execution refresh. The zero-file requirement applies to 016 dry-run. The
coordinator performs no additional or post-stage index/plan refresh and never
rebuilds SQLite cache.

**Alternatives considered**:
- Bypass public runners to avoid the refresh: rejected because it would
  duplicate or skip their established safety and execution contracts.
- Promise confirmed zero index/plan writes: rejected because it contradicts
  compatibility with unchanged 010-012 public runners.

## Decision: Preserve cache, market-data, advice, and automation boundaries

**Rationale**: Outside the established confirmed 010-012 pre-execution refresh,
016 adds no persisted 008/009 refresh and never rebuilds SQLite cache. It adds
no live market API, stock lens, research workflow, batch, latest-N, scheduler,
cron, retry, force, partial work, transcript repair, or full-chain loop.
Confirmed results warn that post-stage derived metadata may be stale and
requires a separate human-triggered refresh.

**Alternatives considered**:
- Automatically rebuild after a write: rejected by the manual cache principle.
- Add future autonomous mode now: rejected because it requires budgets, stop
  conditions, retry, and approval policies in a separate feature.
