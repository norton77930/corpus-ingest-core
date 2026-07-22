from __future__ import annotations

import math
import os
import re
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from . import cache as cache_module
from . import corpus_episode_completion_workflow_runner as completion_workflow_runner
from . import corpus_latest_episode_deterministic_workflow_runner as latest_deterministic_workflow_runner
from . import latest_episode_verified_research_report_workflow_runner as verified_research_report_workflow_runner
from . import mcp_episode_verified_research_report
from . import downloader
from . import entity_extractor
from . import feed_reader
from . import research_workflow
from . import search as search_module
from . import semantic_summarizer
from . import summarizer
from . import transcriber
from . import validator
from .errors import PodcastIngestCoreError, SearchError
from .models import AudioAsset, Episode
from .serialization import to_jsonable


MAX_LIMIT = 50
MAX_CONTEXT_SEGMENTS = 5
MAX_QUOTES = 50
MIN_WINDOW_SECONDS = 60
MAX_WINDOW_SECONDS = 1800
MIN_EVIDENCE_PER_MENTION = 1
MAX_EVIDENCE_PER_MENTION = 20
ALLOWED_TRANSCRIPTION_MODELS = {"tiny", "base", "small", "medium", "large-v3"}
ALLOWED_TRANSCRIPTION_DEVICES = {"cpu", "cuda"}
ALLOWED_TRANSCRIPTION_COMPUTE_TYPES = {"int8", "float16", "float32"}
ALLOWED_SEMANTIC_PROVIDERS = {"openai-compatible"}
MIN_SEMANTIC_CHUNK_SECONDS = 300
MAX_SEMANTIC_CHUNK_SECONDS = 1800
MIN_SEMANTIC_SEGMENTS_PER_CHUNK = 20
MAX_SEMANTIC_SEGMENTS_PER_CHUNK = 300
CACHE_STALE_WARNING = "Cache may be stale. Run rebuild_cache to index updated artifacts."
SEMANTIC_CACHE_STALE_WARNING = (
    "Cache may be stale. Run rebuild_cache to index updated semantic summary artifact."
)
WORKFLOW_CACHE_STALE_WARNING = (
    "Cache may be stale. Run rebuild_cache to index updated research workflow artifacts."
)
SEMANTIC_API_COST_ACK = semantic_summarizer.SEMANTIC_API_COST_ACK
_SAFE_ENV_VAR_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_COMPLETION_EXECUTABLE_ACTIONS = {
    "intake",
    "audio_download",
    "local_transcription",
    "deterministic_remediation",
    "semantic_summary",
    "semantic_review",
}
_COMPLETION_TOOL_ERROR_TYPE = "CorpusEpisodeCompletionWorkflowRunnerFailedError"
_COMPLETION_TOOL_ERROR_MESSAGE = "corpus episode completion workflow command failed"
_LATEST_DETERMINISTIC_WORKFLOW_TOOL_ERROR_TYPE = (
    "CorpusLatestEpisodeDeterministicWorkflowRunnerFailedError"
)
_LATEST_DETERMINISTIC_WORKFLOW_TOOL_ERROR_MESSAGE = (
    "corpus latest episode deterministic workflow command failed"
)
_VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL_ERROR_TYPE = (
    "LatestEpisodeVerifiedResearchReportWorkflowRunnerFailedError"
)
_VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL_ERROR_MESSAGE = (
    "latest episode verified research report workflow command failed"
)
_SAFE_EPISODE_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,127}$")

mcp = FastMCP("podcast-ingest-core")


def tool_success(data: Any, warnings: list[str] | None = None) -> dict[str, Any]:
    """回傳 MCP tool 成功 envelope。"""

    response = {"ok": True, "data": to_jsonable(data)}
    if warnings:
        response["warnings"] = warnings
    return response


def tool_error(message: str, error_type: str | None = None) -> dict[str, Any]:
    """回傳 MCP tool 錯誤 envelope，不暴露 traceback。"""

    return {
        "ok": False,
        "error_type": error_type,
        "message": message,
    }


def tool_action_plan(
    *,
    tool_name: str,
    action: str,
    inputs: dict[str, Any],
    writes: list[str],
    risks: list[str],
    requires_confirmation: bool = True,
) -> dict[str, Any]:
    """回傳 side-effect tool 的 dry-run action plan。"""

    return {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": requires_confirmation,
        "tool": tool_name,
        "action": action,
        "inputs": to_jsonable(inputs),
        "writes": writes,
        "risks": risks,
        "next_step": "Call this tool again with confirm=true to execute.",
    }


def run() -> None:
    """以 FastMCP 預設 stdio transport 啟動 server。"""

    mcp.run()


