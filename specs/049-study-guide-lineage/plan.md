# Implementation Plan: Study-guide lineage
Created2026-10-04. User requests plan then immediate implementation. No branch.
## Technical Context
Python3.11+ existing dataclasses/FastMCP/pytest. Filesystem-only local artifacts. No dependencies added. Input cap2MiB, receipt64KiB, outputs64MiB each. Existing staged-directory publisher and secure_local_snapshot readers remain boundary sources.
## Constitution Check
I traceable digests; II Core-only behavior and thin wrapper; III metadata writes disclosed before confirm; IV unchanged exact ack/no secrets; V scope warnings; VI unchanged output advice validation; VII no external API; VIII no cache rebuild; IX focused RED/GREEN and full regression. All PASS before and after design; no principle amendment.
## Phase0 Research
See research.md: receipt ownership, newline hashes, input capture, precedence and compatibility decisions resolved from local044/046/048 implementation.
## Phase1 Design
New pure study_guide_lineage.py uses public canonical_bytes/bytes_digest helpers from workflow_derivation_lineage; its schema remains separate and strict. Existing study_guide_bundle.py owns safe Core read query and publisher integration. Staged fingerprints use bounded secure reads and refuse oversized outputs before commit. Its original two-key describe_study_guide_plan projection stays unchanged for Tool27; Tool26 reads additive metadata directly from the result. Add default field in models.py and Tool26 preview metadata. New mcp_tools_study_guide_lineage.py registers last as Tool29, facade re-exports it. No existing048 behavior changes. Data-model and contract define exact fields/states.
## Implementation phases
Setup -> codec -> US1 generation and publication -> US2 observation -> US3 Skill and registry -> review/full/converge. One writer. Read-only reviews can inspect independent behavior/engineering areas. No worktrees or branch scripts.
## Paths and boundaries
Create src/corpus_ingest_core/study_guide_lineage.py, mcp_tools_study_guide_lineage.py, tests/test_study_guide_lineage.py, tests/test_mcp_study_guide_lineage.py, tests/fixtures/study_guide_lineage_skill_cases.json. Modify study_guide_bundle.py, models.py, mcp_tools_study_guide.py, mcp_server.py, scripts/validate_mcp_setup.py, .agents/skills/study-guide-bundle/SKILL.md, current docs/registry guards. Preserve other runtime modules, prior044-048 spec packages, workflow derivation Skill, pyproject and actual data. Compare baseline hashes at closeout.
## Complexity Tracking
No layering change. Receipt callback/optional argument extends existing publisher; old direct tests keep default behavior. No schema migration or aggregate freshness workflow.
