# Implementation Plan: Workflow Derivation Bundle

**Branch**: `042-workflow-derivation-bundle` | **Date**: 2026-08-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/042-workflow-derivation-bundle/spec.md`

## Summary

Add a dry-run-first Core runner that turns one available Spec 038 lecture plus an operator workflow-context document into `05_prompt_examples.md` and `06_apply_to_my_workflow.md`. Index them as a new `workflow_derivation` family. Do not send transcript text. Do not rewrite the lecture four. No MCP; registry stays at 24.

## Technical Context

**Language/Version**: Python 3.12 (repo as-is)

**Primary Dependencies**: none new. Reuse `create_provider` → `SemanticSummaryProvider.complete`.

**Storage**: same study-guide episode directory as 038 (`data/study-guides/{podcast}/{stem}/`); add `05`/`06` siblings. Metadata-only run report under `data/corpus/{podcast_id}/workflow-derivation-runs/`. Operator context: committed `config/operator_workflow.yaml`.

**Testing**: pytest. TDD per slice.

**Target Platform**: Windows first (PowerShell)

**Project Type**: library + thin CLI

**Performance Goals**: one confirmed LLM call emitting both documents.

**Constraints**: exact `api_cost_ack` first; dry-run zero-write/zero-LLM; no transcript egress; no MCP; no cache rebuild; no new dependency.

**Scale/Scope**: one episode per invocation; one new family; one new script; one context file.

## Constitution Check

- **I Local artifacts**: derivations come from on-disk lecture Markdown and a local operator-context file.
- **II Thin interfaces**: behaviour in `src/corpus_ingest_core`; CLI parses, calls, prints metadata-only JSON.
- **III Dry-run first**: `confirm=false` default; plan lists real reads/writes/reuses; no `.part` residue.
- **IV LLM opt-in / secrets**: confirmed generation requires exact ack before `create_provider`. Input is lecture + context, never transcript. `.env` values never appear. **No constitution amendment.**
- **V Evidence separation**: reconstructed catalogues and operator-application mappings are labelled. Tools not in context are forbidden as advice.
- **VI No investment advice**: `prohibited_advice` on both generated files.
- **VII No live market API**: unused.
- **VIII Manual cache rebuild**: warn only.
- **IX TDD**: RED then GREEN per slice.

Post-design: `workflow_derivation` MUST NOT join `ARTIFACT_LADDER`. 038 `study_guide` completeness MUST ignore `05`/`06`.

## Design Decisions

1. **Siblings, not a second directory.** `05`/`06` live next to `00`/`03`/`04`/`07` so the prototype reading order is preserved. Index treats them as a different family.
2. **Operator context is a YAML file**, default path `config/operator_workflow.yaml`, overridable by argument. Schema: `allowed_tools: [string, ...]`, optional `notes`. Empty or missing `allowed_tools` fails closed.
3. **One `complete()` call, JSON object with keys `05_prompt_examples` and `06_apply_to_my_workflow`.** Prompts in a new pure-data module. Provider protocol unchanged.
4. **Ack first** on the confirmed-LLM path. Dry-run does not demand ack.
5. **Atomic pair replace.** Write both files into a `.part` sibling then replace; failure deletes `.part` and leaves the previous pair.
6. **Refuse before LLM**: wrong profile, missing/partial lecture, missing context, finance-shaped lecture headings.

## Registry Impact

**None.** No MCP tool.

## Project Structure

```text
specs/042-workflow-derivation-bundle/
config/operator_workflow.yaml
src/corpus_ingest_core/storage.py
src/corpus_ingest_core/errors.py
src/corpus_ingest_core/models.py
src/corpus_ingest_core/workflow_derivation_profiles.py
src/corpus_ingest_core/workflow_derivation.py
src/corpus_ingest_core/corpus_index.py
src/corpus_ingest_core/__init__.py
scripts/run_workflow_derivation.py
tests/test_workflow_derivation.py
tests/test_workflow_derivation_profiles.py
tests/test_corpus_index.py
tests/test_contracts.py
docs/verification-matrix.md
specs/README.md
```

## Risks

- 038 completeness accidentally requiring six files. Mitigation: keep the four-name set; tests assert a lecture stays `available` without `05`/`06`.
- `ARTIFACT_LADDER` growing a derivation action. Mitigation: do not touch the ladder; test the tuple.
- Hard-coding Claude Code in Core. Mitigation: names come only from the context file; tests use a fixture that omits Copilot.