@mcp.tool()
def list_episodes(podcast_id: str = "gooaye", limit: int = 10) -> dict[str, Any]:
    """列出指定 podcast 最近集數；不回傳完整 audio_url。"""

    return _tool_call(
        lambda: [
            _episode_to_safe_dict(episode)
            for episode in feed_reader.list_episodes(podcast_id, _clamp_limit(limit))
        ]
    )


@mcp.tool()
def get_episode(podcast_id: str = "gooaye", episode_ref: str = "latest") -> dict[str, Any]:
    """查詢單一 podcast episode metadata；支援 latest 與大小寫不敏感 EP ref。"""

    return _tool_call(
        lambda: _episode_to_safe_dict(feed_reader.get_episode(podcast_id, episode_ref))
    )


@mcp.tool()
def validate_transcript(podcast_id: str = "gooaye", episode_ref: str = "latest") -> dict[str, Any]:
    """檢查既有 transcript artifacts 是否完整、有效或疑似 partial。"""

    return _tool_call(lambda: validator.validate_transcript(podcast_id, episode_ref))


@mcp.tool()
def search_transcripts(
    query: str,
    podcast_id: str | None = "gooaye",
    limit: int = 10,
    search_mode: str = "auto",
    context_segments: int = 0,
    case_sensitive: bool = False,
) -> dict[str, Any]:
    """搜尋 SQLite cache 中的 transcript segments；不會自動 rebuild cache。"""

    if not query.strip():
        return tool_error("query 不可為空。", "ValueError")
    return _tool_call(
        lambda: search_module.search_transcripts(
            query=query,
            podcast_id=podcast_id,
            limit=_clamp_limit(limit),
            search_mode=search_mode,
            context_segments=_clamp_context_segments(context_segments),
            case_sensitive=case_sensitive,
        )
    )


@mcp.tool()
def search_mentions(
    query: str,
    podcast_id: str | None = "gooaye",
    mention_type: str | None = None,
    limit: int = 10,
    case_sensitive: bool = False,
) -> dict[str, Any]:
    """搜尋 SQLite cache 中的 deterministic mentions 與 timestamp evidence。"""

    if not query.strip():
        return tool_error("query 不可為空。", "ValueError")
    return _tool_call(
        lambda: search_module.search_mentions(
            query=query,
            podcast_id=podcast_id,
            mention_type=mention_type,
            limit=_clamp_limit(limit),
            case_sensitive=case_sensitive,
        )
    )


@mcp.tool()
def rebuild_cache(podcast_id: str | None = None, force: bool = False) -> dict[str, Any]:
    """Maintenance tool：重建 SQLite cache；只索引既有 artifacts，不下載、不轉錄、不摘要。"""

    return _tool_call(lambda: cache_module.rebuild_cache(podcast_id=podcast_id, force=force))


