# Tasks: Workflow Derivation Bundle

**Feature**: 042-workflow-derivation-bundle
**TDD**: RED before GREEN.

## Phase 1: Setup

- [x] T001 Record 042 in `specs/README.md` and add a verification-matrix row in `docs/verification-matrix.md`
- [x] T002 Add committed `config/operator_workflow.yaml` with this operator's `allowed_tools`

## Phase 2: Foundational

- [x] T003 RED `tests/test_workflow_derivation_profiles.py`: prompts forbid transcript and unnamed tools
- [x] T004 GREEN `src/podcast_ingest_core/workflow_derivation_profiles.py` as pure data
- [x] T005 RED/GREEN error + result types in `errors.py` and `models.py`
- [x] T006 RED/GREEN `storage.py` paths for `05`/`06` and run reports
- [x] T007 Export runner from `__init__.py` when it exists

## Phase 3: US2 Dry-run

- [x] T008 [US2] RED dry-run lists lecture + context + planned writes, writes nothing, no provider
- [x] T009 [US2] GREEN dry-run path in `workflow_derivation.py`

## Phase 4: US3 Fail closed

- [x] T010 [US3] RED finance / missing lecture / partial lecture / missing context refuse
- [x] T011 [US3] GREEN those refusals before LLM

## Phase 5: US1 Confirm

- [x] T012 [US1] RED confirm writes both files, omits tools absent from context, lecture unchanged
- [x] T013 [US1] GREEN confirm + atomic pair + ack-first
- [x] T014 [US1] GREEN thin `scripts/run_workflow_derivation.py`

## Phase 6: US4 Honesty

- [x] T015 [US4] RED reconstructed labels when lecture has no prompt section
- [x] T016 [US4] GREEN prompt instructions encode the labels

## Phase 7: Index + polish

- [x] T017 Append `workflow_derivation` to `SUPPORTED_ARTIFACT_FAMILIES`; do not touch `ARTIFACT_LADDER`
- [x] T018 Assert registry still 24; lecture available without `05`/`06`
- [x] T019 `python -m pytest` targeted + `compileall`
