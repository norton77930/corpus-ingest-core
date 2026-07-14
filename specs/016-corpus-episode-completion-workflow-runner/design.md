# 016 Corpus Episode Completion Workflow Runner — Approved Design

**Date**: 2026-07-13

**Status**: Approved design; implementation not started

## Goal

Provide one deterministic, single-episode completion entry point that an AI
agent can call through MCP while a human remains in control of every side
effect. The entry point spans the existing 013–015 ladder, but every confirmed
invocation executes at most one explicitly named action and then stops.

The immediate supported agent is Codex. The MCP tool and skill use open MCP and
Agent Skills conventions so skills-compatible Hermes Agent or OpenClaw
installations should be able to mount them, but 016 does not include
Hermes/OpenClaw-specific installation, fixtures, or live verification.

## User Outcome

An operator can ask an agent to complete one podcast episode. The agent loads a
portable skill, calls the completion MCP tool in dry-run mode, explains the
selected action and risks, waits for explicit approval, calls the same tool
with the explicit confirmed action, reports the result, and stops.

The agent does not decide workflow order. A deterministic Core state machine
selects the next action from RSS resolution and local artifact metadata.

## State Ladder

The ordered state ladder is:

```text
intake
→ audio_download
→ local_transcription
→ deterministic_remediation
→ semantic_summary
→ semantic_review
→ completed
```

Any unsafe or indeterminate state becomes `blocked` or `failed`; the runner
does not skip forward, retry, repair, or choose a fallback action.

## Public Surfaces

### Core

Add an additive public Core function named
`run_corpus_episode_completion_workflow()`. Its request includes:

- podcast id and `latest` or explicit episode selector;
- `next` or one explicit executable action;
- confirmation and exact semantic API-cost acknowledgement;
- bounded local-transcription options;
- bounded semantic provider/model/endpoint/env-name/chunk options;
- an optional safe progress callback.

The function returns an additive immutable result model with normalized
request metadata, selected/executed action, one bounded outcome row, counts,
warnings, risk flags, safe paths, confirmed report paths, and
`not_investment_advice=true`.

Dry-run accepts `latest` or an explicit selector. Confirmed execution rejects
`latest` and requires the canonical episode ref returned by dry-run, so a newly
published RSS episode cannot silently change the target that the human
approved.

### CLI

Add `scripts/run_corpus_episode_completion_workflow.py` as a thin parser and
Core caller. Dry-run and all non-semantic actions bypass LLM profile and local
environment loading. Confirmed semantic summary validates the exact
acknowledgement before profile, `.env`, endpoint, credential, snapshot, RSS,
provider, executor, or writer work.

### MCP

Add the thirteenth MCP tool:

```text
run_corpus_episode_completion_workflow
```

The MCP wrapper keeps the repository's existing success/error envelope style.
It exposes only bounded non-secret options and metadata. It never reads a
local `.env` file; provider credentials remain environment variables of the
MCP server process. The exact MCP registry guard changes from 12 to 13 while
the existing twelve tool schemas and behavior remain unchanged.

### Portable Agent Skill

Add:

```text
.agents/skills/corpus-episode-completion/SKILL.md
```

The skill uses standard `SKILL.md` frontmatter and client-neutral instructions.
It requires this protocol:

1. Call the completion MCP tool with `action=next` and `confirm=false`.
2. Explain the selected action, planned writes, network/compute/transcript
   transfer/API-cost risks, acknowledgement requirement, and blockers.
3. Ask one explicit approval question and wait for the user's answer.
4. Treat ambiguous, missing, or negative answers as no approval.
5. After approval, call the same tool with the exact selected action and
   `confirm=true`; semantic summary also requires the exact acknowledgement.
6. Report the bounded result and stop. Do not perform another dry-run or action
   unless the user asks again.

If the MCP tool is unavailable, the skill reports a setup problem. It does not
fall back to a terminal command, CLI, a different side-effect tool, cron, or an
autonomous loop.

## Deterministic Data Flow

1. Normalize and validate podcast, selector, action, confirmation, positive
   numeric settings, and safe non-secret identifiers.
2. Reject confirmed `next` before any read or write.
3. Reject confirmed `latest` before any read or write; confirmation requires
   the canonical episode ref returned by dry-run.
4. Reject a confirmed semantic summary without the exact acknowledgement
   before RSS, snapshot, profile, `.env`, credential, provider, executor, or
   writer work.
5. Use the existing 013 dry-run selector path to resolve `latest` or an
   explicit selector to one canonical episode.
6. If no safe seed exists, select `intake`.
7. For a seeded episode, build exactly one fresh in-memory 008 index snapshot
   and exactly one 009 plan snapshot.
8. Reuse package-private 014 preview logic in a strict semantic-handoff mode to
   classify intake through deterministic remediation. This private mode blocks
   any transcript state other than exact valid, bounds deterministic remediation
   to one selected row, and ignores only semantic-family blockers after
   non-semantic work is complete; public 014 behavior remains unchanged.