@mcp.tool()
def download_audio(
    podcast_id: str = "gooaye",
    episode_ref: str = "latest",
    confirm: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Side-effect tool：需要 confirm=true 才會下載 podcast audio。"""

    if not confirm:
        return tool_action_plan(
            tool_name="download_audio",
            action="Download podcast episode audio into deterministic data/audio artifacts.",
            inputs={
                "podcast_id": podcast_id,
                "episode_ref": episode_ref,
                "force": force,
            },
            writes=[f"data/audio/{podcast_id}/..."],
            risks=[
                "Network request and potentially large audio download",
                "May write a new audio file under data/audio",
                "force is currently ignored because core download_audio does not support force",
            ],
        )

    warnings = ["force is ignored because core download_audio does not support force"] if force else None
    return _tool_call(
        lambda: _audio_asset_to_safe_dict(downloader.download_audio(podcast_id, episode_ref)),
        warnings=warnings,
    )


@mcp.tool()
def summarize_episode_extractive(
    podcast_id: str = "gooaye",
    episode_ref: str = "latest",
    confirm: bool = False,
    force: bool = False,
    allow_partial: bool = False,
    max_quotes: int = 10,
    window_seconds: int = 300,
) -> dict[str, Any]:
    """Side-effect tool：需要 confirm=true 才會寫入 deterministic extractive summary。"""

    clamped_max_quotes = _clamp(max_quotes, 0, MAX_QUOTES)
    clamped_window_seconds = _clamp(
        window_seconds, MIN_WINDOW_SECONDS, MAX_WINDOW_SECONDS
    )
    inputs = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "force": force,
        "allow_partial": allow_partial,
        "max_quotes": clamped_max_quotes,
        "window_seconds": clamped_window_seconds,
    }
    if not confirm:
        return tool_action_plan(
            tool_name="summarize_episode_extractive",
            action="Read existing transcript artifacts and write deterministic extractive summary markdown.",
            inputs=inputs,
            writes=[f"data/summaries/{podcast_id}/..."],
            risks=[
                "Writes summary artifact under data/summaries",
                "Does not call external LLM APIs",
                "May overwrite summary when force=true",
                "Cache may be stale after completion; run rebuild_cache manually",
            ],
        )

    return _tool_call(
        lambda: summarizer.summarize_episode(**inputs),
        warnings=[CACHE_STALE_WARNING],
    )


@mcp.tool()
def extract_mentions(
    podcast_id: str = "gooaye",
    episode_ref: str = "latest",
    confirm: bool = False,
    force: bool = False,
    allow_partial: bool = False,
    max_evidence_per_mention: int = 5,
) -> dict[str, Any]:
    """Side-effect tool：需要 confirm=true 才會寫入 deterministic mention artifacts。"""

    clamped_max_evidence = _clamp(
        max_evidence_per_mention,
        MIN_EVIDENCE_PER_MENTION,
        MAX_EVIDENCE_PER_MENTION,
    )
    inputs = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "force": force,
        "allow_partial": allow_partial,
        "max_evidence_per_mention": clamped_max_evidence,
    }
    if not confirm:
        return tool_action_plan(
            tool_name="extract_mentions",
            action="Read existing transcript artifacts and write deterministic rule-based mention artifacts.",
            inputs=inputs,
            writes=[
                f"data/mentions/{podcast_id}/...",
            ],
            risks=[
                "Writes mention JSON and Markdown artifacts under data/mentions",
                "Uses deterministic rules and does not call LLM APIs",
                "May overwrite mentions when force=true",
                "Cache may be stale after completion; run rebuild_cache manually",
            ],
        )

    return _tool_call(
        lambda: entity_extractor.extract_mentions(**inputs),
        warnings=[CACHE_STALE_WARNING],
    )


@mcp.tool()
def transcribe_episode(
    podcast_id: str = "gooaye",
    episode_ref: str = "latest",
    confirm: bool = False,
    model: str = "tiny",
    device: str = "cpu",
    compute_type: str = "int8",
    vad_filter: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Long-running side-effect tool：需要 confirm=true 才會下載/取得音檔並轉錄。"""

    validation_error = _validate_transcription_options(model, device, compute_type)
    if validation_error is not None:
        return validation_error

    inputs = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "model": model,
        "device": device,
        "compute_type": compute_type,
        "vad_filter": vad_filter,
        "force": force,
    }
    if not confirm:
        return tool_action_plan(
            tool_name="transcribe_episode",
            action="Download or reuse episode audio and write transcript TXT/SRT/JSON artifacts.",
            inputs=inputs,
            writes=[f"data/audio/{podcast_id}/...", f"data/transcripts/{podcast_id}/..."],
            risks=[
                "Long-running CPU/GPU task",
                "May download large audio files",
                "May download model files if not cached",
                "May overwrite transcript artifacts when force=true",
                "Cache may be stale after completion; run rebuild_cache manually",
            ],
        )

    return _tool_call(
        lambda: transcriber.transcribe_episode(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            model=model,
            device=device,
            compute_type=compute_type,
            vad_filter=vad_filter,
            force=force,
            audio_path=None,
            progress_callback=None,
        ),
        warnings=[CACHE_STALE_WARNING],
    )


