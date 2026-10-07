# Source learning entry usage and acceptance

## Operator prerequisites

Mount the existing repo MCP server and install/reload complete source-learning-entry, source-preparation and source-content-qa Skill folders with all references. Keep the single source-content-qa/references/learning-notes-template.md as the editable default. No new MCP tool or model parameter is added. Use the repository venv for development checks. An already prepared source can be read over stdio; Windows stdio new submissions stop with worker_host_incompatible. New preparation requires an already independently managed compatible HTTP host; the Skill never launches or configures it.

## Natural requests

- URL entry:「幫我整理這支影片的學習筆記，把討論的問題、理由和例子講清楚，標示回聽段落。」附一個 YouTube/X 連結。
- Known prepared source:「整理 x-natewiki / 2106893534980685927 的整集學習筆記。」
- After submission:「處理好了嗎？」只查一次狀態。
- After readiness:「繼續整理剛才的學習筆記。」在同一段對話沿用原需求；若上下文遺失，補上 job_id 或已知 IDs 與需求。
- Single-use preferences override the editable template; project application is omitted unless requested.

URL preview can read public metadata even for an existing transcript. If metadata is unavailable, stop instead of guessing IDs; known explicit prepared IDs can use the independent offline QA route. Accepted means submitted, never notes complete. Keep the source/episode/job reference from the reply for later continuation.

## Developer acceptance

Run pytest on test_source_learning_entry_skill.py and test_spec_057_source_learning_docs.py, then existing source-preparation/QA/registry/docs guards and standard full checks. Use short unused workspace-contained basetemp paths. Log developer instruction/resource/backend checks and synthetic probes separately from actual host execution. The isolated existing X source is in .pytest-tmp/54m/data; an owned pilot may inspect/read it with input hashes preserved, without transcription/provider/network/cache operations.

## Actual Hermes acceptance — pending

No accessible Hermes executable or callable host capability was found here; live acceptance is pending, not passed. With the operator's already configured host and selected data root, record actual tool trace and output for: ready explicit-ID notes; same-video URL ready entry; status-only ready stopping; explicit same-conversation learning continuation; interrupted/budget-limited reading. Validate exact source/job binding, versions/pages, actual coverage, source reasoning/AI labels, omitted project application and unchanged input hashes. URL preview needs network; host inference follows its configured privacy/billing. New live-source preparation additionally requires compatible managed HTTP hosting and fresh displayed-plan submission consent.

Do not print credentials/settings or raw transcripts into committed logs. Store only safe acceptance metadata and user-reviewable notes in operator-approved local locations. A synthetic dialogue or SDK trace is not Hermes acceptance. Keep the live task unchecked until real host trace/output is supplied.
