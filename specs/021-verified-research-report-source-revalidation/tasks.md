# Tasks: Verified Research Report Source Revalidation

**Feature**: 021-verified-research-report-source-revalidation
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Contract**: [contracts/verified-research-report-source-revalidation.md](contracts/verified-research-report-source-revalidation.md)
**TDD**: Add and run focused RED tests before each minimal GREEN implementation change.

## Delivery sequence

`specify → clarify → plan → checklist → tasks → analyze → implement → converge`

## Completion Contract

| Claim | Status | Required evidence |
| --- | --- | --- |
| C0: Current MCP setup/governance has no 13/14/17 drift | PASS-current | Per-document RED→GREEN guards |
| C1: Complete SPEC 021 package has consistent requirements and non-goals | PASS-current | This docs contract, checklists, tasks, and analyze/converge review |
| C2: Bundle gate and source currentness are separate | PASS-current | Missing/invalid bundle fail-if-called tests |
| C3: Manifest/fixture/snapshot hostile paths never dereferenced | PASS-current | Canonical-before-read, containment, reparse, and race sentinels; Code and Architecture Review PASS |
| C4: Currentness shares 018 lineage and publisher source/digest rules | PASS-current | Lineage, role mutation, shared-seam and publisher-reuse regressions; Code and Architecture Review PASS |
| C5: Core/CLI/MCP output is bounded and sanitized | PASS-current | Serialization, subprocess, MCP, and secret sentinels |
| C6: CLI/MCP are thin; Tool 18 append-only and Tools 1–17 unchanged | PASS-current | One-call, registry, order, signature, and envelope tests |
| C7: Workflow is read-only/offline/zero-write with no dependency | PASS-current | Tree snapshots and writer/network/LLM/cache fail-if-called matrix |
| C8: Existing 018–020 behavior has no regression | PASS-current | Targeted publisher/workflow/catalog test set |

Only `planned`, `PASS-current`, `FAIL`, and `stale` are valid claim states. Revalidate only affected evidence after a change.

## Phase 1: Specification and analysis

- [x] T001 Create the complete SPEC 021 package and focused docs contract.
- [x] T002 Run the docs contract RED before the package exists, then document exact locator, bundle/currentness separation, hostile-path, zero-write, non-goal, and Tool 18 boundaries.
- [x] T003 Analyze existing 018–020 seams and storage ownership without changing their public contracts.

## Phase 2: Bundle gate and path safety

- [x] T004 Add RED tests for exact locator validation and secure shared exact-bundle evidence.
- [x] T005 Add RED fail-if-called tests: missing/invalid bundle makes all external checks `not_evaluated`.
- [x] T006 Add RED canonical-before-read hostile fixture/snapshot/manifest path sentinels.
- [x] T007 Implement the smallest Core-only evidence/safety extraction and rerun focused tests GREEN.

## Phase 3: Lineage, snapshots, and digest

- [x] T008 Add RED lineage current/missing/stale/mismatch tests and source role/hash/size/canonical-path mutations.
- [x] T009 Add RED tests for shared source snapshots, optional branches, digest mismatch, and replacement race.
- [x] T010 Implement shared canonical snapshot/digest seams with no publication, staging, or write behavior.
- [x] T011 Run 018/019 publisher regressions before proceeding.

## Phase 4: Thin interfaces

- [x] T012 Add CLI RED tests for exact forwarding, one Core call, generic bounded error envelope, and redaction.
- [x] T013 Add MCP RED tests for Tool 18 append-only registration; Tools 1–17 unchanged.
- [x] T014 Implement only the thin CLI and MCP adapter after Core GREEN.

## Phase 5: Converge

- [x] T015 Add zero-write/offline/disclosure sentinels and run focused Core/CLI/MCP/docs tests.
- [x] T016 Converge C0–C8 evidence; mark each `PASS-current`, `FAIL`, or `stale` only with recorded selected evidence.

## Final Verification (run exactly once)

After all C0–C8 are `PASS-current` and the main agent has reviewed the complete diff and role evidence, run exactly this one final verification:

```powershell
python -m pytest; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; python -m compileall src scripts; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; git diff --check; exit $LASTEXITCODE
```

Record actual passed/skipped counts, skip reasons, compileall/diff-check results, and confirm `uv.lock` was neither read, modified, nor staged; no generated data, secret, dependency change, branch, commit, or PR was created.