@mcp.tool()
def semantic_summarize_episode(
    podcast_id: str = "gooaye",
    episode_ref: str = "latest",
    confirm: bool = False,
    api_cost_ack: str = "",
    provider: str = "openai-compatible",
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "OPENAI_API_KEY",
    force: bool = False,
    chunk_seconds: int = 600,
    max_segments_per_chunk: int = 120,
    allow_partial: bool = False,
) -> dict[str, Any]:
    """API-cost side-effect tool：需要 confirm=true 與 exact api_cost_ack 才會呼叫外部 LLM。"""

    validation_error = _validate_semantic_options(provider, api_key_env)
    if validation_error is not None:
        return validation_error

    clamped_chunk_seconds = _clamp(
        chunk_seconds, MIN_SEMANTIC_CHUNK_SECONDS, MAX_SEMANTIC_CHUNK_SECONDS
    )
    clamped_max_segments = _clamp(
        max_segments_per_chunk,
        MIN_SEMANTIC_SEGMENTS_PER_CHUNK,
        MAX_SEMANTIC_SEGMENTS_PER_CHUNK,
    )
    inputs = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "provider": provider,
        "model": model,
        "base_url_configured": bool(base_url),
        "api_key_env": api_key_env,
        "api_key_env_configured": bool(os.environ.get(api_key_env, "").strip()),
        "force": force,
        "chunk_seconds": clamped_chunk_seconds,
        "max_segments_per_chunk": clamped_max_segments,
        "allow_partial": allow_partial,
    }
    if not confirm:
        response = tool_action_plan(
            tool_name="semantic_summarize_episode",
            action="Generate semantic LLM summary from an existing transcript.",
            inputs=inputs,
            writes=[
                f"data/summaries/{podcast_id}/{episode_ref}__{{safe_title_slug}}.semantic.md"
            ],
            risks=[
                "Calls an external LLM API",
                "May incur API costs",
                "Sends transcript text outside this machine",
                "May take time for long transcripts",
                "May overwrite semantic summary when force=true",
                "Does not provide financial advice",
            ],
        )
        response["requires_api_cost_ack"] = True
        response["required_acknowledgement"] = SEMANTIC_API_COST_ACK
        response["transcript_validation"] = _semantic_transcript_preview(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            chunk_seconds=clamped_chunk_seconds,
            max_segments_per_chunk=clamped_max_segments,
        )
        response["next_step"] = (
            "Call this tool again with confirm=true and the exact api_cost_ack string to execute."
        )
        return response

    if api_cost_ack != SEMANTIC_API_COST_ACK:
        return tool_error(
            "semantic_summarize_episode requires exact api_cost_ack: "
            f"{SEMANTIC_API_COST_ACK}",
            "ValueError",
        )

    return _semantic_tool_call(
        lambda: semantic_summarizer.semantic_summarize_episode(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            api_cost_ack=api_cost_ack,
            provider=provider,
            model=model,
            base_url=base_url,
            api_key_env=api_key_env,
            force=force,
            chunk_seconds=clamped_chunk_seconds,
            max_segments_per_chunk=clamped_max_segments,
            allow_partial=allow_partial,
        ),
        warnings=[SEMANTIC_CACHE_STALE_WARNING],
        base_url=base_url,
    )


@mcp.tool()
def run_research_workflow(
    podcast_id: str = "gooaye",
    episode_ref: str = "latest",
    stock_query: str | None = None,
    confirm: bool = False,
    force: bool = False,
    allow_partial: bool = False,
    include_semantic_summary: bool = False,
    include_stock_lens_synthesis: bool = False,
    api_cost_ack: str = "",
    semantic_provider: str = "openai-compatible",
    semantic_model: str | None = None,
    semantic_base_url: str | None = None,
    semantic_api_key_env: str = "OPENAI_API_KEY",
    semantic_chunk_seconds: int = 600,
    semantic_max_segments_per_chunk: int = 120,
    synthesis_provider: str = "openai-compatible",
    synthesis_model: str | None = None,
    synthesis_base_url: str | None = None,
    synthesis_api_key_env: str = "OPENAI_API_KEY",
    synthesis_max_prompt_chars: int = 24000,
    max_evidence_per_mention: int = 5,
    report_window_seconds: int = 300,
    max_evidence_per_section: int = 5,
    max_candidates_per_node: int = 5,
    max_evidence_per_candidate: int = 5,
    max_stock_evidence_items: int = 10,
) -> dict[str, Any]:
    """Side-effect workflow tool：dry-run first，confirmed LLM steps require exact ack。"""

    normalized_stock_query = stock_query.strip() if stock_query else None
    validation_error = _validate_workflow_options(
        include_stock_lens_synthesis=include_stock_lens_synthesis,
        stock_query=normalized_stock_query,
        semantic_provider=semantic_provider,
        semantic_api_key_env=semantic_api_key_env,
        synthesis_provider=synthesis_provider,
        synthesis_api_key_env=synthesis_api_key_env,
    )
    if validation_error is not None:
        return validation_error

    requires_llm_ack = include_semantic_summary or include_stock_lens_synthesis
    if confirm and requires_llm_ack and api_cost_ack != SEMANTIC_API_COST_ACK:
        return tool_error(
            "run_research_workflow requires exact api_cost_ack for external LLM steps: "
            f"{SEMANTIC_API_COST_ACK}",
            "ValueError",
        )

    inputs = {
        "podcast_id": podcast_id,
        "episode_ref": episode_ref,
        "stock_query": normalized_stock_query,
        "force": force,
        "allow_partial": allow_partial,
        "include_semantic_summary": include_semantic_summary,
        "include_stock_lens_synthesis": include_stock_lens_synthesis,
        "semantic_provider": semantic_provider,
        "semantic_model": semantic_model,
        "semantic_base_url_configured": bool(semantic_base_url),
        "semantic_api_key_env": semantic_api_key_env,
        "semantic_chunk_seconds": semantic_chunk_seconds,
        "semantic_max_segments_per_chunk": semantic_max_segments_per_chunk,
        "synthesis_provider": synthesis_provider,
        "synthesis_model": synthesis_model,
        "synthesis_base_url_configured": bool(synthesis_base_url),
        "synthesis_api_key_env": synthesis_api_key_env,
        "synthesis_max_prompt_chars": synthesis_max_prompt_chars,
        "max_evidence_per_mention": max_evidence_per_mention,
        "report_window_seconds": report_window_seconds,
        "max_evidence_per_section": max_evidence_per_section,
        "max_candidates_per_node": max_candidates_per_node,
        "max_evidence_per_candidate": max_evidence_per_candidate,
        "max_stock_evidence_items": max_stock_evidence_items,
    }

    def operation():
        return research_workflow.run_research_workflow(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            stock_query=normalized_stock_query,
            confirm=confirm,
            force=force,
            allow_partial=allow_partial,
            include_semantic_summary=include_semantic_summary,
            include_stock_lens_synthesis=include_stock_lens_synthesis,
            api_cost_ack=api_cost_ack,
            semantic_provider=semantic_provider,
            semantic_model=semantic_model,
            semantic_base_url=semantic_base_url,
            semantic_api_key_env=semantic_api_key_env,
            semantic_chunk_seconds=semantic_chunk_seconds,
            semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
            synthesis_provider=synthesis_provider,
            synthesis_model=synthesis_model,
            synthesis_base_url=synthesis_base_url,
            synthesis_api_key_env=synthesis_api_key_env,
            synthesis_max_prompt_chars=synthesis_max_prompt_chars,
            max_evidence_per_mention=max_evidence_per_mention,
            report_window_seconds=report_window_seconds,
            max_evidence_per_section=max_evidence_per_section,
            max_candidates_per_node=max_candidates_per_node,
            max_evidence_per_candidate=max_evidence_per_candidate,
            max_stock_evidence_items=max_stock_evidence_items,
        )

    if not confirm:
        return _workflow_dry_run_call(
            operation=operation,
            inputs=inputs,
            base_urls=[semantic_base_url, synthesis_base_url],
        )

    return _workflow_tool_call(
        operation=operation,
        warnings=[WORKFLOW_CACHE_STALE_WARNING],
        base_urls=[semantic_base_url, synthesis_base_url],
    )


