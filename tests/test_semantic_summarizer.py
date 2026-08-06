from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from podcast_ingest_core import storage

    monkeypatch.setattr(storage, "TRANSCRIPTS_DIR", tmp_path / "transcripts")
    monkeypatch.setattr(storage, "SUMMARIES_DIR", tmp_path / "summaries")


def _write_transcript(
    monkeypatch,
    tmp_path,
    *,
    podcast_id="gooaye",
    episode_ref="EP672",
    title="EP672 title",
    segments=None,
    segment_count=None,
    completed=True,
):
    from podcast_ingest_core.storage import transcript_asset_paths

    _use_tmp_data_dirs(monkeypatch, tmp_path)
    if segments is None:
        segments = [
            {"id": 1, "start": 0.0, "end": 10.0, "text": "第一段提到市場。"},
            {"id": 2, "start": 620.0, "end": 640.0, "text": "第二段提到公司。"},
            {"id": 3, "start": 1250.0, "end": 1270.0, "text": "第三段提到生活。"},
        ]
    if segment_count is None:
        segment_count = len(segments)

    paths = transcript_asset_paths(podcast_id, episode_ref, title)
    paths.text_path.parent.mkdir(parents=True, exist_ok=True)
    paths.text_path.write_text(
        "\n".join(segment["text"] for segment in segments), encoding="utf-8"
    )
    paths.srt_path.write_text(
        "\n".join(f"{index}\n00:00:00,000 --> 00:00:01,000\n{segment['text']}\n" for index, segment in enumerate(segments, start=1)),
        encoding="utf-8",
    )
    payload = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "title": title,
        "language": "zh",
        "text_path": str(paths.text_path),
        "srt_path": str(paths.srt_path),
        "json_path": str(paths.json_path),
        "segment_count": segment_count,
        "completed": completed,
        "segments": segments,
    }
    paths.json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return paths


class FakeProvider:
    def __init__(self):
        self.chunk_calls = []
        self.final_calls = []

    def summarize_chunk(self, chunk):
        self.chunk_calls.append(chunk)
        return f"### Chunk {chunk['index']}\n- 重點 `[{chunk['start_time']} - {chunk['end_time']}]`"

    def summarize_final(self, *, podcast_display_name, episode_ref, title, chunk_summaries):
        self.final_calls.append(
            {
                "podcast_display_name": podcast_display_name,
                "episode_ref": episode_ref,
                "title": title,
                "chunk_summaries": chunk_summaries,
            }
        )
        return "## 本集主題\n\n- 語意摘要 `[00:00:00 - 00:00:10]`"


def test_semantic_summarizer_calls_validation_before_provider(monkeypatch, tmp_path):
    import podcast_ingest_core.semantic_summarizer as semantic_summarizer

    _write_transcript(monkeypatch, tmp_path)
    provider = FakeProvider()
    called = []
    original_validate = semantic_summarizer.validate_transcript

    def wrapped_validate(*args, **kwargs):
        called.append("validate")
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(semantic_summarizer, "validate_transcript", wrapped_validate)
    monkeypatch.setattr(semantic_summarizer, "_build_provider", lambda **kwargs: provider)

    semantic_summarizer.semantic_summarize_episode(
        "gooaye",
        "EP672",
        api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        model="test-model",
    )

    assert called == ["validate"]
    assert len(provider.chunk_calls) == 3


def test_semantic_summarizer_chunks_segments_by_time(monkeypatch, tmp_path):
    import podcast_ingest_core.semantic_summarizer as semantic_summarizer

    _write_transcript(monkeypatch, tmp_path)
    provider = FakeProvider()
    monkeypatch.setattr(semantic_summarizer, "_build_provider", lambda **kwargs: provider)

    asset = semantic_summarizer.semantic_summarize_episode(
        "gooaye",
        "EP672",
        api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        model="test-model",
        chunk_seconds=600,
    )

    assert asset.summary_mode == "semantic-llm"
    assert asset.chunk_count == 3
    assert [chunk["index"] for chunk in provider.chunk_calls] == [1, 2, 3]
    assert provider.chunk_calls[0]["segment_ids"] == [1]
    assert provider.chunk_calls[1]["segment_ids"] == [2]
    assert provider.chunk_calls[2]["segment_ids"] == [3]


