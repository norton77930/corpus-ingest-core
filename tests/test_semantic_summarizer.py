from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest


def _use_tmp_data_dirs(monkeypatch, tmp_path):
    from corpus_ingest_core import storage

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
    from corpus_ingest_core.storage import transcript_asset_paths

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
    import corpus_ingest_core.semantic_summarizer as semantic_summarizer

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


def test_semantic_summarizer_forwards_reasoning_effort_to_provider(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.semantic_summarizer as semantic_summarizer

    _write_transcript(monkeypatch, tmp_path)
    provider = FakeProvider()
    captured = {}

    def fake_build_provider(**kwargs):
        captured.update(kwargs)
        return provider

    monkeypatch.setattr(semantic_summarizer, "_build_provider", fake_build_provider)

    semantic_summarizer.semantic_summarize_episode(
        "gooaye",
        "EP672",
        api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        model="test-model",
        reasoning_effort="max",
    )

    assert captured["reasoning_effort"] == "max"


def test_semantic_summarizer_chunks_segments_by_time(monkeypatch, tmp_path):
    import corpus_ingest_core.semantic_summarizer as semantic_summarizer

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
    import corpus_ingest_core.semantic_summarizer as semantic_summarizer

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
    import corpus_ingest_core.semantic_summarizer as semantic_summarizer

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
    import corpus_ingest_core.semantic_summarizer as semantic_summarizer

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
    import corpus_ingest_core.semantic_summarizer as semantic_summarizer
    from corpus_ingest_core.errors import TranscriptParseError

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
    import corpus_ingest_core.semantic_summarizer as semantic_summarizer

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
    import corpus_ingest_core.semantic_summarizer as semantic_summarizer
    from corpus_ingest_core.errors import LLMProviderConfigError

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
    from corpus_ingest_core.errors import LLMProviderRequestError
    from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class Response:
        status_code = 500
        text = "server error"

        def json(self):
            return {}

    def fake_post(*args, **kwargs):
        return Response()

    import corpus_ingest_core.llm_provider as llm_provider

    monkeypatch.setattr(llm_provider.requests, "post", fake_post)
    # Batch 3C: construct only via create_provider (exact ack + factory token).
    provider = create_provider(
        "openai-compatible",
        model="test-model",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    with pytest.raises(LLMProviderRequestError, match="500"):
        provider.complete([{"role": "user", "content": "hi"}])


def test_openai_provider_omits_reasoning_effort_by_default(monkeypatch):
    from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    captured = {}

    class Response:
        status_code = 200
        text = "ok"

        def json(self):
            return {"choices": [{"message": {"content": "done"}}]}

    def fake_post(*args, **kwargs):
        captured["json"] = kwargs["json"]
        captured["timeout"] = kwargs["timeout"]
        return Response()

    import corpus_ingest_core.llm_provider as llm_provider

    monkeypatch.setattr(llm_provider.requests, "post", fake_post)
    messages = [{"role": "user", "content": "hi"}]
    provider = create_provider(
        "openai-compatible",
        model="test-model",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert provider.complete(messages) == "done"
    assert captured["json"] == {
        "model": "test-model",
        "messages": messages,
    }
    assert captured["timeout"] == (10, 120)


def test_openai_provider_uses_requested_read_timeout(monkeypatch):
    from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    captured = {}

    class Response:
        status_code = 200
        text = "ok"

        def json(self):
            return {"choices": [{"message": {"content": "done"}}]}

    def fake_post(*args, **kwargs):
        captured["timeout"] = kwargs["timeout"]
        return Response()

    import corpus_ingest_core.llm_provider as llm_provider

    monkeypatch.setattr(llm_provider.requests, "post", fake_post)
    provider = create_provider(
        "openai-compatible",
        model="test-model",
        read_timeout_seconds=600,
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert provider.complete([{"role": "user", "content": "hi"}]) == "done"
    assert captured["timeout"] == (10, 600)


def test_openai_provider_sends_reasoning_effort_when_requested(monkeypatch):
    from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    captured = {}

    class Response:
        status_code = 200
        text = "ok"

        def json(self):
            return {"choices": [{"message": {"content": "done"}}]}

    def fake_post(*args, **kwargs):
        captured["json"] = kwargs["json"]
        return Response()

    import corpus_ingest_core.llm_provider as llm_provider

    monkeypatch.setattr(llm_provider.requests, "post", fake_post)
    messages = [{"role": "user", "content": "hi"}]
    provider = create_provider(
        "openai-compatible",
        model="test-model",
        reasoning_effort="max",
        api_cost_ack=SEMANTIC_API_COST_ACK,
    )

    assert provider.complete(messages) == "done"
    assert captured["json"] == {
        "model": "test-model",
        "messages": messages,
        "reasoning_effort": "max",
    }


def test_openai_provider_prefers_generic_model_and_base_url(monkeypatch):
    from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

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
    from corpus_ingest_core.llm_provider import SEMANTIC_API_COST_ACK, create_provider

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
    from scripts import summarize_episode

    from corpus_ingest_core.models import SummaryAsset

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
            "--reasoning-effort",
            "max",
            "--read-timeout-seconds",
            "600",
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
        "reasoning_effort": "max",
        "read_timeout_seconds": 600,
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
    from scripts import summarize_episode

    from corpus_ingest_core.models import SummaryAsset

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


# --- Spec 037: summary profiles ---------------------------------------------

_EXPECTED_FINANCE_DOCUMENT = """# Gooaye 股癌 - EP672 語意摘要

## Metadata

- Podcast: Gooaye 股癌
- Podcast ID: gooaye
- Episode: EP672
- Title: EP672 title
- Transcript status: valid
- Segment count: 3
- Last segment end: 1270.00
- Summary mode: semantic-llm
- Provider: openai-compatible
- Model: test-model
- Chunk count: 3

## 摘要限制

本摘要由 LLM 根據逐字稿產生。所有重點應盡量附 timestamp evidence。
本摘要不構成投資建議。

## Validation Warnings

- legacy transcript metadata missing: generated_at, source_audio_path, source_audio_size_bytes

## 本集主題

- 語意摘要 `[00:00:00 - 00:00:10]`

## Chunk Summaries

### Chunk 1

### Chunk 1
- 重點 `[00:00:00 - 00:00:10]`

### Chunk 2

### Chunk 2
- 重點 `[00:10:20 - 00:10:40]`

### Chunk 3

### Chunk 3
- 重點 `[00:20:50 - 00:21:10]`
"""


def _profile_with_summary(summary_profile):
    from corpus_ingest_core.models import PodcastProfile

    return PodcastProfile(
        podcast_id="gooaye",
        display_name="Gooaye 股癌",
        rss_url="https://example.invalid/feed.xml",
        language="zh",
        default_episode_prefix="EP",
        summary_profile=summary_profile,
    )


def test_finance_rendering_is_byte_identical_to_the_pre_spec_037_document(
    monkeypatch, tmp_path
):
    """Every published verified research report descends from a semantic summary.
    This literal is the fixed point that keeps 股癌's shape from drifting."""

    import corpus_ingest_core.semantic_summarizer as semantic_summarizer

    paths = _write_transcript(monkeypatch, tmp_path)
    monkeypatch.setattr(
        semantic_summarizer, "_build_provider", lambda **kwargs: FakeProvider()
    )

    asset = semantic_summarizer.semantic_summarize_episode(
        "gooaye",
        "EP672",
        api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        model="test-model",
    )

    assert paths.json_path.exists()
    assert (
        Path(asset.summary_path).read_text(encoding="utf-8")
        == _EXPECTED_FINANCE_DOCUMENT
    )


def test_learning_notes_replaces_the_disclaimer_and_keeps_the_envelope(
    monkeypatch, tmp_path
):
    import corpus_ingest_core.semantic_summarizer as semantic_summarizer

    _write_transcript(monkeypatch, tmp_path)
    monkeypatch.setattr(
        semantic_summarizer,
        "load_podcast_profile",
        lambda podcast_id: _profile_with_summary("learning-notes"),
    )
    monkeypatch.setattr(
        semantic_summarizer, "_build_provider", lambda **kwargs: FakeProvider()
    )

    asset = semantic_summarizer.semantic_summarize_episode(
        "gooaye",
        "EP672",
        api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        model="test-model",
    )
    content = Path(asset.summary_path).read_text(encoding="utf-8")

    # The profile-driven part changed.
    assert "本摘要不構成投資建議" not in content
    assert "本摘要僅整理影片內容，結論請回到 timestamp 驗證。" in content

    # The envelope did not. Four downstream readers depend on each of these.
    assert "## 摘要限制" in content
    assert "## Chunk Summaries" in content
    assert "Summary mode: semantic-llm" in content
    assert "Provider:" in content
    assert "Model:" in content
    assert "Transcript status:" in content


def test_the_profile_reaches_the_provider_factory(monkeypatch, tmp_path):
    """FR-009: the shape follows the registered profile, not a call argument."""

    import corpus_ingest_core.semantic_summarizer as semantic_summarizer

    _write_transcript(monkeypatch, tmp_path)
    monkeypatch.setattr(
        semantic_summarizer,
        "load_podcast_profile",
        lambda podcast_id: _profile_with_summary("learning-notes"),
    )
    captured = {}

    def _capture(**kwargs):
        captured.update(kwargs)
        return FakeProvider()

    monkeypatch.setattr(semantic_summarizer, "_build_provider", _capture)

    semantic_summarizer.semantic_summarize_episode(
        "gooaye",
        "EP672",
        api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        model="test-model",
    )

    assert captured["summary_profile"] == "learning-notes"


def test_semantic_summarize_episode_has_no_per_run_profile_argument():
    """A per-run override would let one episode's summaries disagree with each
    other at the same canonical path."""

    import inspect

    from corpus_ingest_core.semantic_summarizer import semantic_summarize_episode

    assert "summary_profile" not in inspect.signature(
        semantic_summarize_episode
    ).parameters


def test_empty_transcript_branch_still_honours_the_profile(monkeypatch, tmp_path):
    """The empty-chunk path renders without ever building a provider, so it is
    the one place the profile reaches rendering through a different route."""

    import corpus_ingest_core.semantic_summarizer as semantic_summarizer

    _write_transcript(
        monkeypatch,
        tmp_path,
        segments=[{"id": 1, "start": 0.0, "end": 10.0, "text": "   "}],
    )
    monkeypatch.setattr(
        semantic_summarizer,
        "load_podcast_profile",
        lambda podcast_id: _profile_with_summary("learning-notes"),
    )

    def _must_not_build(**kwargs):
        raise AssertionError("the empty branch must not construct a provider")

    monkeypatch.setattr(semantic_summarizer, "_build_provider", _must_not_build)

    asset = semantic_summarizer.semantic_summarize_episode(
        "gooaye",
        "EP672",
        api_cost_ack=semantic_summarizer.SEMANTIC_API_COST_ACK,
        model="test-model",
    )
    content = Path(asset.summary_path).read_text(encoding="utf-8")

    assert "本摘要不構成投資建議" not in content
    assert "本摘要僅整理影片內容，結論請回到 timestamp 驗證。" in content
    assert "## Chunk Summaries" in content
