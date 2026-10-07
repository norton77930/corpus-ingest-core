# Current Capability Map and Next Phase

Planning snapshot inspected 2026-10-03; subsequently authorized047 implementation is tracked in [implementation-log.md](implementation-log.md). Runtime source and executable contracts take precedence over older phase-log next-step notes. Working tree contains uncommitted 044-046 changes; this is a local implementation inventory, not a deployment claim. Latest recorded full regression: 046, 1872 passed / 26 native-symlink skips. That historical result is not rerun by this planning task.

| Capability | Current implemented scope | Evidence |
| --- | --- | --- |
| Source ingestion | Podcast RSS, X video and YouTube video; local audio/transcript paths; X/YouTube MCP previews may read public network metadata | specs 002,036,039-041; mcp_tools_x_video.py, mcp_tools_youtube_video.py |
| Summaries | Deterministic extraction; opt-in semantic summaries with finance/learning-notes profiles and review guards | specs 006,015,037; semantic_summarizer.py, summary_profiles.py |
| Search and corpus state | SQLite metadata/transcript/mention search; local artifact index, remediation plan and bounded stage runners | specs 003,008-017; corpus_index.py; mcp_tools_corpus_workflows.py |
| Research reports | Deterministic research/stock lens; latest and named verified reports; catalog, source revalidation, coverage, historical next-step and gap backlog | specs 004-005,018-024,035; mcp_tools_verified_report_queries.py, mcp_tools_stock_lens.py |
| Learning lecture | 00 cover + 03 full summary + 04 learning notes + 07 guide from learning-notes semantic summary; generation/reuse/cover-only; append-only Tool26 | specs 038,044; study_guide_bundle.py; mcp_tools_study_guide.py |
| Workflow derivation | Separate 05 prompt examples + 06 apply-to-my-workflow from lecture and operator context; generation/reuse; Tool25 | specs 042-043; workflow_derivation.py |
| Agent execution guidance | Two separate learning Skills: preview, explicit approval, one confirm, stop; conditional exact cost ack | spec045; .agents/skills/study-guide-bundle and workflow-derivation-bundle |
| Publication safeguards | Byte-preserving non-owned files, unsafe/recovery refusal, bounded reads and fixed public error outcomes | specs 044,046; test_study_guide_bundle.py, test_workflow_derivation_safety.py |

Both transport entry points share the reviewed MCP registry. At planning time, the live count was26; the authorized implementation appends Tool27. Existing human confirmation, exact LLM cost acknowledgement, no-investment-advice and manual-cache boundaries remain. Learning artifacts are not ARTIFACT_LADDER stages.

## Proposed priorities

| Priority | Candidate | User value | Scope decision |
| --- | --- | --- | --- |
| Current: SPEC047 | Learning workflow next-step query | One named episode yields one safe next preview or a blocker | Core + one read-query MCP; implemented and offline-verified |
| Later, unnumbered | Source/lecture/context lineage and currentness | Distinguish reusable files from outputs derived from current sources | Requires own digest/provenance/migration spec; no hash backfill automatically |
| Later, unnumbered | Explicit recovery diagnosis and operator runbook | Explain retained backup/staging states without risky retry | Read-only diagnosis before considering any restoration/cleanup executor |
| Later, unnumbered | Learning catalog/search or UI | Navigate many episodes and generated lessons | Requires bounded inventory/index and artifact visibility design |
| Deferred | Multi-stage automation, scheduling and batch generation | Fewer manual steps | New authorization/cost/partial-failure policy; not part of047 |

Deferred or not approved: source freshness for lecture/05/06, Web UI, scheduler, embeddings/vector search, live market API. Existing verified-report source revalidation is a separate report capability and must not be presented as learning-artifact freshness.

Delivery order:047 makes the existing safe operations easier to discover; a later learning-lineage spec can address freshness if prioritized. Automatic execution is not necessary for the next-step query. This plan does not reserve future spec numbers.

SPEC047 closeout: live registry27, full regression1960 passed/26 native-symlink skips, no pending convergence tasks. This adds the next-step query; the deferred candidates above remain unapproved future scope.
