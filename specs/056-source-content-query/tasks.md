# Tasks — SPEC 056

One writer, dependency order below; no parallel mutation, branch, commit or deployment. Checklists assess specification quality, not runtime completion.

## Phase 1: Design and analysis

- [x] T001 Create selected package, research, contracts, checklists and run docs RED/GREEN; analyze traceability and constitution boundaries. FR-001–FR-014 SC-001–SC-005.

## Phase 2: Offline Core

- [x] T002 Add focused failing inspect/read tests for prepared RSS/YouTube/X with no cache; source identity/title/metadata/timestamps. tests/test_source_content_query.py. FR-001 FR-002 FR-003 SC-001 SC-002.
- [x] T003 Add failing safe-discovery/hardlink/open-handle/race/malformed/empty/partial/ambiguity tests; implement opt-in snapshot protection and strict source loader. src/corpus_ingest_core/{secure_local_snapshot,source_content_query}.py. FR-008 FR-009 SC-003.
- [x] T004 Implement inspect and version-pinned read using validated immutable segments; rerun focused checks. FR-002 FR-003 FR-005 SC-001 SC-002 SC-003.
- [x] T005 Add RED then implement literal search, range overlap, cursor binding, oversized text continuation and accurate coverage. FR-004 FR-005 FR-006 FR-007 SC-002 SC-003.
- [x] T006 Verify no side effects/network/provider/cache/SQLite, unsafe error projection and strict input limits. FR-001 FR-006 FR-010 FR-013 SC-001 SC-003.

## Phase 3: MCP

- [x] T007 Add wrapper/registry/schema/SDK failing checks; append thin Tool 35 and facade export, finite error mapping. tests/test_mcp_source_content_query.py; src/corpus_ingest_core/mcp_tools_source_content.py. FR-011 SC-004.
- [x] T008 Update current 35-tool counts/setup/console/facade/documentation guards; preserve first 34 signatures/order. FR-011 SC-004.

## Phase 4: QA Skill and pilot

- [x] T009 Run baseline pressure scenarios without new Skill; add failing Skill/dialogue checks. FR-012 FR-013 SC-005.
- [x] T010 Write .agents/skills/source-content-qa/SKILL.md, reference and dialogue fixtures; rerun pressure checks with Skill. FR-012 FR-013 SC-005.
- [x] T011 Execute read-only existing medium X pilot; reconstruct whole transcript via pages and keyword/range evidence with source hash preservation. FR-014 SC-001 SC-002 SC-003.

## Phase 5: Review and delivery

- [x] T012 Update operator docs, handoff, roadmap, verification matrix and specs registry; run targeted guards. FR-010 FR-011 FR-012 FR-013 FR-014 SC-004 SC-005.
- [x] T013 Fresh read-only review of behavior and engineering; fix evidenced gaps via RED/GREEN. FR-001 FR-002 FR-003 FR-004 FR-005 FR-006 FR-007 FR-008 FR-009 FR-010 FR-011 FR-012 FR-013 FR-014 SC-001 SC-002 SC-003 SC-004 SC-005.
- [x] T014 Full pytest, compileall src scripts, diff check; write implementation-log with skipped reasons/limits and converge, append only real gaps. FR-014 SC-001 SC-002 SC-003 SC-004 SC-005.