def test_semantic_summarizer_chunks_segments_by_max_segments(monkeypatch, tmp_path):
    import podcast_ingest_core.semantic_summarizer as semantic_summarizer

    segments = [
        {"id": 1, "start": 0.0, "end": 1.0, "text": "a"},
        {"id": 2, "start": 2.0, "end": 3.0, "text": "b"},
        {"id": 3, "start": 4.0, "end": 5.0, "text": "c"},
    ]
    _write_transcript(monkeypatch, tmp_path, segments=segments)
    provider = FakeProvider()
    monkeypatch.setattr(semantic_summarizer, "_build_provider", lambda **kwargs: provider)

    asset = semantic_summarizer.semantic_summarize_episode(
        "gooaye",
        "EP672",
        api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        model="test-model",
        chunk_seconds=600,
        max_segments_per_chunk=2,
    )

    assert asset.chunk_count == 2
    assert provider.chunk_calls[0]["segment_ids"] == [1, 2]
    assert provider.chunk_calls[1]["segment_ids"] == [3]


def test_semantic_summarizer_writes_semantic_markdown(monkeypatch, tmp_path):
    import podcast_ingest_core.semantic_summarizer as semantic_summarizer

    _write_transcript(monkeypatch, tmp_path)
    provider = FakeProvider()
    monkeypatch.setattr(semantic_summarizer, "_build_provider", lambda **kwargs: provider)

    asset = semantic_summarizer.semantic_summarize_episode(
        "gooaye",
        "EP672",
        api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        model="test-model",
    )

    content = asset.summary_path.read_text(encoding="utf-8")
    assert asset.generated is True
    assert asset.provider == "openai-compatible"
    assert asset.model == "test-model"
    assert asset.evidence_count == 1
    assert asset.summary_path.name.endswith(".semantic.md")
    assert "Summary mode: semantic-llm" in content
    assert "本摘要不構成投資建議" in content
    assert "## Chunk Summaries" in content


def test_semantic_summarizer_generates_empty_summary_without_provider(monkeypatch, tmp_path):
    import podcast_ingest_core.semantic_summarizer as semantic_summarizer

    _write_transcript(
        monkeypatch,
        tmp_path,
        episode_ref="smoke-test",
        title="smoke-test",
        segments=[],
        segment_count=0,
    )
    provider = FakeProvider()
    monkeypatch.setattr(
        semantic_summarizer,
        "_build_provider",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("provider should not be used")),
    )

    asset = semantic_summarizer.semantic_summarize_episode(
        "gooaye",
        "smoke-test",
        api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        model="test-model",
    )

    content = asset.summary_path.read_text(encoding="utf-8")
    assert asset.generated is True
    assert asset.chunk_count == 0
    assert provider.chunk_calls == []
    assert "此 transcript 沒有可摘要的語音 segments。" in content


def test_semantic_summarizer_rejects_partial_by_default(monkeypatch, tmp_path):
    import podcast_ingest_core.semantic_summarizer as semantic_summarizer
    from podcast_ingest_core.errors import TranscriptParseError

    _write_transcript(monkeypatch, tmp_path, completed=False)
    monkeypatch.setattr(
        semantic_summarizer,
        "_build_provider",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("provider should not be used")),
    )

    with pytest.raises(TranscriptParseError, match="partial"):
        semantic_summarizer.semantic_summarize_episode(
            "gooaye",
            "EP672",
            api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
            model="test-model",
        )


def test_semantic_summarizer_allows_partial_when_requested(monkeypatch, tmp_path):
    import podcast_ingest_core.semantic_summarizer as semantic_summarizer

    _write_transcript(monkeypatch, tmp_path, completed=False)
    monkeypatch.setattr(semantic_summarizer, "_build_provider", lambda **kwargs: FakeProvider())

    asset = semantic_summarizer.semantic_summarize_episode(
        "gooaye",
        "EP672",
        api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        model="test-model",
        allow_partial=True,
    )

    assert asset.generated is True
    assert "Transcript status: partial" in asset.summary_path.read_text(encoding="utf-8")


def test_semantic_summarizer_missing_api_key_raises_config_error(monkeypatch, tmp_path):
    import podcast_ingest_core.semantic_summarizer as semantic_summarizer
    from podcast_ingest_core.errors import LLMProviderConfigError

    _write_transcript(monkeypatch, tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "test-model")

    with pytest.raises(LLMProviderConfigError, match="OPENAI_API_KEY"):
        semantic_summarizer.semantic_summarize_episode(
            "gooaye",
            "EP672",
            api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        )