@mcp.tool()
def run_corpus_episode_completion_workflow(
    podcast_id: str,
    episode_ref: str = "latest",
    action: str = "next",
    confirm: bool = False,
    api_cost_ack: str = "",
    transcription_model: str | None = None,
    transcription_device: str = "cpu",
    transcription_compute_type: str = "int8",
    transcription_vad_filter: bool = False,
    semantic_provider: str = "openai-compatible",
    semantic_model: str | None = None,
    semantic_base_url: str | None = None,
    semantic_api_key_env: str = "OPENAI_API_KEY",
    semantic_chunk_seconds: int = 600,
    semantic_max_segments_per_chunk: int = 120,
) -> dict[str, Any]:
    """Preview or advance one episode by one explicitly confirmed action."""

    if _completion_request_rejected_early(
        episode_ref=episode_ref,
        action=action,
        confirm=confirm,
        api_cost_ack=api_cost_ack,
    ):
        return _completion_tool_error()

    return _completion_workflow_tool_call(
        operation=lambda: completion_workflow_runner.run_corpus_episode_completion_workflow(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            action=action,
            confirm=confirm,
            api_cost_ack=api_cost_ack,
            transcription_model=transcription_model,
            transcription_device=transcription_device,
            transcription_compute_type=transcription_compute_type,
            transcription_vad_filter=transcription_vad_filter,
            semantic_provider=semantic_provider,
            semantic_model=semantic_model,
            semantic_base_url=semantic_base_url,
            semantic_api_key_env=semantic_api_key_env,
            semantic_chunk_seconds=semantic_chunk_seconds,
            semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
            progress_callback=None,
        ),
        confirm=confirm,
    )


@mcp.tool()
def run_corpus_latest_episode_deterministic_workflow(
    podcast_id: str,
    confirm: bool = False,
    transcription_model: str | None = None,
    transcription_device: str = "cpu",
    transcription_compute_type: str = "int8",
    transcription_vad_filter: bool = False,
) -> dict[str, Any]:
    """Preview or process one current latest episode through local deterministic stages."""

    return _latest_deterministic_workflow_tool_call(
        operation=lambda: latest_deterministic_workflow_runner.run_corpus_latest_episode_deterministic_workflow(
            podcast_id,
            confirm=confirm,
            transcription_model=transcription_model,
            transcription_device=transcription_device,
            transcription_compute_type=transcription_compute_type,
            transcription_vad_filter=transcription_vad_filter,
        ),
        confirm=confirm,
    )