9. Only when the deterministic ladder is complete, reuse package-private 015
   preview logic with the same snapshot to classify semantic summary, semantic
   review, completed, or blocked.
10. Dry-run returns immediately and creates, modifies, or deletes zero files.
11. Confirmed execution requires the explicit freshly selected action. It
    dispatches the matching existing 013, 012, 011, 010, or 015 public runner
    exactly once, records the bounded result, writes the 016 latest report, and
    stops.
12. If state changed, return `rejected`; never execute the newly selected
    alternative action.

Existing 013–015 public APIs, CLIs, schemas, reports, and standalone behavior
remain unchanged.

## Human-Control Boundary

The Core and MCP tool enforce the rules that must not depend on agent
obedience:

- strict zero-file dry-run;
- explicit confirmed action;
- exact semantic acknowledgement;
- fresh-state equality before dispatch;
- exactly one executor attempt;
- no fallback, retry, loop, batch, scheduler, extra/post-stage index or plan
  refresh, or cache rebuild; unchanged confirmed 010-012 runners retain their
  established pre-execution 008/009 refresh;
- category-only failures and bounded output.

The skill owns the conversational protocol: explain, ask, wait, confirm, report,
and stop. A skill is guidance rather than a security boundary, so Core guards
remain effective even when the skill is missing or ignored.

## Reports and Safe Output

Confirmed stage attempts that pass early validation and fresh action-equality
checks write:

```text
data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.json
data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.md
```

Each file uses the repository's atomic `.part` replacement pattern. The pair
is not transactional. Reports contain only bounded metadata, safe local paths,
counts, fixed reasons, warnings, risk flags, safe provider/model identifiers,
and category-only failures. They do not contain `generated_at`, RSS/source URL,
base URL, query/fragment, transcript/evidence/semantic/prompt/provider bodies,
secret values, raw exception messages, or traceback bodies.

Early-invalid, terminal, and drift-rejected requests write no 016 report. A
report-write failure after one stage attempt is an uncontained safe command
error. Existing stage artifacts and stage reports remain; 016 performs no
cleanup, retry, fallback, or compensating action.

## Error Semantics

- Invalid request or invalid acknowledgement raises the dedicated 016 error
  before reads or writes.
- RSS/selector failure is category-only and fail-closed.
- Snapshot failure maps to action `blocked`, row status `failed`, and
  `manual_only=true` with no later probe or dispatch.
- Missing episode, invalid transcript, unreadable semantic summary, failed or
  unknown semantic review, or unsafe dependency maps to blocked/manual-only.
- Confirmed action drift maps to rejected with zero executor calls.
- A stage-runner blocked, rejected, failed, or exception result is recorded and
  stops the completion runner.
- Semantic review ignores every LLM configuration option and reads no profile,
  `.env`, credential, or provider configuration.

## Testing and Acceptance

Implementation follows RED→GREEN TDD.

### Core integration

- Real 008/009 builders cover every ladder action and terminal state.
- Every dry-run case proves an identical path/hash/size/mtime tree manifest,
  zero writer/provider/env/executor/progress calls, no `.part`, and no stale
  persisted index/plan/report truth.
- Seeded preview proves exactly one index snapshot and one plan snapshot reused
  across deterministic and semantic classification.
- Confirmed tests prove one matching runner call, no other runner calls, drift
  rejection, no fallback, and stop-after-one-action.

### LLM and no-leak

- Wrong or missing acknowledgement precedes RSS, snapshot, profile, `.env`,
  provider, executor, and report writer work.
- Review ignores malicious LLM options.
- Adversarial source/exception/provider content cannot appear in JSON,
  Markdown, stdout, stderr, or MCP responses.

### MCP and skill

- Registry is exact 13 and existing tool contracts remain stable.
- New tool dry-run/confirmed/error envelopes and bounded schema are locked.
- Skill frontmatter and required procedure are validated.
- Skill tests prohibit terminal/CLI/other-tool fallback and autonomous loops.
- A Codex smoke test verifies a fresh Codex session can discover the repository
  skill, discover the MCP tool, select it for a safe dry-run request, and avoid
  calling a side-effect action. The smoke does not use real transcript data,
  call an external LLM provider, or write corpus artifacts.

### Final gates

- Targeted 013–016, MCP, skill, acknowledgement, secret, cache, and governance
  suites.
- Full `python -m pytest`.
- `python -m compileall src scripts`.
- `git diff --check`.
- All 016 tasks/checklists complete before status becomes `Implemented`.

## Exclusions

016 does not include Hermes/OpenClaw-specific setup files, installation,
fixtures, or live smoke tests; Codex plugin packaging; Skills Hub or ClawHub
publishing; remote HTTP MCP; auth/TLS/deployment; batch/latest-N; scheduler;
cron; retry; transcript repair; force/partial semantic work; stock lens;
research workflow; live market data; extra/post-stage index/plan refresh;
automatic cache rebuild; or autonomous full-chain execution.

Future autonomous execution, if approved, is a separate feature that adds an
outer loop, budgets, stop conditions, retry policy, and approval policy without
weakening 016's single-action contract.