def test_openai_provider_request_failure_raises_request_error(monkeypatch):
    from podcast_ingest_core.errors import LLMProviderRequestError
    from podcast_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class Response:
        status_code = 500
        text = "server error"

        def json(self):
            return {}

    def fake_post(*args, **kwargs):
        return Response()

    import podcast_ingest_core.llm_provider as llm_provider

    monkeypatch.setattr(llm_provider.requests, "post", fake_post)
    # Batch 3C: construct only via create_provider (exact ack + factory token).
    provider = create_provider(
        "openai-compatible",
        model="test-model",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    with pytest.raises(LLMProviderRequestError, match="500"):
        provider.complete([{"role": "user", "content": "hi"}])


def test_openai_provider_prefers_generic_model_and_base_url(monkeypatch):
    from podcast_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("MODEL", "generic-model")
    monkeypatch.setenv("BASE_URL", "https://generic.example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "legacy-model")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://legacy.example.test/v1")

    provider = create_provider(
        "openai-compatible",
        api_key_env="API_KEY",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert provider.model == "generic-model"
    assert provider.base_url == "https://generic.example.test/v1"


def test_openai_provider_falls_back_to_legacy_openai_model_and_base_url(monkeypatch):
    from podcast_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.delenv("BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "legacy-model")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://legacy.example.test/v1")

    provider = create_provider(
        "openai-compatible",
        api_key_env="API_KEY",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert provider.model == "legacy-model"
    assert provider.base_url == "https://legacy.example.test/v1"


def test_summarize_cli_parses_semantic_options(monkeypatch, capsys, tmp_path):
    from podcast_ingest_core.models import SummaryAsset
    from scripts import summarize_episode

    asset = SummaryAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        summary_path=tmp_path / "summary.semantic.md",
        transcript_json_path=tmp_path / "transcript.json",
        transcript_text_path=tmp_path / "transcript.txt",
        segment_count=2,
        summary_mode="semantic-llm",
        generated=True,
        already_exists=False,
        provider="openai-compatible",
        model="test-model",
        chunk_count=1,
        evidence_count=1,
    )
    captured = {}

    def fake_semantic(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return asset

    monkeypatch.setattr(summarize_episode, "semantic_summarize_episode", fake_semantic)
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
            "--provider",
            "openai-compatible",
            "--model",
            "test-model",
            "--base-url",
            "https://example.test/v1",
            "--api-key-env",
            "TEST_API_KEY",
            "--chunk-seconds",
            "600",
            "--max-segments-per-chunk",
            "120",
            "--allow-partial",
            "--force",
            "--api-cost-ack",
            summarize_episode.SEMANTIC_API_COST_ACK,
        ],
    )

    summarize_episode.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["summary_mode"] == "semantic-llm"
    assert payload["provider"] == "openai-compatible"
    assert captured["args"] == ("gooaye", "EP672")
    assert captured["kwargs"] == {
        "api_cost_ack": summarize_episode.SEMANTIC_API_COST_ACK,
        "provider": "openai-compatible",
        "model": "test-model",
        "base_url": "https://example.test/v1",
        "api_key_env": "TEST_API_KEY",
        "force": True,
        "chunk_seconds": 600,
        "max_segments_per_chunk": 120,
        "allow_partial": True,
    }


def test_summarize_cli_semantic_mode_requires_exact_ack_before_provider(monkeypatch, capsys):
    from scripts import summarize_episode

    monkeypatch.setattr(
        summarize_episode,
        "semantic_summarize_episode",
        lambda *args, **kwargs: pytest.fail("semantic summary must not run without ack"),
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
            "--api-cost-ack",
            "wrong",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        summarize_episode.main()

    assert exc_info.value.code == 1
    assert "exact api_cost_ack" in capsys.readouterr().err


def test_summarize_cli_loads_env_file_for_semantic_mode(monkeypatch, capsys, tmp_path):
    from podcast_ingest_core.models import SummaryAsset
    from scripts import summarize_episode

    env_path = tmp_path / ".env"
    env_path.write_text("API_KEY=secret-value\nMODEL=file-model\n", encoding="utf-8")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    asset = SummaryAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 title",
        summary_path=tmp_path / "summary.semantic.md",
        transcript_json_path=tmp_path / "transcript.json",
        transcript_text_path=tmp_path / "transcript.txt",
        segment_count=2,
        summary_mode="semantic-llm",
        generated=True,
        already_exists=False,
        provider="openai-compatible",
        model="file-model",
        chunk_count=1,
        evidence_count=1,
    )
    captured = {}

    def fake_semantic(*args, **kwargs):
        captured["kwargs"] = kwargs
        captured["api_key"] = os.environ.get("API_KEY")
        return asset

    monkeypatch.setattr(summarize_episode, "semantic_summarize_episode", fake_semantic)
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
            "--env-file",
            str(env_path),
            "--api-key-env",
            "API_KEY",
            "--api-cost-ack",
            summarize_episode.SEMANTIC_API_COST_ACK,
        ],
    )

    summarize_episode.main()

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert captured["api_key"] == "secret-value"
    assert captured["kwargs"]["api_key_env"] == "API_KEY"
    assert payload["local_env"]["loaded_env_var_names"] == ["API_KEY", "MODEL"]
    assert "secret-value" not in output