@mcp.tool()
def run_latest_episode_verified_research_report_workflow(
    podcast_id: str,
    confirm: bool = False,
    expected_episode_ref: str | None = None,
    api_cost_ack: str = "",
    stock_query: str | None = None,
    include_fixture_verification: bool = False,
    transcription_model: str | None = None,
    transcription_device: str = "cpu",
    transcription_compute_type: str = "int8",
    transcription_vad_filter: bool = False,
    semantic_provider: str = "openai-compatible",
    semantic_model: str | None = None,
    semantic_chunk_seconds: int = 600,
    semantic_max_segments_per_chunk: int = 120,
) -> dict[str, Any]:
    """Preview or complete one approved latest verified research report workflow."""

    if _verified_research_report_request_rejected_early(
        confirm=confirm,
        expected_episode_ref=expected_episode_ref,
        api_cost_ack=api_cost_ack,
    ):
        return _verified_research_report_tool_error()
    return _verified_research_report_workflow_tool_call(
        operation=lambda: verified_research_report_workflow_runner.run_latest_episode_verified_research_report_workflow(
            podcast_id,
            confirm=confirm,
            expected_episode_ref=expected_episode_ref,
            api_cost_ack=api_cost_ack,
            stock_query=stock_query,
            include_fixture_verification=include_fixture_verification,
            transcription_model=transcription_model,
            transcription_device=transcription_device,
            transcription_compute_type=transcription_compute_type,
            transcription_vad_filter=transcription_vad_filter,
            semantic_provider=semantic_provider,
            semantic_model=semantic_model,
            semantic_chunk_seconds=semantic_chunk_seconds,
            semantic_max_segments_per_chunk=semantic_max_segments_per_chunk,
        ),
        confirm=confirm,
    )


@mcp.tool()
def run_episode_verified_research_report_workflow(
    podcast_id: str,
    episode_ref: str,
    confirm: bool = False,
    stock_query: str | None = None,
    include_fixture_verification: bool = False,
) -> dict[str, Any]:
    """Preview or publish one explicit-episode verified research report (assemble only)."""

    return mcp_episode_verified_research_report.dispatch(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        confirm=confirm,
        stock_query=stock_query,
        include_fixture_verification=include_fixture_verification,
    )


def _tool_call(operation: Callable[[], Any], warnings: list[str] | None = None) -> dict[str, Any]:
    try:
        return tool_success(operation(), warnings=warnings)
    except PodcastIngestCoreError as exc:
        return tool_error(_safe_error_message(exc), type(exc).__name__)
    except ValueError as exc:
        return tool_error(str(exc), "ValueError")
    except Exception as exc:
        return tool_error(str(exc), type(exc).__name__)


def _completion_workflow_tool_call(
    *,
    operation: Callable[[], Any],
    confirm: bool,
) -> dict[str, Any]:
    """Map 016 Core results into bounded envelopes without dependency details."""

    try:
        result = operation()
        payload = completion_workflow_runner.result_to_dict(result)
    except Exception:
        return _completion_tool_error()

    if confirm:
        return tool_success(payload)
    return {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": _completion_result_requires_confirmation(result),
        "data": payload,
    }


def _latest_deterministic_workflow_tool_call(
    *,
    operation: Callable[[], Any],
    confirm: bool,
) -> dict[str, Any]:
    """Map 017 Core results into the existing bounded MCP envelope."""

    try:
        result = operation()
        payload = latest_deterministic_workflow_runner.result_to_dict(result)
    except Exception:
        return tool_error(
            _LATEST_DETERMINISTIC_WORKFLOW_TOOL_ERROR_MESSAGE,
            _LATEST_DETERMINISTIC_WORKFLOW_TOOL_ERROR_TYPE,
        )

    if confirm:
        return tool_success(payload)
    return {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": True,
        "data": payload,
    }


def _verified_research_report_workflow_tool_call(
    *, operation: Callable[[], Any], confirm: bool
) -> dict[str, Any]:
    """Map SPEC 018 Core results into a category-only bounded MCP envelope."""

    try:
        result = operation()
        payload = verified_research_report_workflow_runner.result_to_dict(result)
    except Exception:
        return _verified_research_report_tool_error()
    if confirm:
        return tool_success(payload)
    return {
        "ok": True,
        "dry_run": True,
        "requires_confirmation": True,
        "data": payload,
    }


def _verified_research_report_request_rejected_early(
    *, confirm: bool, expected_episode_ref: str | None, api_cost_ack: str
) -> bool:
    """Reject unapproved confirmed requests before RSS or Core access."""

    if not confirm:
        return False
    return (
        not isinstance(expected_episode_ref, str)
        or not _SAFE_EPISODE_REF_PATTERN.fullmatch(expected_episode_ref)
        or expected_episode_ref.casefold() == "latest"
        or api_cost_ack != SEMANTIC_API_COST_ACK
    )


