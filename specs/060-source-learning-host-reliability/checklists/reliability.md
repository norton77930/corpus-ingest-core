# Reliability and evidence requirement checklist

Purpose: Assess whether spec/plan/contracts define all failure classes before code changes; this is not a runtime pass report.
Created: 2026-10-08. Feature: [spec](../spec.md), [contract](../contracts/learning.md).

- [x] CHK001 Are full-version and identity/action/query/window bindings explicitly preserved? [Safety, FR-002]
- [x] CHK002 Are token length, canonical form, corrupt in-range positions and legacy limits defined? [Completeness, FR-001, FR-004]
- [x] CHK003 Are search selection indexes distinguished from ordinals and split-text offsets? [Clarity, FR-003]
- [x] CHK004 Does recovery require the successful response rather than the failed request and preserve allowance/budgets? [Consistency, FR-005–007]
- [x] CHK005 Are initial/recovery inspect failure, source drift, unsafe/missing data, malformed replies and second errors defined as stops? [Coverage, FR-006]
- [x] CHK006 Does the discovery test requirement cover normalization, actual truncation and a negative case? [Completeness, FR-008]
- [x] CHK007 Are local-first calls and no silent web fallback distinguished from preview metadata networking? [Clarity, FR-009–010]
- [x] CHK008 Do delegation/progress restrictions leave approved server-managed media jobs intact? [Consistency, FR-011–012]
- [x] CHK009 Are source concept evidence, literal search limits and relevant example fidelity testable separately? [Completeness, FR-013–016]
- [x] CHK010 Are source quotations distinguished from narrator gender inference, and supplements from attributed claims? [Clarity, FR-015, FR-017]
- [x] CHK011 Does whole-source verification require final-instant coverage and source-count equality, not exhaustion alone? [Coverage, FR-020]
- [x] CHK012 Are deterministic tests, synthetic SDK checks and real-host observations explicitly distinguished? [Consistency, FR-020]
- [x] CHK013 Are missing operator environment and host enforcement outside scope, without invented successful outcomes? [Dependencies, Spec Assumptions]
