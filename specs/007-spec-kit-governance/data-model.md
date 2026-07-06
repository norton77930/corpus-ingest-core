# Spec Kit Governance Data Model

**Status: Backfilled / As-built**

## Entities

- Constitution: project governance principles and workflow requirements.
- Spec Kit template: reusable prompt/template artifact aligned with constitution gates.
- Agent instruction: `AGENTS.md` repository rules for Codex work.
- Capability package: as-built spec directory with spec, plan, data model, quickstart, tasks, and checklist.
- Registry: `specs/README.md` mapping phases, modules, CLI/scripts, and tests.

## Boundaries

Governance artifacts are documentation and tests only. They do not read `.env`,
call LLMs, change MCP behavior, change runtime behavior, or fetch market data.
