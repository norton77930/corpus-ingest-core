# Latest Episode Deterministic Workflow Contract

## Core

```python
run_corpus_latest_episode_deterministic_workflow(
    podcast_id: str,
    *,
    confirm: bool = False,
    transcription_model: str | None = None,
    transcription_device: str = "cpu",
    transcription_compute_type: str = "int8",
    transcription_vad_filter: bool = False,
) -> CorpusLatestEpisodeDeterministicWorkflowRunResult
```

- `confirm=False` is a strict zero-write preview.
- `confirm=True` is required before intake, network download, local compute, or
  deterministic artifact writes.
- The runner accepts no explicit episode ref, semantic option, provider option,
  credential option, force, partial, retry, batch, or scheduler option.

## MCP

```text
run_corpus_latest_episode_deterministic_workflow(
  podcast_id,
  confirm=false,
  transcription_model=null,
  transcription_device="cpu",
  transcription_compute_type="int8",
  transcription_vad_filter=false
)
```

The tool is the fourteenth reviewed stdio MCP tool. It returns the existing
success/error envelope; its dry-run response includes the existing confirmation
envelope fields. The wrapper exposes exactly the core's local options and no
semantic/provider/credential settings.

## CLI

```powershell
python scripts/run_corpus_latest_episode_deterministic_workflow.py --podcast gooaye
python scripts/run_corpus_latest_episode_deterministic_workflow.py --podcast gooaye --confirm
```

The CLI prints metadata-only JSON, returns non-zero only for invalid input or
uncontained runner failure, and never loads local environment configuration.

## Portable Skill

`corpus-latest-episode-processing` recognizes an unambiguous request to process
one configured podcast's latest episode. It responds with one short start
acknowledgement, calls only this MCP tool with `confirm=true`, then gives one
bounded final report. Missing tool setup is reported as a setup problem; no
terminal, CLI, retry, or alternate tool fallback is permitted.
