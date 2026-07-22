from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_to_jsonable_handles_dataclass_path_list_and_dict():
    from podcast_ingest_core.serialization import to_jsonable

    @dataclass(frozen=True)
    class Sample:
        path: Path
        values: list[object]

    payload = {
        "sample": Sample(path=Path("data/test.txt"), values=[Path("data/a.txt"), 1]),
    }

    assert to_jsonable(payload) == {
        "sample": {
            "path": "data\\test.txt",
            "values": ["data\\a.txt", 1],
        }
    }


def test_to_jsonable_handles_side_effect_asset_dataclasses():
    from podcast_ingest_core.models import (
        AudioAsset,
        MentionExtractionAsset,
        SummaryAsset,
        TranscriptAsset,
    )
    from podcast_ingest_core.serialization import to_jsonable

    payload = [
        AudioAsset(
            podcast_id="gooaye",
            episode_ref="EP672",
            title="Audio",
            source_url="https://example.test/audio.mp3",
            local_path=Path("data/audio/gooaye/audio.mp3"),
        ),
        TranscriptAsset(
            podcast_id="gooaye",
            episode_ref="EP672",
            title="Transcript",
            audio_path=Path("data/audio/gooaye/audio.mp3"),
            text_path=Path("data/transcripts/gooaye/EP672.txt"),
            srt_path=Path("data/transcripts/gooaye/EP672.srt"),
            json_path=Path("data/transcripts/gooaye/EP672.json"),
            model="tiny",
            language="zh",
            segment_count=1,
        ),
        SummaryAsset(
            podcast_id="gooaye",
            episode_ref="EP672",
            title="Summary",
            summary_path=Path("data/summaries/gooaye/EP672.md"),
            transcript_json_path=Path("data/transcripts/gooaye/EP672.json"),
            transcript_text_path=Path("data/transcripts/gooaye/EP672.txt"),
            segment_count=1,
            summary_mode="extractive-template",
        ),
        MentionExtractionAsset(
            podcast_id="gooaye",
            episode_ref="EP672",
            title="Mentions",
            source_transcript_json_path=Path("data/transcripts/gooaye/EP672.json"),
            mentions_json_path=Path("data/mentions/gooaye/EP672.mentions.json"),
            mentions_markdown_path=Path("data/mentions/gooaye/EP672.mentions.md"),
            mention_count=1,
            segment_count=1,
            extraction_mode="deterministic-rules",
            generated=True,
            already_exists=False,
        ),
    ]

    jsonable = to_jsonable(payload)

    assert jsonable[0]["local_path"] == "data\\audio\\gooaye\\audio.mp3"
    assert jsonable[1]["json_path"] == "data\\transcripts\\gooaye\\EP672.json"
    assert jsonable[2]["summary_path"] == "data\\summaries\\gooaye\\EP672.md"
    assert jsonable[3]["mentions_json_path"] == "data\\mentions\\gooaye\\EP672.mentions.json"


def test_mcp_server_imports_and_exposes_server_object():
    from podcast_ingest_core import mcp_server

    assert mcp_server.mcp.name == "podcast-ingest-core"


