# Implementation Plan: Source learning entry Skill

**Feature**: 057-source-learning-entry-skill | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)
**Branch**: None; the existing dirty working tree is preserved.
**Authorization**: User approved the presented flow and explicitly requested planning followed directly by implementation.

## Summary

Add one independent source-learning-entry coordination Skill over the existing preparation preview/confirm, job status and content-query tools. It handles only a user-requested source question/learning-note journey. Keep preparation-only and prepared-source QA Skills independent. A URL ready result may hand off to QA immediately; an accepted submission always stops. A later status-only request stops; explicit learning continuation may check the retained job then hand off on matching ready state.

## Technical Context

**Language/Version**: Portable Markdown Skill instructions; repository Python >=3.11, current local venv3.12.9 for pytest.
**Primary Dependencies**: Existing FastMCP Tools33/34/35, source-preparation response contract, source-content-qa Skill and references. No new dependencies.
**Storage**: Existing preparation ledger/transcripts owned by Core; entry context remains in conversation, no new persistent store.
**Testing**: pytest docs/resource/backend characterization, labelled synthetic conversation probes, owned read-only source pilot, standard regressions.
**Target Platform**: Agent hosts loading local portable Skills, with same mounted repo MCP server. Windows stdio new submissions retain worker_host_incompatible; compatible independent HTTP hosting is operator-managed.
**Project Type**: Skill-only coordination over reviewed runtime.
**Performance Goals**: One URL preview per requested entry, at most one confirmed submission, one status call per explicit progress/continuation request. Retrieval uses existing limits/budget.
**Constraints**: No automatic polling, prepare retry, settings edits, service launch, model fallback, new tools, formal generation or automatic cache rebuild.
**Scale/Scope**: One source, one request, current conversation; configured YouTube/X URL or known prepared RSS/YouTube/X identity.

## Constitution Check

Pre-design and post-design: PASS without amendment (v1.0.1). Core remains the sole runtime executor; interfaces and35tools remain stable. Preparation is dry-run-first with fresh explicit confirmation; no repository LLM provider is constructed. Host processing of returned text retains SPEC056 privacy/billing separation and local-only requirement. Formal generation/provider opt-in/ack gates remain separate. Timed evidence, inference and AI additions stay distinct; no live market API or investment advice. No .env/credentials/settings access. Cache remains manual. TDD, docs checks, full pytest, compileall and diff-check are required.

## Project Structure

- specs/057-source-learning-entry-skill/: spec, plan, research, data-model, contracts/skill, quickstart, tasks, requirements/interaction checklists, implementation-log.
- .agents/skills/source-learning-entry/SKILL.md and references/entry-protocol.md: new coordination and conditional reference.
- Existing source-preparation/references/response-contract.md and source-content-qa with its references/template are required installed resources, referenced by Skill identity; no duplicate learning-note template.
- tests/test_source_learning_entry_skill.py; tests/test_spec_057_source_learning_docs.py; tests/fixtures/source_learning_entry_cases.json.
- AGENTS.md active marker; specs/README.md; .agents/skills/README.md; docs/mcp-usage.md, docs/install-and-porting.md, docs/verification-matrix.md, docs/roadmap.md: discoverability and operator handoff only.

**Structure Decision**: A standalone coordinator avoids weakening either existing Skill's stopping rules. No runtime parser/router/store is added. Entry resources link internally and declare the two installed Skill dependencies. Missing required resources stop instead of inventing a fallback.

## Phases

1. Resolve existing contracts and capabilities; write spec/design/checklists/tasks and analyze.
2. Establish failing docs/resource checks and current standalone baseline.
3. Build ready-entry and preparation/continuation protocol with controlled backend cases.
4. Validate portable resources and independent simulated decisions; update operator docs.
5. Run relevant regressions/full checks, converge intent against implementation, record actual host acceptance status.

## Verification and host acceptance

Use short unused workspace-contained pytest temp directories and process-only exact-repo Git safe.directory. Transport tests require the same approved host context that passed SPEC056. Preserve logs and explicit exit receipts in ignored scratch. Synthetic probes do not call MCP or prove live Hermes. Existing X source may be read in isolated configured data root; record version/pages/input hashes, no content in committed logs.

Actual Hermes acceptance requires an accessible already configured host, matching data root and mounted Skills/tools. Discovery found no hermes/hermes-agent executable or callable Hermes tool. Deliver the runnable acceptance guide and record the execution gate pending; keep the live task unchecked until real trace/output is available. No installation, service launch or external inference is implied by development authorization.

## Complexity Tracking

No constitution violation or new subsystem. Known risks: busy job belongs elsewhere; status omits URL/source_type; readiness can still be unreadable; context_digest in non-executable previews is not an approval binding. Contracts explicitly handle these without runtime changes.
