"""No raw transcript / no secret stdout guards for LLM-facing CLIs (B2-T5).

Invariants protected:
- Dry-run stdout/stderr of LLM-facing CLIs never contains raw transcript
  text, API key values, or prompt/LLM-response content.
- The semantic summarize CLI prints only path/count metadata (a locked JSON
  key set), so transcript or prompt content cannot be added to stdout
  silently.

All providers are mocked or never constructed (dry-run); no external LLM is
called and ``.env`` is never read (tests use ``--no-env-file`` plus
``monkeypatch.setenv`` fake values).
"""

from __future__ import annotations

import json
import sys

import pytest

from tests.test_research_workflow import _use_tmp_data_dirs

ACK = (
    "I understand this may call an external LLM API, send transcript text outside this machine, "
    "and incur costs."
)
TRANSCRIPT_MARKER = "UNIQUE-TRANSCRIPT-MARKER-93117"
FAKE_KEY_VALUE = "fake-key-value-71249"


def _write_marker_transcript(monkeypatch, tmp_path, *, podcast_id="gooaye", episode_ref="EP672"):
    from corpus_ingest_core.storage import transcript_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    title = f"{episode_ref} title"
    segments = [
        {"id": 1, "start": 10.0, "end": 20.0, "text": f"開場提到 {TRANSCRIPT_MARKER} 的內容。"},
        {"id": 2, "start": 30.0, "end": 40.0, "text": "接著聊市場情緒與供需。"},
    ]
    paths = transcript_asset_paths(podcast_id, episode_ref, title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text(
        "\n".join(segment["text"] for segment in segments), encoding="utf-8"
    )
    paths.srt_path.write_text("1\n00:00:10,000 --> 00:00:20,000\n字幕\n", encoding="utf-8")
    paths.json_path.write_text(
        json.dumps(
            {
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "title": title,
                "language": "zh",
                "segment_count": len(segments),
                "completed": True,
                "generated_at": "2026-06-28T00:00:00Z",
                "source_audio_path": "data/audio/gooaye/EP672__EP672.mp3",
                "source_audio_size_bytes": 123,
                "segments": segments,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return paths


def test_summarize_cli_semantic_stdout_is_metadata_only(monkeypatch, tmp_path, capsys):
    from scripts import summarize_episode as cli

    from tests.test_semantic_summary_smoke import _summary_asset

    monkeypatch.setenv("API_KEY", FAKE_KEY_VALUE)
    monkeypatch.setattr(
        cli, "semantic_summarize_episode", lambda *args, **kwargs: _summary_asset(tmp_path)
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "summarize_episode.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--mode",
            "semantic",
            "--no-env-file",
            "--api-cost-ack",
            ACK,
        ],
    )

    cli.main()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    # Locked stdout schema: path/count metadata only. Adding a field that could
    # carry transcript, prompt, or LLM response text must fail this test.
    assert set(payload) == {
        "podcast_id",
        "episode_ref",
        "title",
        "summary_path",
        "transcript_json_path",
        "transcript_text_path",
        "segment_count",
        "summary_mode",
        "generated",
        "already_exists",
        "provider",
        "model",
        "chunk_count",
        "evidence_count",
        "local_env",
    }
    assert payload["summary_mode"] == "semantic-llm"
    combined_output = captured.out + captured.err
    assert FAKE_KEY_VALUE not in combined_output
    assert TRANSCRIPT_MARKER not in combined_output


def test_semantic_smoke_dry_run_does_not_leak_transcript_text(
    monkeypatch, tmp_path, capsys
):
    from scripts import run_semantic_summary_smoke as smoke

    _write_marker_transcript(monkeypatch, tmp_path)
    monkeypatch.setenv("API_KEY", FAKE_KEY_VALUE)
    monkeypatch.setattr(
        smoke,
        "semantic_summarize_episode",
        lambda *args, **kwargs: pytest.fail("dry-run must not execute the semantic summary"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_semantic_summary_smoke.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--model",
            "GB10",
            "--api-key-env",
            "API_KEY",
            "--no-env-file",
        ],
    )

    smoke.main()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["dry_run"] is True
    assert payload["transcript_status"] == "valid"
    combined_output = captured.out + captured.err
    assert TRANSCRIPT_MARKER not in combined_output
    assert FAKE_KEY_VALUE not in combined_output


def test_research_smoke_dry_run_does_not_leak_transcript_text(
    monkeypatch, tmp_path, capsys
):
    from scripts import run_research_llm_smoke as smoke

    _write_marker_transcript(monkeypatch, tmp_path)
    monkeypatch.setenv("API_KEY", FAKE_KEY_VALUE)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_research_llm_smoke.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--stock",
            "台積電",
            "--model",
            "GB10",
            "--no-env-file",
        ],
    )

    smoke.main()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["dry_run"] is True
    combined_output = captured.out + captured.err
    assert TRANSCRIPT_MARKER not in combined_output
    assert FAKE_KEY_VALUE not in combined_output

def test_corpus_semantic_cli_uncontained_error_is_category_only(monkeypatch, capsys):
    from scripts import run_corpus_semantic_remediation as cli

    monkeypatch.setattr(
        cli,
        "run_corpus_semantic_remediation",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError(
                "raw transcript prompt text raw response semantic body "
                "https://endpoint.invalid/?token=secret sk-test-secret-value Traceback"
            )
        ),
    )
    monkeypatch.setattr(
        cli.sys,
        "argv",
        [
            "run_corpus_semantic_remediation.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP700",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main()
    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert captured.out == ""
    assert "RuntimeError" in captured.err
    for forbidden in (
        "raw transcript",
        "prompt text",
        "raw response",
        "semantic body",
        "endpoint.invalid",
        "token=secret",
        "sk-test-secret-value",
        "Traceback",
    ):
        assert forbidden not in captured.err


def test_completion_cli_uncontained_error_is_category_only(monkeypatch, capsys):
    from scripts import run_corpus_episode_completion_workflow as cli

    monkeypatch.setattr(
        cli,
        "run_corpus_episode_completion_workflow",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError(
                "raw transcript prompt text raw response semantic body "
                "https://endpoint.invalid/?token=secret sk-test-secret-value Traceback"
            )
        ),
    )

    status = cli.main(["--podcast", "gooaye"])
    captured = capsys.readouterr()

    assert status == 1
    assert captured.out == ""
    assert "RuntimeError" in captured.err
    for forbidden in (
        "raw transcript",
        "prompt text",
        "raw response",
        "semantic body",
        "endpoint.invalid",
        "token=secret",
        "sk-test-secret-value",
        "Traceback",
    ):
        assert forbidden not in captured.err
