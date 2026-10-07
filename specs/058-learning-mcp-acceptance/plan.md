# Implementation Plan: Learning MCP acceptance and Hermes handoff

2026-10-08 | [Specification](spec.md) | No branch creation

## Summary and Technical Context
Python >=3.11/current3.12, existing MCP SDK/stdlib and pytest; Windows/Linux. Add Core learning_mcp_acceptance.py and thin scripts/verify_learning_mcp.py. No new dependency/tool or persisted state. Defaults20 tool calls,60000 chars,60-second whole-operation timeout. Explicit source/time range and connection. JSON stdout only; operator may redirect to a new owned receipt.

## Constitution Check
Constitution1.0.1 reviewed without amendment; all nine gates pass before/after design. Core owns validation/transports/inventory. No side-effect tool, repository LLM, .env/config-secret read, corpus copying/repair, live market API, advice, automatic cache rebuild or deployment. Evidence delivery is distinct from ASR/answer/host quality. TDD, targeted/full pytest, compileall, diff and read-only review required.

## Project Structure
src/corpus_ingest_core/learning_mcp_acceptance.py; scripts/verify_learning_mcp.py; tests/test_learning_mcp_acceptance.py; tests/test_spec_058_learning_acceptance_docs.py. This package includes research/data-model/contracts/quickstart/content-acceptance/checklists/tasks/implementation-log. Discovery updates in specs/README.md, docs/install-and-porting.md, docs/verification-matrix.md, docs/roadmap.md, AGENTS.md. Existing35tools/Skills unchanged.

## Design and execution
Clarify: tooling/handoff authorized; actual inaccessible Hermes and undisclosed preparation stay operational gates. No further scope question.
Validate requests before connection. List required native learning tools, allowing filtered registry. Fresh inspect exact identity/read-only/network=false and pin version. Read fixed range; verify ordinal/offset/timestamp continuity, stable selection count and cursor progress. Reserve final inspect; budgets yield partial. Final inspect detects drift. Empty selection is complete zero delivery. Finite metadata only.
Owned stdio runs existing repo runner with child-only explicit safe data root and silent raw server diagnostics. Existing HTTP accepts numeric loopback http URLs without credentials/query/fragment; redirects/proxy disabled; no service launch. Timeout covers setup/calls/teardown; no retries.
Inventory walks Markdown relative-resource links recursively beneath three fixed Skill folders, finite file/count limits and secure reads. Require single notes template; missing/unsafe/out-of-folder resources fail. No copy/install/archive.
TDD before code; malformed/partial/budget/transport/resource coverage; actual SDK pilot on existing isolated X with preserved hashes; full regression, fresh review, Converge.

## Operational gates
Guide covers ready-ID/URL, Windows stdio incompatibility, model/device prerequisites, approved submission, one status call, explicit continuation, human rubric and metadata-only host records. Live preparation requires fresh disclosed-plan consent and compatible existing host. Hermes inference requires accessible already configured host. Do not install/configure services or close SPEC057 T017/T018 with SDK evidence.

## Complexity Tracking
New operator utility with two transport adapters, no architecture rewrite or constitution exception.