def _verified_research_report_tool_error() -> dict[str, Any]:
    return tool_error(
        _VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL_ERROR_MESSAGE,
        _VERIFIED_RESEARCH_REPORT_WORKFLOW_TOOL_ERROR_TYPE,
    )


def _completion_request_rejected_early(
    *,
    episode_ref: str,
    action: str,
    confirm: bool,
    api_cost_ack: str,
) -> bool:
    """Keep invalid confirmed requests away from selection and provider work."""

    if not confirm:
        return False
    normalized_action = action.strip().casefold() if isinstance(action, str) else ""
    normalized_selector = (
        episode_ref.strip().casefold() if isinstance(episode_ref, str) else ""
    )
    if normalized_action == "next" or normalized_selector == "latest":
        return True
    return (
        normalized_action == "semantic_summary"
        and api_cost_ack != SEMANTIC_API_COST_ACK
    )


def _completion_result_requires_confirmation(result: Any) -> bool:
    selected_action = getattr(result, "selected_action", None)
    if selected_action not in _COMPLETION_EXECUTABLE_ACTIONS:
        return False
    return any(
        getattr(row, "status", None) == "selected"
        and getattr(row, "requires_confirmation", False) is True
        for row in (getattr(result, "rows", None) or ())
    )


def _completion_tool_error() -> dict[str, Any]:
    return tool_error(_COMPLETION_TOOL_ERROR_MESSAGE, _COMPLETION_TOOL_ERROR_TYPE)


def _semantic_tool_call(
    operation: Callable[[], Any],
    warnings: list[str] | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    try:
        return tool_success(operation(), warnings=warnings)
    except PodcastIngestCoreError as exc:
        return tool_error(_safe_semantic_error_message(exc, base_url), type(exc).__name__)
    except ValueError as exc:
        return tool_error(str(exc), "ValueError")
    except Exception as exc:
        return tool_error(_redact_text(str(exc), base_url), type(exc).__name__)


def _workflow_dry_run_call(
    *,
    operation: Callable[[], Any],
    inputs: dict[str, Any],
    base_urls: list[str | None],
) -> dict[str, Any]:
    try:
        result = operation()
    except PodcastIngestCoreError as exc:
        return tool_error(_safe_workflow_error_message(exc, base_urls), type(exc).__name__)
    except ValueError as exc:
        return tool_error(_redact_many(str(exc), base_urls), "ValueError")
    except Exception as exc:
        return tool_error(_redact_many(str(exc), base_urls), type(exc).__name__)

    response = tool_action_plan(
        tool_name="run_research_workflow",
        action="Run the local research workflow from existing podcast artifacts.",
        inputs=inputs,
        writes=result.planned_writes,
        risks=_unique(
            risk for step in result.steps for risk in step.risks
        ),
        requires_confirmation=result.requires_confirmation,
    )
    response["workflow_status"] = result.workflow_status
    response["transcript_status"] = result.transcript_status
    response["steps"] = to_jsonable(result.steps)
    response["planned_reads"] = result.planned_reads
    response["planned_writes"] = result.planned_writes
    response["external_api_steps"] = result.external_api_steps
    response["warnings"] = result.warnings
    response["not_investment_advice"] = result.not_investment_advice
    response["requires_api_cost_ack"] = result.requires_api_cost_ack
    if result.required_acknowledgement is not None:
        response["required_acknowledgement"] = result.required_acknowledgement
    response["next_step"] = (
        "Call this tool again with confirm=true"
        + (
            " and the exact api_cost_ack string"
            if result.requires_api_cost_ack
            else ""
        )
        + " to execute."
    )
    return response


def _workflow_tool_call(
    operation: Callable[[], Any],
    warnings: list[str] | None = None,
    base_urls: list[str | None] | None = None,
) -> dict[str, Any]:
    base_urls = base_urls or []
    try:
        return tool_success(operation(), warnings=warnings)
    except PodcastIngestCoreError as exc:
        return tool_error(_safe_workflow_error_message(exc, base_urls), type(exc).__name__)
    except ValueError as exc:
        return tool_error(_redact_many(str(exc), base_urls), "ValueError")
    except Exception as exc:
        return tool_error(_redact_many(str(exc), base_urls), type(exc).__name__)


def _episode_to_safe_dict(episode: Episode) -> dict[str, Any]:
    return {
        "podcast_id": episode.podcast_id,
        "episode_ref": episode.episode_ref,
        "title": episode.title,
        "published_at": episode.published_at,
        "duration": episode.duration,
        "guid": episode.guid,
        "link": episode.link,
        "audio_url_present": bool(episode.audio_url),
    }


def _audio_asset_to_safe_dict(audio_asset: AudioAsset) -> dict[str, Any]:
    data = to_jsonable(audio_asset)
    data.pop("source_url", None)
    data["source_url_present"] = bool(audio_asset.source_url)
    return data


def _safe_error_message(exc: PodcastIngestCoreError) -> str:
    message = str(exc)
    if isinstance(exc, SearchError) and "SQLite cache 不存在" in message and "rebuild_cache" not in message:
        return f"{message}。請先執行 rebuild_cache maintenance tool。"
    return message


def _clamp_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_LIMIT))


