# Quickstart: Corpus Episode Completion Workflow Runner

## Prerequisites

- Use the local stdio MCP server or the thin CLI. No remote MCP service is part
  of 016.
- Run dry-run first. Confirm only the canonical episode reference and explicit
  action returned by that dry-run.
- Do not provide a real provider secret on the command line. Confirmed semantic
  summary uses a validated environment-variable name and may transfer transcript
  text outside the machine or incur cost.
- Confirmed semantic review is local and deterministic and uses no LLM
  configuration.

## Preview the Latest Episode

```powershell
python scripts/run_corpus_episode_completion_workflow.py --podcast gooaye
```

Defaults are `--episode latest --action next` with no confirmation. Expected
behavior:

- Resolves one canonical episode reference through the existing intake
  dry-run.
- Selects exactly one next ladder action or returns `completed`/`blocked`.
- For a seeded episode, builds one in-memory 008 index snapshot and one 009 plan
  snapshot and reuses them across deterministic and semantic classification.
- Creates, modifies, and deletes zero files; creates no `.part`; calls no
  stage runner, provider, environment loader, or progress callback.
- Prints metadata-only JSON containing the canonical ref, selected action,
  planned reads/writes, blockers, risk flags, warnings, and confirmation
  requirement.

The selected action is one of:

```text
intake
audio_download
local_transcription
deterministic_remediation
semantic_summary
semantic_review
completed
blocked
```

## Confirm One Explicit Action

Replace the placeholders with the exact values returned by dry-run:

```powershell
python scripts/run_corpus_episode_completion_workflow.py --podcast gooaye --episode CANONICAL_REF --action EXPLICIT_ACTION --confirm
```

Confirmed `latest` and confirmed `next` are rejected before feed, snapshot,
configuration, executor, or writer work. A valid confirmation:

1. recomputes fresh state;
2. rejects action drift without executing an alternative;
3. calls exactly one matching existing 013/012/011/010/015 runner;
4. records the bounded outcome;
5. writes the latest 016 JSON/Markdown reports; and
6. stops.

For `deterministic_remediation`, 016 fixes the existing runner to
`max_actions=1`. Confirmed 010-012 runners retain their existing
pre-execution 008/009 refresh; 016 performs no extra or post-stage refresh and
never rebuilds SQLite cache.

## Confirm Semantic Summary

Only use this command when dry-run selected `semantic_summary`. The
acknowledgement must exactly match the repository constant:

```powershell
python scripts/run_corpus_episode_completion_workflow.py --podcast gooaye --episode CANONICAL_REF --action semantic_summary --confirm --api-cost-ack "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
```

The exact acknowledgement is validated before RSS, snapshot, profile, local
environment, credential, provider, executor, progress, or report-writer work.
Only after the guard may the thin CLI use existing confirmed-summary
configuration resolution.

## Confirm Semantic Review

```powershell
python scripts/run_corpus_episode_completion_workflow.py --podcast gooaye --episode CANONICAL_REF --action semantic_review --confirm
```

Semantic review ignores provider, model, endpoint, credential-variable, chunk,
and acknowledgement options. It does not load `.env`, construct a provider,
transfer transcript text, or call an LLM.

## Use the Portable Agent Skill

Mount the repository stdio MCP server and make
`.agents/skills/corpus-episode-completion/SKILL.md` visible to the agent. Ask:

```text
Use the corpus-episode-completion skill to preview the latest episode for
podcast gooaye. Do not confirm an action until I explicitly approve it.
```

Expected protocol:

1. The agent calls only the completion MCP tool with `action=next` and
   `confirm=false`.
2. It explains the canonical ref, selected action, planned writes, blockers,
   and risks.
3. It asks one approval question and waits.
4. Missing, ambiguous, conditional, or negative replies cause no confirmed
   call.
5. Explicit approval produces one call to the same tool with the canonical ref,
   exact selected action, and `confirm=true`.
6. The agent reports the bounded outcome and stops.

If the tool is unavailable, the skill reports a setup problem without terminal,
CLI, other-tool, retry, scheduler, or autonomous fallback.

## MCP Setup and Safe Guard Validation

```powershell
python scripts/validate_mcp_setup.py
```

016 extends setup validation with registry discovery, Skill metadata, and an
early-rejected confirmed-`next` guard. Validation does not perform a real
latest RSS/corpus run, load `.env`, call a provider, or rebuild cache.

## Sanitized Fresh Ephemeral Smoke Record

The following fresh ephemeral read-only smoke was recorded during 016
implementation. It used the repository `corpus-episode-completion` Skill and
the corresponding local stdio MCP completion handler only; it did not invoke a
CLI, terminal fallback, or real corpus operation.

- **Input class**: unsafe podcast id; preview shape `action=next,
  confirm=false`.
- **Skill result**: PASS. General approval was not treated as an explicit
  canonical action confirmation. The protocol remained preview only, reported
  one bounded result, and stopped.
- **MCP early-guard result**: PASS. The unsafe podcast id combined with a
  confirmed `next` request returned only the fixed category-only error envelope
  before Core selection; it exposed no identifier, path, URL, secret, or raw
  content.
- **Observed side effects**: zero RSS/corpus/provider/cache access and zero
  files written. no CLI, other tool, retry, scheduler, loop, or automatic
  second action was used.

## Reports

Valid confirmed attempts write:

- `data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.json`
- `data/corpus/{podcast_id}/corpus-episode-completion-workflow-run.md`

The reports have no `generated_at` and contain no feed/source URL, endpoint,
transcript/semantic/prompt/provider body, secret, raw exception, traceback, or
investment advice.

## Verification Commands

```powershell
python -m pytest tests/test_corpus_episode_completion_workflow_runner.py tests/test_corpus_episode_completion_skill.py
python -m pytest tests/test_corpus_episode_workflow_runner.py tests/test_corpus_semantic_remediation_runner.py tests/test_corpus_episode_intake.py tests/test_corpus_audio_download_runner.py tests/test_corpus_local_transcription_runner.py tests/test_corpus_remediation_runner.py
python -m pytest tests/test_mcp_server.py tests/test_mcp_tool_registry_contract.py tests/test_mcp_setup_validation.py tests/test_llm_ack_guard_contracts.py tests/test_llm_cli_no_leak.py tests/test_llm_provider_factory_boundary.py tests/test_cache_rebuild_guard.py tests/test_repository_secret_boundary.py tests/test_architecture_spec_docs.py
python -m pytest
python -m compileall src scripts
git diff --check
```