def test_list_episodes_tool_returns_enveloped_json_without_audio_url(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import Episode

    captured = {}

    def fake_list_episodes(podcast_id, limit):
        captured["podcast_id"] = podcast_id
        captured["limit"] = limit
        return [
            Episode(
                podcast_id=podcast_id,
                episode_ref="EP672",
                title="Title",
                audio_url="https://example.test/audio.mp3",
                published_at="today",
                duration="10:00",
                guid="guid",
                link="https://example.test/episode",
            )
        ]

    monkeypatch.setattr(mcp_server.feed_reader, "list_episodes", fake_list_episodes)

    response = mcp_server.list_episodes(podcast_id="gooaye", limit=999)

    assert response["ok"] is True
    assert captured == {"podcast_id": "gooaye", "limit": 50}
    episode = response["data"][0]
    assert episode["audio_url_present"] is True
    assert "audio_url" not in episode


def test_get_episode_tool_returns_enveloped_json_without_audio_url(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import Episode

    def fake_get_episode(podcast_id, episode_ref):
        return Episode(
            podcast_id=podcast_id,
            episode_ref="EP672",
            title="Title",
            audio_url="https://example.test/audio.mp3",
        )

    monkeypatch.setattr(mcp_server.feed_reader, "get_episode", fake_get_episode)

    response = mcp_server.get_episode(podcast_id="gooaye", episode_ref="latest")

    assert response["ok"] is True
    assert response["data"]["episode_ref"] == "EP672"
    assert response["data"]["audio_url_present"] is True
    assert "audio_url" not in response["data"]


def test_validate_transcript_tool_returns_jsonable_result(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import TranscriptValidationResult

    def fake_validate_transcript(podcast_id, episode_ref):
        return TranscriptValidationResult(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            valid=True,
            status="valid",
            segment_count=2,
            last_segment_end_seconds=10.0,
            transcript_text_length=100,
            problems=[],
            warnings=[],
            paths={"json": "data/transcripts/gooaye/EP672.json"},
        )

    monkeypatch.setattr(mcp_server.validator, "validate_transcript", fake_validate_transcript)

    response = mcp_server.validate_transcript(podcast_id="gooaye", episode_ref="EP672")

    assert response["ok"] is True
    assert response["data"]["status"] == "valid"
    assert response["data"]["paths"]["json"].endswith("EP672.json")


def test_search_transcripts_tool_clamps_limits_and_context(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import TranscriptSearchResult

    captured = {}

    def fake_search_transcripts(**kwargs):
        captured.update(kwargs)
        return [
            TranscriptSearchResult(
                podcast_id="gooaye",
                episode_ref="EP672",
                title="Title",
                segment_id="1",
                start=1.0,
                end=2.0,
                timestamp="[00:00:01 - 00:00:02]",
                text="台積電",
                matched_text="台積電",
                highlighted_text="[[台積電]]",
                context_before=[],
                context_after=[],
                search_mode="fallback",
            )
        ]

    monkeypatch.setattr(mcp_server.search_module, "search_transcripts", fake_search_transcripts)

    response = mcp_server.search_transcripts(query="台積電", limit=999, context_segments=999)

    assert response["ok"] is True
    assert captured["limit"] == 50
    assert captured["context_segments"] == 5
    assert response["data"][0]["highlighted_text"] == "[[台積電]]"


def test_search_mentions_tool_returns_enveloped_results(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import MentionSearchResult

    captured = {}

    def fake_search_mentions(**kwargs):
        captured.update(kwargs)
        return [
            MentionSearchResult(
                podcast_id="gooaye",
                episode_ref="EP672",
                title="Title",
                mention_type="company",
                text="台積電",
                normalized_text="台積電",
                count=2,
                evidence_timestamp="[00:00:01 - 00:00:02]",
                evidence_text="台積電",
                highlighted_text="[[台積電]]",
                search_mode="like",
            )
        ]

    monkeypatch.setattr(mcp_server.search_module, "search_mentions", fake_search_mentions)

    response = mcp_server.search_mentions(query="台積電", mention_type="company", limit=999)

    assert response["ok"] is True
    assert captured["limit"] == 50
    assert response["data"][0]["mention_type"] == "company"


def test_rebuild_cache_tool_returns_enveloped_result(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import CacheRebuildResult

    def fake_rebuild_cache(podcast_id=None, force=False):
        return CacheRebuildResult(
            db_path="data/cache/podcast_ingest.sqlite3",
            indexed_episode_count=1,
            skipped_episode_count=0,
            problems=[],
            warnings=[],
        )

    monkeypatch.setattr(mcp_server.cache_module, "rebuild_cache", fake_rebuild_cache)

    response = mcp_server.rebuild_cache(podcast_id="gooaye", force=True)

    assert response["ok"] is True
    assert response["data"]["indexed_episode_count"] == 1


def test_tool_wrapper_converts_core_errors_to_error_response(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.errors import SearchError

    def fake_search_transcripts(**kwargs):
        raise SearchError("SQLite cache 不存在：請先執行 rebuild_cache。")

    monkeypatch.setattr(mcp_server.search_module, "search_transcripts", fake_search_transcripts)

    response = mcp_server.search_transcripts(query="台積電")

    assert response == {
        "ok": False,
        "error_type": "SearchError",
        "message": "SQLite cache 不存在：請先執行 rebuild_cache。",
    }


def test_search_tools_reject_blank_query_before_core_call(monkeypatch):
    from podcast_ingest_core import mcp_server

    called = False

    def fake_search_transcripts(**kwargs):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(mcp_server.search_module, "search_transcripts", fake_search_transcripts)

    response = mcp_server.search_transcripts(query="   ")

    assert response["ok"] is False
    assert response["error_type"] == "ValueError"
    assert called is False


def test_download_audio_dry_run_does_not_call_core(monkeypatch):
    from podcast_ingest_core import mcp_server

    called = False

    def fake_download_audio(*args, **kwargs):
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(mcp_server.downloader, "download_audio", fake_download_audio)

    response = mcp_server.download_audio(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=False,
    )

    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["requires_confirmation"] is True
    assert response["tool"] == "download_audio"
    assert called is False


def test_download_audio_confirm_calls_core_and_hides_source_url(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import AudioAsset

    captured = {}

    def fake_download_audio(podcast_id, episode_ref):
        captured["podcast_id"] = podcast_id
        captured["episode_ref"] = episode_ref
        return AudioAsset(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title="Audio",
            source_url="https://example.test/audio.mp3",
            local_path=Path("data/audio/gooaye/audio.mp3"),
            size_bytes=123,
        )

    monkeypatch.setattr(mcp_server.downloader, "download_audio", fake_download_audio)

    response = mcp_server.download_audio(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=True,
        force=True,
    )

    assert response["ok"] is True
    assert captured == {"podcast_id": "gooaye", "episode_ref": "EP672"}
    assert response["data"]["source_url_present"] is True
    assert "source_url" not in response["data"]
    assert response["warnings"] == ["force is ignored because core download_audio does not support force"]


def test_summarize_episode_extractive_dry_run_does_not_call_core(monkeypatch):
    from podcast_ingest_core import mcp_server

    called = False

    def fake_summarize_episode(*args, **kwargs):
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(mcp_server.summarizer, "summarize_episode", fake_summarize_episode)

    response = mcp_server.summarize_episode_extractive(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=False,
    )

    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["tool"] == "summarize_episode_extractive"
    assert called is False


def test_summarize_episode_extractive_confirm_clamps_and_warns_cache_stale(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import SummaryAsset

    captured = {}

    def fake_summarize_episode(**kwargs):
        captured.update(kwargs)
        return SummaryAsset(
            podcast_id=kwargs["podcast_id"],
            episode_ref=kwargs["episode_ref"],
            title="Summary",
            summary_path=Path("data/summaries/gooaye/EP672.md"),
            transcript_json_path=Path("data/transcripts/gooaye/EP672.json"),
            transcript_text_path=Path("data/transcripts/gooaye/EP672.txt"),
            segment_count=1,
            summary_mode="extractive-template",
            generated=True,
        )

    monkeypatch.setattr(mcp_server.summarizer, "summarize_episode", fake_summarize_episode)

    response = mcp_server.summarize_episode_extractive(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=True,
        max_quotes=999,
        window_seconds=1,
    )

    assert response["ok"] is True
    assert captured["max_quotes"] == 50
    assert captured["window_seconds"] == 60
    assert "Cache may be stale" in response["warnings"][0]


def test_extract_mentions_dry_run_does_not_call_core(monkeypatch):
    from podcast_ingest_core import mcp_server

    called = False

    def fake_extract_mentions(*args, **kwargs):
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(mcp_server.entity_extractor, "extract_mentions", fake_extract_mentions)

    response = mcp_server.extract_mentions(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=False,
    )

    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["tool"] == "extract_mentions"
    assert called is False


def test_extract_mentions_confirm_clamps_and_warns_cache_stale(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import MentionExtractionAsset

    captured = {}

    def fake_extract_mentions(**kwargs):
        captured.update(kwargs)
        return MentionExtractionAsset(
            podcast_id=kwargs["podcast_id"],
            episode_ref=kwargs["episode_ref"],
            title="Mentions",
            source_transcript_json_path=Path("data/transcripts/gooaye/EP672.json"),
            mentions_json_path=Path("data/mentions/gooaye/EP672.mentions.json"),
            mentions_markdown_path=Path("data/mentions/gooaye/EP672.mentions.md"),
            mention_count=1,
            segment_count=1,
            extraction_mode="deterministic-rules",
            generated=True,
            already_exists=False,
        )

    monkeypatch.setattr(mcp_server.entity_extractor, "extract_mentions", fake_extract_mentions)

    response = mcp_server.extract_mentions(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=True,
        max_evidence_per_mention=999,
    )

    assert response["ok"] is True
    assert captured["max_evidence_per_mention"] == 20
    assert "Cache may be stale" in response["warnings"][0]


def test_transcribe_episode_dry_run_does_not_call_core(monkeypatch):
    from podcast_ingest_core import mcp_server

    called = False

    def fake_transcribe_episode(*args, **kwargs):
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(mcp_server.transcriber, "transcribe_episode", fake_transcribe_episode)

    response = mcp_server.transcribe_episode(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=False,
    )

    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["tool"] == "transcribe_episode"
    assert called is False


def test_transcribe_episode_confirm_calls_core_and_warns_cache_stale(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import TranscriptAsset

    captured = {}

    def fake_transcribe_episode(**kwargs):
        captured.update(kwargs)
        return TranscriptAsset(
            podcast_id=kwargs["podcast_id"],
            episode_ref=kwargs["episode_ref"],
            title="Transcript",
            audio_path=Path("data/audio/gooaye/audio.mp3"),
            text_path=Path("data/transcripts/gooaye/EP672.txt"),
            srt_path=Path("data/transcripts/gooaye/EP672.srt"),
            json_path=Path("data/transcripts/gooaye/EP672.json"),
            model=kwargs["model"],
            language="zh",
            segment_count=1,
        )

    monkeypatch.setattr(mcp_server.transcriber, "transcribe_episode", fake_transcribe_episode)

    response = mcp_server.transcribe_episode(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=True,
        model="tiny",
        device="cpu",
        compute_type="int8",
    )

    assert response["ok"] is True
    assert captured["audio_path"] is None
    assert captured["progress_callback"] is None
    assert "Cache may be stale" in response["warnings"][0]


def test_transcribe_episode_rejects_unknown_model_device_and_compute_type():
    from podcast_ingest_core import mcp_server

    assert mcp_server.transcribe_episode(
        episode_ref="EP672",
        confirm=True,
        model="unknown",
    )["error_type"] == "ValueError"
    assert mcp_server.transcribe_episode(
        episode_ref="EP672",
        confirm=True,
        device="metal",
    )["error_type"] == "ValueError"
    assert mcp_server.transcribe_episode(
        episode_ref="EP672",
        confirm=True,
        compute_type="bf16",
    )["error_type"] == "ValueError"


def test_side_effect_tool_core_error_returns_error_response(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.errors import DownloadFailedError

    def fake_download_audio(podcast_id, episode_ref):
        raise DownloadFailedError("download failed")

    monkeypatch.setattr(mcp_server.downloader, "download_audio", fake_download_audio)

    response = mcp_server.download_audio(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=True,
    )

    assert response == {
        "ok": False,
        "error_type": "DownloadFailedError",
        "message": "download failed",
    }


def test_semantic_summarize_episode_dry_run_does_not_call_core(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import TranscriptValidationResult

    called = False

    def fake_semantic_summarize_episode(*args, **kwargs):
        nonlocal called
        called = True
        return None

    def fake_validate_transcript(podcast_id, episode_ref):
        return TranscriptValidationResult(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            valid=True,
            status="valid",
            segment_count=245,
            last_segment_end_seconds=1234.5,
            transcript_text_length=9999,
            problems=[],
            warnings=[],
            paths={"json": "data/transcripts/gooaye/EP672.json"},
        )

    monkeypatch.setattr(
        mcp_server.semantic_summarizer,
        "semantic_summarize_episode",
        fake_semantic_summarize_episode,
    )
    monkeypatch.setattr(mcp_server.validator, "validate_transcript", fake_validate_transcript)
    monkeypatch.setenv("OPENAI_API_KEY", "secret-test-key")

    response = mcp_server.semantic_summarize_episode(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=False,
        model="test-model",
    )

    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["requires_api_cost_ack"] is True
    assert response["required_acknowledgement"] == mcp_server.SEMANTIC_API_COST_ACK
    assert response["tool"] == "semantic_summarize_episode"
    assert response["inputs"]["api_key_env_configured"] is True
    assert response["transcript_validation"]["status"] == "valid"
    assert response["transcript_validation"]["segment_count"] == 245
    assert response["transcript_validation"]["estimated_chunk_count"] == 3
    assert "secret-test-key" not in str(response)
    assert "raw transcript" not in str(response).lower()
    assert called is False


def test_semantic_summarize_episode_requires_exact_ack_before_core_call(monkeypatch):
    from podcast_ingest_core import mcp_server

    called = False

    def fake_semantic_summarize_episode(*args, **kwargs):
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(
        mcp_server.semantic_summarizer,
        "semantic_summarize_episode",
        fake_semantic_summarize_episode,
    )

    missing = mcp_server.semantic_summarize_episode(
        episode_ref="EP672",
        confirm=True,
        api_cost_ack="",
    )
    wrong = mcp_server.semantic_summarize_episode(
        episode_ref="EP672",
        confirm=True,
        api_cost_ack="I accept",
    )

    assert missing["ok"] is False
    assert missing["error_type"] == "ValueError"
    assert mcp_server.SEMANTIC_API_COST_ACK in missing["message"]
    assert wrong["ok"] is False
    assert wrong["error_type"] == "ValueError"
    assert called is False


def test_semantic_summarize_episode_confirm_calls_core_with_clamped_values(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.models import SummaryAsset

    captured = {}

    def fake_semantic_summarize_episode(**kwargs):
        captured.update(kwargs)
        return SummaryAsset(
            podcast_id=kwargs["podcast_id"],
            episode_ref=kwargs["episode_ref"],
            title="Semantic Summary",
            summary_path=Path("data/summaries/gooaye/EP672.semantic.md"),
            transcript_json_path=Path("data/transcripts/gooaye/EP672.json"),
            transcript_text_path=Path("data/transcripts/gooaye/EP672.txt"),
            segment_count=1,
            summary_mode="semantic-llm",
            generated=True,
            provider=kwargs["provider"],
            model=kwargs["model"],
            chunk_count=1,
            evidence_count=1,
        )

    monkeypatch.setattr(
        mcp_server.semantic_summarizer,
        "semantic_summarize_episode",
        fake_semantic_summarize_episode,
    )

    response = mcp_server.semantic_summarize_episode(
        podcast_id="gooaye",
        episode_ref="EP672",
        confirm=True,
        api_cost_ack=mcp_server.SEMANTIC_API_COST_ACK,
        model="test-model",
        base_url="https://api.example.test/v1?token=secret",
        chunk_seconds=1,
        max_segments_per_chunk=999,
    )

    assert response["ok"] is True
    assert captured["api_cost_ack"] == mcp_server.SEMANTIC_API_COST_ACK
    assert captured["chunk_seconds"] == 300
    assert captured["max_segments_per_chunk"] == 300
    assert captured["base_url"] == "https://api.example.test/v1?token=secret"
    assert response["data"]["summary_mode"] == "semantic-llm"
    assert "Cache may be stale" in response["warnings"][0]
    assert "secret" not in str(response)


def test_semantic_summarize_episode_rejects_provider_and_invalid_api_key_env():
    from podcast_ingest_core import mcp_server

    unsupported_provider = mcp_server.semantic_summarize_episode(
        episode_ref="EP672",
        confirm=True,
        api_cost_ack=mcp_server.SEMANTIC_API_COST_ACK,
        provider="other-provider",
    )
    invalid_env = mcp_server.semantic_summarize_episode(
        episode_ref="EP672",
        confirm=True,
        api_cost_ack=mcp_server.SEMANTIC_API_COST_ACK,
        api_key_env="OPENAI_API_KEY;echo secret",
    )

    assert unsupported_provider["ok"] is False
    assert unsupported_provider["error_type"] == "ValueError"
    assert invalid_env["ok"] is False
    assert invalid_env["error_type"] == "ValueError"


def test_semantic_summarize_episode_core_errors_return_error_response(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.errors import LLMProviderConfigError, LLMProviderRequestError

    def fake_config_error(**kwargs):
        raise LLMProviderConfigError("missing model")

    monkeypatch.setattr(
        mcp_server.semantic_summarizer,
        "semantic_summarize_episode",
        fake_config_error,
    )

    config_response = mcp_server.semantic_summarize_episode(
        episode_ref="EP672",
        confirm=True,
        api_cost_ack=mcp_server.SEMANTIC_API_COST_ACK,
    )

    def fake_request_error(**kwargs):
        raise LLMProviderRequestError("provider failed")

    monkeypatch.setattr(
        mcp_server.semantic_summarizer,
        "semantic_summarize_episode",
        fake_request_error,
    )

    request_response = mcp_server.semantic_summarize_episode(
        episode_ref="EP672",
        confirm=True,
        api_cost_ack=mcp_server.SEMANTIC_API_COST_ACK,
    )

    assert config_response == {
        "ok": False,
        "error_type": "LLMProviderConfigError",
        "message": "missing model",
    }
    assert request_response == {
        "ok": False,
        "error_type": "LLMProviderRequestError",
        "message": "provider failed",
    }


def test_completion_workflow_mcp_dry_run_forwards_to_core_and_uses_bounded_envelope(monkeypatch):
    from podcast_ingest_core import mcp_server

    captured = {}
    result = SimpleNamespace(
        selected_action="semantic_summary",
        rows=[SimpleNamespace(status="selected", requires_confirmation=True)],
    )

    def fake_run(**kwargs):
        captured.update(kwargs)
        return result

    monkeypatch.setattr(
        mcp_server.completion_workflow_runner,
        "run_corpus_episode_completion_workflow",
        fake_run,
    )
    monkeypatch.setattr(
        mcp_server.completion_workflow_runner,
        "result_to_dict",
        lambda value: {
            "selected_action": value.selected_action,
            "episode_ref": "EP672",
            "rows": [],
            "not_investment_advice": True,
        },
    )

    response = mcp_server.run_corpus_episode_completion_workflow(
        podcast_id="gooaye",
        episode_ref="latest",
        action="next",
        confirm=False,
        transcription_model="tiny",
        semantic_model="safe-model",
    )

    assert response == {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": True,
        "data": {
            "selected_action": "semantic_summary",
            "episode_ref": "EP672",
            "rows": [],
            "not_investment_advice": True,
        },
    }
    assert captured["podcast_id"] == "gooaye"
    assert captured["episode_ref"] == "latest"
    assert captured["action"] == "next"
    assert captured["confirm"] is False
    assert captured["progress_callback"] is None


def test_completion_workflow_mcp_terminal_dry_run_does_not_require_confirmation(monkeypatch):
    from podcast_ingest_core import mcp_server

    result = SimpleNamespace(selected_action="blocked", rows=[])
    monkeypatch.setattr(
        mcp_server.completion_workflow_runner,
        "run_corpus_episode_completion_workflow",
        lambda **kwargs: result,
    )
    monkeypatch.setattr(
        mcp_server.completion_workflow_runner,
        "result_to_dict",
        lambda value: {"selected_action": value.selected_action, "rows": []},
    )

    response = mcp_server.run_corpus_episode_completion_workflow(
        podcast_id="gooaye",
        confirm=False,
    )

    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["requires_confirmation"] is False


def test_completion_workflow_mcp_failed_selected_action_does_not_require_confirmation(monkeypatch):
    from podcast_ingest_core import mcp_server

    result = SimpleNamespace(
        selected_action="semantic_summary",
        rows=[SimpleNamespace(status="failed", requires_confirmation=False)],
    )
    monkeypatch.setattr(
        mcp_server.completion_workflow_runner,
        "run_corpus_episode_completion_workflow",
        lambda **kwargs: result,
    )
    monkeypatch.setattr(
        mcp_server.completion_workflow_runner,
        "result_to_dict",
        lambda value: {
            "selected_action": value.selected_action,
            "rows": [{"status": "failed", "requires_confirmation": False}],
        },
    )

    response = mcp_server.run_corpus_episode_completion_workflow(
        podcast_id="gooaye",
        confirm=False,
    )

    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["requires_confirmation"] is False


def test_completion_workflow_mcp_confirmed_result_uses_success_envelope(monkeypatch):
    from podcast_ingest_core import mcp_server

    captured = {}
    result = SimpleNamespace(selected_action="audio_download", rows=[])

    def fake_run(**kwargs):
        captured.update(kwargs)
        return result

    monkeypatch.setattr(
        mcp_server.completion_workflow_runner,
        "run_corpus_episode_completion_workflow",
        fake_run,
    )
    monkeypatch.setattr(
        mcp_server.completion_workflow_runner,
        "result_to_dict",
        lambda value: {"selected_action": value.selected_action, "executed_action": "audio_download"},
    )

    response = mcp_server.run_corpus_episode_completion_workflow(
        podcast_id="gooaye",
        episode_ref="EP672",
        action="audio_download",
        confirm=True,
    )

    assert response == {
        "ok": True,
        "data": {"selected_action": "audio_download", "executed_action": "audio_download"},
    }
    assert captured["confirm"] is True
    assert captured["progress_callback"] is None


def test_completion_workflow_mcp_uses_fixed_category_only_error_envelope(monkeypatch):
    from podcast_ingest_core import mcp_server
    from podcast_ingest_core.errors import CorpusEpisodeCompletionWorkflowRunnerFailedError

    monkeypatch.setattr(
        mcp_server.completion_workflow_runner,
        "run_corpus_episode_completion_workflow",
        lambda **kwargs: (_ for _ in ()).throw(
            CorpusEpisodeCompletionWorkflowRunnerFailedError(
                "https://private.example.test/path?token=secret raw transcript traceback"
            )
        ),
    )

    response = mcp_server.run_corpus_episode_completion_workflow(
        podcast_id="gooaye",
        confirm=False,
    )

    assert response == {
        "ok": False,
        "error_type": "CorpusEpisodeCompletionWorkflowRunnerFailedError",
        "message": "corpus episode completion workflow command failed",
    }


def test_completion_workflow_mcp_semantic_ack_rejects_before_selection_work(monkeypatch):
    from podcast_ingest_core import mcp_server

    called = False

    def fake_run(**kwargs):
        nonlocal called
        called = True
        raise AssertionError("core selection must not run for an invalid acknowledgement")

    monkeypatch.setattr(
        mcp_server.completion_workflow_runner,
        "run_corpus_episode_completion_workflow",
        fake_run,
    )

    response = mcp_server.run_corpus_episode_completion_workflow(
        podcast_id="gooaye",
        episode_ref="EP672",
        action="semantic_summary",
        confirm=True,
        api_cost_ack="wrong acknowledgement",
    )

    assert response == {
        "ok": False,
        "error_type": "CorpusEpisodeCompletionWorkflowRunnerFailedError",
        "message": "corpus episode completion workflow command failed",
    }
    assert called is False


def test_latest_deterministic_workflow_mcp_uses_bounded_envelopes(monkeypatch):
    from podcast_ingest_core import mcp_server

    captured = {}
    dry_result = SimpleNamespace(outcome="dry_run", episode_ref="EP672")

    def fake_run(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return dry_result

    monkeypatch.setattr(
        mcp_server.latest_deterministic_workflow_runner,
        "run_corpus_latest_episode_deterministic_workflow",
        fake_run,
    )
    monkeypatch.setattr(
        mcp_server.latest_deterministic_workflow_runner,
        "result_to_dict",
        lambda result: {"outcome": result.outcome, "episode_ref": result.episode_ref},
    )

    response = mcp_server.run_corpus_latest_episode_deterministic_workflow(
        podcast_id="gooaye",
        transcription_model="tiny",
        transcription_vad_filter=True,
    )

    assert response == {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": True,
        "data": {"outcome": "dry_run", "episode_ref": "EP672"},
    }
    assert captured == {
        "args": ("gooaye",),
        "confirm": False,
        "transcription_model": "tiny",
        "transcription_device": "cpu",
        "transcription_compute_type": "int8",
        "transcription_vad_filter": True,
    }

    ready_result = SimpleNamespace(outcome="ready_for_semantic_summary", episode_ref="EP672")
    monkeypatch.setattr(
        mcp_server.latest_deterministic_workflow_runner,
        "run_corpus_latest_episode_deterministic_workflow",
        lambda *args, **kwargs: ready_result,
    )
    confirmed = mcp_server.run_corpus_latest_episode_deterministic_workflow(
        podcast_id="gooaye",
        confirm=True,
    )
    assert confirmed == {
        "ok": True,
        "data": {"outcome": "ready_for_semantic_summary", "episode_ref": "EP672"},
    }

    monkeypatch.setattr(
        mcp_server.latest_deterministic_workflow_runner,
        "run_corpus_latest_episode_deterministic_workflow",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("https://private.example.test/path?token=secret raw transcript")
        ),
    )
    rejected = mcp_server.run_corpus_latest_episode_deterministic_workflow(
        podcast_id="gooaye",
    )
    assert rejected == {
        "ok": False,
        "error_type": "CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError",
        "message": "corpus latest episode deterministic workflow command failed",
    }


def test_verified_research_report_workflow_mcp_uses_dry_run_envelope_and_early_guard(monkeypatch):
    from podcast_ingest_core import mcp_server

    captured = {}
    monkeypatch.setattr(
        mcp_server.verified_research_report_workflow_runner,
        "run_latest_episode_verified_research_report_workflow",
        lambda podcast_id, **kwargs: captured.update({"podcast_id": podcast_id, **kwargs})
        or SimpleNamespace(outcome="dry_run"),
    )
    monkeypatch.setattr(
        mcp_server.verified_research_report_workflow_runner,
        "result_to_dict",
        lambda result: {"outcome": result.outcome},
    )

    preview = mcp_server.run_latest_episode_verified_research_report_workflow("gooaye")

    assert preview == {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": True,
        "data": {"outcome": "dry_run"},
    }
    assert captured["podcast_id"] == "gooaye"
    assert captured["confirm"] is False

    monkeypatch.setattr(
        mcp_server.verified_research_report_workflow_runner,
        "run_latest_episode_verified_research_report_workflow",
        lambda *args, **kwargs: pytest.fail("invalid confirmation must not reach Core"),
    )
    rejected = mcp_server.run_latest_episode_verified_research_report_workflow(
        "gooaye",
        confirm=True,
        expected_episode_ref="EP700",
        api_cost_ack="wrong",
    )

    assert rejected == {
        "ok": False,
        "error_type": "LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError",
        "message": "latest episode verified research report workflow command failed",
    }


def _workflow_result(*, dry_run=True, requires_api_cost_ack=False, stock_query="台積電"):
    from podcast_ingest_core.models import ResearchWorkflowResult, ResearchWorkflowStep

    steps = [
        ResearchWorkflowStep(
            name="extract_mentions",
            status="planned" if dry_run else "completed",
            action="Read transcript and write mentions.",
            planned_reads=["data/transcripts/gooaye/EP672__title.json"],
            planned_writes=[
                "data/mentions/gooaye/EP672__title.mentions.json",
                "data/mentions/gooaye/EP672__title.mentions.md",
            ],
            risks=["Writes local mention artifacts", "Does not call external APIs"],
            generated_artifacts=[] if dry_run else ["data/mentions/gooaye/EP672__title.mentions.json"],
            reused_artifacts=[],
        )
    ]
    if stock_query:
        steps.append(
            ResearchWorkflowStep(
                name="generate_stock_lens_report",
                status="planned" if dry_run else "completed",
                action="Write stock lens report.",
                planned_reads=["data/mappings/gooaye/*.industry-map.json"],
                planned_writes=[
                    "data/stock-lens/gooaye/台積電.stock-lens.json",
                    "data/stock-lens/gooaye/台積電.stock-lens.md",
                ],
                risks=["No buy/sell/hold advice"],
                generated_artifacts=[] if dry_run else ["data/stock-lens/gooaye/台積電.stock-lens.json"],
                reused_artifacts=[],
            )
        )
    if requires_api_cost_ack:
        steps.append(
            ResearchWorkflowStep(
                name="generate_stock_lens_synthesis_report",
                status="planned" if dry_run else "completed",
                action="Write LLM stock lens synthesis.",
                planned_reads=["data/stock-lens/gooaye/台積電.stock-lens.json"],
                planned_writes=[
                    "data/stock-lens/gooaye/台積電.stock-lens-synthesis.json",
                    "data/stock-lens/gooaye/台積電.stock-lens-synthesis.md",
                ],
                risks=[
                    "Calls an external LLM API",
                    "May incur API cost risk",
                    "Uses no raw transcript text",
                ],
                generated_artifacts=[]
                if dry_run
                else ["data/stock-lens/gooaye/台積電.stock-lens-synthesis.json"],
                reused_artifacts=[],
            )
        )
    return ResearchWorkflowResult(
        podcast_id="gooaye",
        episode_ref="EP672",
        stock_query=stock_query,
        workflow_status="planned" if dry_run else "completed",
        dry_run=dry_run,
        requires_confirmation=dry_run,
        requires_api_cost_ack=requires_api_cost_ack,
        required_acknowledgement="I understand this may call an external LLM API, send transcript text outside this machine, and incur costs."
        if requires_api_cost_ack
        else None,
        transcript_status="valid",
        steps=steps,
        planned_reads=["data/transcripts/gooaye/EP672__title.json"],
        planned_writes=[path for step in steps for path in step.planned_writes],
        written_artifacts=[] if dry_run else [path for step in steps for path in step.generated_artifacts],
        generated_artifacts=[] if dry_run else [path for step in steps for path in step.generated_artifacts],
        reused_artifacts=[],
        external_api_steps=["semantic_summarize_episode"]
        + (["generate_stock_lens_synthesis_report"] if requires_api_cost_ack else []),
        warnings=["Cache may be stale. Run rebuild_cache manually after workflow completion."],
        not_investment_advice=True,
    )


def test_run_research_workflow_mcp_dry_run_returns_plan_without_leaks(monkeypatch):
    from podcast_ingest_core import mcp_server

    captured = {}

    def fake_run_research_workflow(**kwargs):
        captured.update(kwargs)
        return _workflow_result(dry_run=True)

    monkeypatch.setattr(
        mcp_server.research_workflow,
        "run_research_workflow",
        fake_run_research_workflow,
    )
    monkeypatch.setenv("OPENAI_API_KEY", "secret-test-key")

    response = mcp_server.run_research_workflow(
        podcast_id="gooaye",
        episode_ref="EP672",
        stock_query="台積電",
        confirm=False,
    )

    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["tool"] == "run_research_workflow"
    assert response["requires_confirmation"] is True
    assert response["planned_reads"] == ["data/transcripts/gooaye/EP672__title.json"]
    assert "data/mentions/gooaye/EP672__title.mentions.json" in response["planned_writes"]
    assert response["steps"][0]["name"] == "extract_mentions"
    assert captured["confirm"] is False
    assert "secret-test-key" not in str(response)
    assert "raw transcript" not in str(response).lower()


def test_run_research_workflow_mcp_confirm_calls_core_with_defaults(monkeypatch):
    from podcast_ingest_core import mcp_server

    captured = {}
    rebuild_called = False

    def fake_run_research_workflow(**kwargs):
        captured.update(kwargs)
        return _workflow_result(dry_run=False)

    def fake_rebuild_cache(*args, **kwargs):
        nonlocal rebuild_called
        rebuild_called = True
        return None

    monkeypatch.setattr(
        mcp_server.research_workflow,
        "run_research_workflow",
        fake_run_research_workflow,
    )
    monkeypatch.setattr(mcp_server.cache_module, "rebuild_cache", fake_rebuild_cache)

    response = mcp_server.run_research_workflow(
        podcast_id="gooaye",
        episode_ref="EP672",
        stock_query="台積電",
        confirm=True,
    )

    assert response["ok"] is True
    assert response["data"]["workflow_status"] == "completed"
    assert captured["confirm"] is True
    assert captured["force"] is False
    assert captured["allow_partial"] is False
    assert captured["include_semantic_summary"] is False
    assert captured["include_stock_lens_synthesis"] is False
    assert captured["semantic_provider"] == "openai-compatible"
    assert captured["synthesis_provider"] == "openai-compatible"
    assert "Cache may be stale" in response["warnings"][0]
    assert rebuild_called is False


def test_run_research_workflow_mcp_semantic_dry_run_requires_ack(monkeypatch):
    from podcast_ingest_core import mcp_server

    def fake_run_research_workflow(**kwargs):
        return _workflow_result(dry_run=True, requires_api_cost_ack=True)

    monkeypatch.setattr(
        mcp_server.research_workflow,
        "run_research_workflow",
        fake_run_research_workflow,
    )

    response = mcp_server.run_research_workflow(
        podcast_id="gooaye",
        episode_ref="EP672",
        include_semantic_summary=True,
        confirm=False,
    )

    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["requires_api_cost_ack"] is True
    assert response["required_acknowledgement"] == mcp_server.SEMANTIC_API_COST_ACK
    assert "semantic_summarize_episode" in response["external_api_steps"]
    assert "external LLM API" in str(response)
    assert "API cost risk" in str(response)


def test_run_research_workflow_mcp_confirm_requires_ack_before_core(monkeypatch):
    from podcast_ingest_core import mcp_server

    called = False

    def fake_run_research_workflow(**kwargs):
        nonlocal called
        called = True
        return _workflow_result(dry_run=False, requires_api_cost_ack=True)

    monkeypatch.setattr(
        mcp_server.research_workflow,
        "run_research_workflow",
        fake_run_research_workflow,
    )

    semantic_response = mcp_server.run_research_workflow(
        podcast_id="gooaye",
        episode_ref="EP672",
        include_semantic_summary=True,
        confirm=True,
    )
    synthesis_response = mcp_server.run_research_workflow(
        podcast_id="gooaye",
        episode_ref="EP672",
        stock_query="台積電",
        include_stock_lens_synthesis=True,
        confirm=True,
        api_cost_ack="wrong",
    )

    assert semantic_response["ok"] is False
    assert semantic_response["error_type"] == "ValueError"
    assert synthesis_response["ok"] is False
    assert synthesis_response["error_type"] == "ValueError"
    assert called is False


def test_run_research_workflow_mcp_requires_stock_for_synthesis():
    from podcast_ingest_core import mcp_server

    response = mcp_server.run_research_workflow(
        podcast_id="gooaye",
        episode_ref="EP672",
        include_stock_lens_synthesis=True,
        confirm=False,
    )

    assert response["ok"] is False
    assert response["error_type"] == "ValueError"
    assert "stock_query" in response["message"]


def test_run_research_workflow_mcp_rejects_provider_and_invalid_env():
    from podcast_ingest_core import mcp_server

    unsupported_semantic_provider = mcp_server.run_research_workflow(
        podcast_id="gooaye",
        episode_ref="EP672",
        include_semantic_summary=True,
        semantic_provider="other-provider",
    )
    unsupported_synthesis_provider = mcp_server.run_research_workflow(
        podcast_id="gooaye",
        episode_ref="EP672",
        stock_query="台積電",
        include_stock_lens_synthesis=True,
        synthesis_provider="other-provider",
    )
    invalid_env = mcp_server.run_research_workflow(
        podcast_id="gooaye",
        episode_ref="EP672",
        include_semantic_summary=True,
        semantic_api_key_env="OPENAI_API_KEY;echo secret",
    )

    assert unsupported_semantic_provider["ok"] is False
    assert unsupported_semantic_provider["error_type"] == "ValueError"
    assert unsupported_synthesis_provider["ok"] is False
    assert unsupported_synthesis_provider["error_type"] == "ValueError"
    assert invalid_env["ok"] is False
    assert invalid_env["error_type"] == "ValueError"


def test_to_jsonable_handles_semantic_summary_asset():
    from podcast_ingest_core.models import SummaryAsset
    from podcast_ingest_core.serialization import to_jsonable

    asset = SummaryAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="Semantic Summary",
        summary_path=Path("data/summaries/gooaye/EP672.semantic.md"),
        transcript_json_path=Path("data/transcripts/gooaye/EP672.json"),
        transcript_text_path=Path("data/transcripts/gooaye/EP672.txt"),
        segment_count=1,
        summary_mode="semantic-llm",
        generated=True,
        provider="openai-compatible",
        model="test-model",
        chunk_count=2,
        evidence_count=3,
    )

    jsonable = to_jsonable(asset)

    assert jsonable["summary_path"] == "data\\summaries\\gooaye\\EP672.semantic.md"
    assert jsonable["provider"] == "openai-compatible"
    assert jsonable["model"] == "test-model"
    assert jsonable["chunk_count"] == 2
