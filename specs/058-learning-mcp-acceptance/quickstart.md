# Local acceptance and Hermes handoff

Use the existing repo venv. No service installation, configuration change or source copying is part of verification.

## Local prepared-source checks

```powershell
.\.venv\Scripts\python.exe scripts/verify_learning_mcp.py inventory
.\.venv\Scripts\python.exe scripts/verify_learning_mcp.py verify --data-dir .pytest-tmp/54m/data --podcast x-natewiki --episode 2106893534980685927 --start 600 --end 674
```

The existing X data is an isolated developer pilot, not shipped corpus. Choose your own data root explicitly. A wrong root reports source_missing, without copying data, repairing paths or rebuilding cache. Owned stdio is a separate developer server, not the currently mounted host. To check an already managed server use --mcp-url http://127.0.0.1:8765/mcp instead of --data-dir; this is an example address, not an instruction to create a listener. No raw transcript output. Redirection to a new operator-owned file saves a receipt; never overwrite historical receipts.

## VM handoff

`scope_complete=true` certifies only delivery of the selected time range. Whole-source understanding, human replay and actual Hermes execution remain separate outcomes.

1. Record the delivered revision and runtime/SDK versions. Current developer validation uses Python3.12.9 and MCP SDK1.28.1. Select a revision containing the SPEC044–058 delivery: an older main/HEAD does not include these learning features. Confirm scripts/verify_learning_mcp.py, the required Skill resources and the actual registry after updating. Use the operator-managed Python environment; the verifier performs no installation or commit.
2. Inventory and copy/reload all source-learning-entry, source-preparation, source-content-qa folders with every reference. Preserve source-content-qa/references/learning-notes-template.md as the single editable template. Inventory verifies resources, not host loading.
3. Select the actual server's data root explicitly (CORPUS_INGEST_DATA_DIR); keep IDs unchanged. Do not assume the local pilot exists on the VM. Copy intended corpus only as a separately authorized operator action; never copy .env/credentials/complete host settings.
4. Confirm configured ASR model/device/compute and available hardware. Current local pilot recorded medium/cuda/float16/VAD=true; VM readiness must be checked separately. No tiny/CPU downgrade is authorized silently. Host model privacy/billing is separate from local transcription.
5. Use an already configured compatible transport. Windows stdio reads prepared content but new background submissions stop worker_host_incompatible; compatible independently managed HTTP is required. The verifier starts no HTTP service. Hermes should expose the three native tools prepare_learning_source, inspect_source_preparation_job, query_source_content from the same server; verify the installed Hermes filtering syntax against its own version.
6. Run the local utility beside the existing VM server, then record actual Hermes requests/tool trace/output. A utility receipt is not actual Hermes acceptance.

Complete current Skill resources (copy whole folders, not just these filenames):

| Folder | Required resources |
|---|---|
| source-learning-entry | SKILL.md; references/entry-protocol.md |
| source-preparation | SKILL.md; references/response-contract.md |
| source-content-qa | SKILL.md; references/response-contract.md; references/learning-notes-template.md |

The inventory checks transitive Markdown references and rejects secret/non-Markdown links before reading. Missing resources prevent readiness. This is a local inventory, not proof Hermes has reloaded the same folders.

## Live cases — pending operator execution

- Prepared IDs: ask the TDD question; fresh inspect/pinned read and source/AI distinctions.
- Same ready URL: one metadata preview then QA; no preparation job.
- New configured URL: one preview, disclose model/download/resource effects, obtain fresh source/plan-bound approval, one confirmation; record job/reference and stop.
- 「處理好了嗎？」: one job status call and stop, including when ready.
- 「繼續整理」: retained same-conversation request/job/source match, ready then fresh QA. Lost context clarifies; another source's busy job does not attach.
- Limited budget/source drift: partial/stop, never whole-source claim.

No implicit consent from this spec to download/transcribe a new URL or invoke a host provider. Live preparation needs accessible compatible hosting and fresh displayed-plan approval. Actual Hermes needs its accessible already configured host. Keep SPEC057 T017/T018 pending until genuine traces are supplied. Use [content-acceptance.md](content-acceptance.md); repository developer logs store metadata only, not raw transcript/settings.

## Current long-source budget (SPEC059)

Default --max-total-chars is now120000 rather than the original60000. Call/timeout bounds still apply; choose explicit bounded budgets/ranges for longer sources and retain partial reporting when exhausted. The verifier does not retry. See [SPEC059](../059-source-learning-reliability/quickstart.md) for Skill recovery/discovery/note-quality validation.