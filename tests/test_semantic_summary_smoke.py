from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ACK = "I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."


def _summary_asset(tmp_path: Path):
    from corpus_ingest_core.models import SummaryAsset

    return SummaryAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        summary_path=tmp_path / "EP672__EP672 title.semantic.md",
        transcript_json_path=tmp_path / "EP672.json",
        transcript_text_path=tmp_path / "EP672.txt",
        segment_count=2,
        summary_mode="semantic-llm",
        generated=True,
        already_exists=False,
        provider="openai-compatible",
        model="GB10",
        chunk_count=1,
        evidence_count=1,
    )


def test_semantic_summary_smoke_dry_run_writes_nothing_and_exposes_no_secret(monkeypatch, tmp_path, capsys):
    from scripts import run_semantic_summary_smoke

    from corpus_ingest_core.models import TranscriptValidationResult

    monkeypatch.setenv("API_KEY", "secret-value")
    monkeypatch.setattr(
        run_semantic_summary_smoke,
        "validate_transcript",
        lambda *args, **kwargs: TranscriptValidationResult(
            podcast_id="gooaye",
            episode_ref="EP672",
            valid=True,
            status="valid",
            segment_count=2,
            last_segment_end_seconds=120.0,
            transcript_text_length=500,
            problems=[],
            warnings=[],
            paths={"json": "data/transcripts/gooaye/EP672__title.json"},
        ),
    )
    monkeypatch.setattr(
        run_semantic_summary_smoke,
        "semantic_summarize_episode",
        lambda *args, **kwargs: pytest.fail("semantic summary must not run in dry-run"),
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

    run_semantic_summary_smoke.main()

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["dry_run"] is True
    assert payload["transcript_status"] == "valid"
    assert payload["requires_api_cost_ack"] is True
    assert payload["required_acknowledgement"] == ACK
    assert payload["provider_config"]["model"] == "GB10"
    assert payload["provider_config"]["api_key_env"] == "API_KEY"
    assert payload["provider_config"]["api_key_value_exposed"] is False
    assert payload["api_key_value_read"] is False
    assert "secret-value" not in output
    assert "raw transcript" not in output.lower()


def test_semantic_summary_smoke_confirm_requires_exact_ack_before_execution(monkeypatch, capsys):
    from scripts import run_semantic_summary_smoke

    monkeypatch.setattr(
        run_semantic_summary_smoke,
        "semantic_summarize_episode",
        lambda *args, **kwargs: pytest.fail("semantic summary must not run without ack"),
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
            "--confirm",
            "--api-cost-ack",
            "wrong",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        run_semantic_summary_smoke.main()

    assert exc_info.value.code == 1
    assert "exact api_cost_ack" in capsys.readouterr().err


def test_semantic_summary_smoke_confirm_runs_semantic_summary_with_profile_and_env(monkeypatch, tmp_path, capsys):
    from scripts import run_semantic_summary_smoke

    env_path = tmp_path / ".env"
    env_path.write_text("API_KEY=secret-value\nMODEL=env-model\n", encoding="utf-8")
    profile_path = tmp_path / "llm_profiles.yaml"
    profile_path.write_text(
        """
profiles:
  gb10:
    provider: openai-compatible
    model: GB10
    base_url: https://api.example.com/v1
    api_key_env: API_KEY
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    calls = []

    def fake_semantic(*args, **kwargs):
        calls.append((args, kwargs, os.environ.get("API_KEY")))
        progress_callback = kwargs.get("progress_callback")
        assert progress_callback is not None
        progress_callback("chunk_count", chunk_count=2, llm_requests=3)
        progress_callback("chunk_start", index=1, total=2)
        progress_callback("chunk_done", index=1, total=2)
        progress_callback("final_start")
        progress_callback("final_done")
        return _summary_asset(tmp_path)

    monkeypatch.setattr(run_semantic_summary_smoke, "semantic_summarize_episode", fake_semantic)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_semantic_summary_smoke.py",
            "--podcast",
            "gooaye",
            "--episode",
            "EP672",
            "--confirm",
            "--force",
            "--allow-partial",
            "--llm-profile",
            "gb10",
            "--llm-profile-path",
            str(profile_path),
            "--env-file",
            str(env_path),
            "--chunk-seconds",
            "300",
            "--max-segments-per-chunk",
            "50",
            "--api-cost-ack",
            ACK,
        ],
    )

    run_semantic_summary_smoke.main()

    captured = capsys.readouterr()
    output = captured.out
    stderr = captured.err
    payload = json.loads(output)
    args, kwargs, api_key = calls[0]
    assert args == ("gooaye", "EP672")
    assert api_key == "secret-value"
    assert kwargs["progress_callback"] is not None
    kwargs_without_callback = dict(kwargs)
    kwargs_without_callback.pop("progress_callback")
    assert kwargs_without_callback == {
        "api_cost_ack": ACK,
        "provider": "openai-compatible",
        "model": "GB10",
        "base_url": "https://api.example.com/v1",
        "api_key_env": "API_KEY",
        "force": True,
        "chunk_seconds": 300,
        "max_segments_per_chunk": 50,
        "allow_partial": True,
    }
    assert payload["dry_run"] is False
    assert payload["summary"]["summary_mode"] == "semantic-llm"
    assert payload["local_env"]["loaded_env_var_names"] == ["API_KEY", "MODEL"]
    assert "secret-value" not in output
    assert "semantic_summary_progress: chunk_count=2 llm_requests=3" in stderr
    assert "semantic_summary_progress: chunk 1/2 start" in stderr
    assert "semantic_summary_progress: chunk 1/2 done" in stderr
    assert "semantic_summary_progress: final_summary start" in stderr
    assert "semantic_summary_progress: final_summary done" in stderr
    assert "secret-value" not in stderr
    assert "raw transcript" not in stderr.lower()
