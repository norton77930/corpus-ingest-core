# Research: 045 Operation Skills

## R1 - Two independent portable Skills

Decision: two single-tool instructions, following `.agents/skills/youtube-video-ingest/SKILL.md` and its contract tests. Rationale: matches the approved one-operation scope and existing repo packaging. Rejected: combined lecture/derivation execution, a new orchestrator tool, a new Python state machine, client-specific slash commands. Skills are instruction documents; runtime safety remains in Core.

## R2 - Cost classification uses actual responses

Decision: Tool 26 `mcp_tools_study_guide.py` exposes requires_llm/report_writes and run_mode=dry-run. Tool 25 `mcp_tools_workflow_derivation.py` exposes neither cost boolean nor report paths and uses run_mode=preview. Its `workflow_derivation.py` preview has empty writes and exact 05/06 reuses for no-cost complete-pair reuse, otherwise exact pair writes and empty reuses. The wrapper's generic cost risk overstates the reuse branch. Use bounded validated role combinations, not prose. Rejected: change Tool 25 runtime, treat absent requires_llm as false, require ack for every reuse, invent report filenames.

## R3 - Ack literal and real transfer boundary

Decision: embed the current literal from `llm_provider.SEMANTIC_API_COST_ACK`, pin it by import in tests, and require the user to provide it unchanged after preview for a generating plan. Explain that the shared literal mentions transcript while these operations send existing summary/lecture/context, not raw transcript. No-cost confirm always sends empty ack. Rationale: state drift from reuse to generation then hits the existing Core guard. Rejected: rewrite constant, auto-fill from generic yes, carry an earlier ack into a different operation.

## R4 - Transient consent, not digest pinning

Decision: approval binds one displayed tool/podcast/episode/force/cost-class request. A changed tuple requires a new explicit request/preview. No persistent tokens or filesystem reads. Both runners reevaluate state on confirm; do not promise stable source bytes. Rejected: source digest/currentness work under a Skill spec.

## R5 - Tool 25 backend limitations are explicit

Evidence: `workflow_derivation.py::_atomic_write_pair` restores an old backup when destination is absent and removes existing staging/backup entries. Tool 25 preview does not implement Tool 26's all-mode recovery refusal. Its wrapper/runtime may return str(exc); it also lacks Tool 26's full path/identity hardening.

Decision: instruct the agent never to delete/repair/retry, to stop on user-reported or tool-reported recovery trouble, and to avoid verbatim unknown errors. Document that this does not prevent existing backend behavior or sanitize transport before the model receives it. Rationale: preserving production runtime is the approved scope. Rejected: claiming equivalent safety to Tool 26, adding filesystem inspection fallback, silently expanding to Tool 25 runtime hardening.

## R6 - Honest offline verification

Decision: static contract checks, actual-wrapper characterization and synthetic dialogue acceptance cases. Existing precedents: `tests/test_youtube_video_ingest_skill.py`, `tests/test_mcp_study_guide_bundle.py`, `tests/test_mcp_workflow_derivation.py`, shared `tests/conftest.py::tmp_data_dirs`. Assertions must tie dialogue fixtures to rules actually present in Skill text. No fake agent as proof of model obedience. Live host behavior is unverified until separately evaluated.

## Research provenance

Main writer inspected local constitution, templates, Skill docs/tests and Core/wrappers. Read-only research agent `research_045_contract` independently checked signatures, branch semantics, ack source and legacy limitations. No agent modified files or called live services. Existing 044 modifications are the dependency baseline, not changes authored for 045.