def _clamp_context_segments(context_segments: int) -> int:
    return max(0, min(int(context_segments), MAX_CONTEXT_SEGMENTS))


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(int(value), maximum))


def _validate_transcription_options(
    model: str, device: str, compute_type: str
) -> dict[str, Any] | None:
    if model not in ALLOWED_TRANSCRIPTION_MODELS:
        return tool_error(f"unsupported model: {model}", "ValueError")
    if device not in ALLOWED_TRANSCRIPTION_DEVICES:
        return tool_error(f"unsupported device: {device}", "ValueError")
    if compute_type not in ALLOWED_TRANSCRIPTION_COMPUTE_TYPES:
        return tool_error(f"unsupported compute_type: {compute_type}", "ValueError")
    return None


def _validate_semantic_options(provider: str, api_key_env: str) -> dict[str, Any] | None:
    if provider not in ALLOWED_SEMANTIC_PROVIDERS:
        return tool_error(f"unsupported semantic provider: {provider}", "ValueError")
    if not _SAFE_ENV_VAR_PATTERN.match(api_key_env):
        return tool_error(f"invalid api_key_env: {api_key_env}", "ValueError")
    return None


def _validate_workflow_options(
    *,
    include_stock_lens_synthesis: bool,
    stock_query: str | None,
    semantic_provider: str,
    semantic_api_key_env: str,
    synthesis_provider: str,
    synthesis_api_key_env: str,
) -> dict[str, Any] | None:
    if include_stock_lens_synthesis and not stock_query:
        return tool_error(
            "include_stock_lens_synthesis requires stock_query.",
            "ValueError",
        )
    if semantic_provider not in ALLOWED_SEMANTIC_PROVIDERS:
        return tool_error(f"unsupported semantic provider: {semantic_provider}", "ValueError")
    if synthesis_provider not in ALLOWED_SEMANTIC_PROVIDERS:
        return tool_error(
            f"unsupported synthesis provider: {synthesis_provider}",
            "ValueError",
        )
    if not _SAFE_ENV_VAR_PATTERN.match(semantic_api_key_env):
        return tool_error(f"invalid semantic_api_key_env: {semantic_api_key_env}", "ValueError")
    if not _SAFE_ENV_VAR_PATTERN.match(synthesis_api_key_env):
        return tool_error(f"invalid synthesis_api_key_env: {synthesis_api_key_env}", "ValueError")
    return None


def _semantic_transcript_preview(
    *,
    podcast_id: str,
    episode_ref: str,
    chunk_seconds: int,
    max_segments_per_chunk: int,
) -> dict[str, Any]:
    try:
        validation = validator.validate_transcript(podcast_id, episode_ref)
    except PodcastIngestCoreError as exc:
        return {
            "status": "unavailable",
            "error_type": type(exc).__name__,
            "message": _safe_error_message(exc),
        }
    except Exception as exc:
        return {
            "status": "unavailable",
            "error_type": type(exc).__name__,
            "message": str(exc),
        }

    estimated_by_segments = (
        math.ceil(validation.segment_count / max_segments_per_chunk)
        if validation.segment_count > 0
        else 0
    )
    estimated_by_time = (
        math.ceil(validation.last_segment_end_seconds / chunk_seconds)
        if validation.last_segment_end_seconds is not None
        and validation.last_segment_end_seconds > 0
        else 0
    )
    return {
        "status": validation.status,
        "valid": validation.valid,
        "segment_count": validation.segment_count,
        "last_segment_end_seconds": validation.last_segment_end_seconds,
        "problems": validation.problems,
        "warnings": validation.warnings,
        "estimated_chunk_count": max(estimated_by_segments, estimated_by_time),
    }


def _safe_semantic_error_message(exc: PodcastIngestCoreError, base_url: str | None) -> str:
    return _redact_text(_safe_error_message(exc), base_url)


def _safe_workflow_error_message(exc: PodcastIngestCoreError, base_urls: list[str | None]) -> str:
    return _redact_many(_safe_error_message(exc), base_urls)


def _redact_text(message: str, sensitive_value: str | None) -> str:
    if sensitive_value:
        return message.replace(sensitive_value, "[redacted-base-url]")
    return message


def _redact_many(message: str, sensitive_values: list[str | None]) -> str:
    redacted = message
    for sensitive_value in sensitive_values:
        redacted = _redact_text(redacted, sensitive_value)
    return redacted


def _unique(values) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
