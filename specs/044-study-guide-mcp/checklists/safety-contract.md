# Safety and Contract Requirements Checklist

**Purpose**: requirements-quality gate before implementation, not proof of working code.
**Created**: 2026-10-02 | **Feature**: [spec.md](../spec.md)
**Audience**: Claude/Grok implementer and reviewer | **Depth**: standard, with publication/data-loss and MCP secrecy emphasis.

## Completeness

- [x] CHK001 Are the start point, four outputs and excluded upstream/downstream actions explicit? [Completeness, Spec FR-001/004/008/012]
- [x] CHK002 Are exact public parameter names/defaults and forbidden overrides specified? [Completeness, Spec FR-009, Contract Input]
- [x] CHK003 Are artifact writes, report writes and reuse distinguished in every preview branch? [Completeness, Spec FR-002, Data-model Action Selection]
- [x] CHK004 Are existing derivations and extra regular files separately defined? [Completeness, Spec FR-006/007, Data-model Existing Entities]
- [x] CHK005 Are identity JSON reads distinguished from sending transcript content to an LLM? [Completeness, Spec Safety, Plan Core entry]

## Clarity and Consistency

- [x] CHK006 Is conditional ack consistent for generation, reuse and cover-only across spec/plan/contract? [Consistency, Spec FR-005]
- [x] CHK007 Is cover-only defined for missing and safe non-readable-UTF8 cover without authorizing deletion on I/O errors? [Clarity, Spec Clarifications, Data-model Action Selection]
- [x] CHK008 Does byte preservation explicitly include newline/BOM/binary contents and exclude ACL/mtime guarantees? [Clarity, Spec FR-007/Edge Cases]
- [x] CHK009 Are run-mode labels pinned to existing Core values rather than copied from video tools? [Consistency, Contract Preview]
- [x] CHK010 Are existing CLI/result/report schemas and the new MCP-only projection distinguished? [Consistency, Plan Core entry, Contract Compatibility]

## Failure and Recovery Coverage

- [x] CHK011 Are all four recovery sibling names and all-mode zero-write refusal specified? [Coverage, Spec FR-013, Data-model Refusal Precedence]
- [x] CHK012 Is the publication commit point defined independently from cleanup/report success? [Clarity, Spec FR-014, Data-model Publication State]
- [x] CHK013 Are pre-commit failure, rollback failure, post-commit cleanup failure and report failure all covered? [Coverage, Spec US3, Contract Errors]
- [x] CHK014 Are report failure after reuse and after publication distinguishable without changing envelopes? [Consistency, Spec FR-014, Contract Errors]
- [x] CHK015 Are links, dangling links, Windows reparse points, unsafe ancestors, child directories and special files covered? [Coverage, Spec FR-013, Plan Core entry]
- [x] CHK016 Are concurrency and source-currentness explicitly excluded rather than silently promised? [Clarity, Spec Edge Cases]

## Safety and Testability

- [x] CHK017 Are fixed error messages and unknown-exception fallback specified without raw exception interpolation? [Measurability, Spec FR-011/014, Contract Errors]
- [x] CHK018 Are no-env/provider/network preview and no automatic cache/downstream action requirements measurable? [Measurability, Spec FR-003/004/008, SC-002/003]
- [x] CHK019 Is the first-25-tool compatibility prefix preserved while the new count is separately identified as future state? [Consistency, Spec FR-010, Contract Compatibility]
- [x] CHK020 Are fake-provider testing, native-versus-mocked filesystem checks and full verification obligations recorded? [Acceptance quality, Spec SC-005, Quickstart]
- [x] CHK021 Are framework-independent user outcomes tied to observable artifact/status results? [Measurability, Spec SC-001/004]
- [x] CHK022 Do the requirements retain no investment advice, no live market API, manual cache and finance-prompt boundaries? [Coverage, Spec Safety, Plan Constitution Check]
- [x] CHK023 Is implementation explicitly left to the designated developer, with one writer and no unsolicited git actions? [Scope, Spec Workflow Status, Handoff]

## Review Notes

23/23 requirements-quality items were reviewed against the written design. Checked items do not mean implementation tests passed. No unresolved requirement question remains; code execution and review evidence belong to tasks.md and the future implementation log.
