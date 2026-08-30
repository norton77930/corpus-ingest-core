from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .canonical_transcript import resolve_canonical_transcript_asset_paths
from .config import load_podcast_profile
from .episode_claim import episode_writer_claimed
from .errors import (
    LLMProviderConfigError,
    LLMProviderRequestError,
    SemanticSummaryFailedError,
    TranscriptMissingError,
    TranscriptParseError,
)
from .llm_provider import (
    SEMANTIC_API_COST_ACK,  # noqa: F401 - re-exported as the canonical ack for research_workflow/stock_lens_synthesis/mcp_runtime and 5 scripts
    SemanticSummaryProvider,
    create_provider,
    require_exact_api_cost_ack,
)
from .models import SummaryAsset
from .storage import semantic_summary_asset_path
from .summary_profiles import SummaryProfile, resolve_summary_profile
from .validator import validate_transcript

SUMMARY_MODE = "semantic-llm"
_TIMESTAMP_EVIDENCE_PATTERN = re.compile(r"\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]")


@episode_writer_claimed
def semantic_summarize_episode(
    podcast_id: str,
    episode_ref: str,
    *,
    api_cost_ack: str = "",
    provider: str = "openai-compatible",
    model: str | None = None,
    base_url: str | None = None,
    api_key_env: str = "OPENAI_API_KEY",
    reasoning_effort: str | None = None,
    read_timeout_seconds: int = 120,
    force: bool = False,
    chunk_seconds: int = 600,
    max_segments_per_chunk: int = 120,
    allow_partial: bool = False,
    progress_callback: Callable[..., None] | None = None,
) -> SummaryAsset:
    """從已驗證逐字稿產生 LLM 語意 Markdown 摘要。

    需要 exact ``api_cost_ack``（audit F-03）：guard 在所有 early return 與
    provider construction 之前執行；dry-run 仍由 CLI/MCP/workflow 包裝層負責。
    """

    if chunk_seconds < 1:
        raise ValueError("chunk_seconds 必須大於 0。")
    if max_segments_per_chunk < 1:
        raise ValueError("max_segments_per_chunk 必須大於 0。")
    require_exact_api_cost_ack(api_cost_ack)

    profile = load_podcast_profile(podcast_id)
    summary_profile = resolve_summary_profile(profile.summary_profile)
    validation = validate_transcript(podcast_id, episode_ref)
    _raise_for_invalid_transcript(validation.status, validation.problems, allow_partial)

    transcript_paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    if transcript_paths is None:
        raise TranscriptMissingError(f"找不到逐字稿 JSON：{podcast_id}/{episode_ref}")
    if not transcript_paths.json_path.exists():
        raise TranscriptMissingError(f"找不到逐字稿 JSON：{transcript_paths.json_path}")
    if not transcript_paths.text_path.exists():
        raise TranscriptMissingError(f"找不到逐字稿 TXT：{transcript_paths.text_path}")

    payload = _load_transcript_payload(transcript_paths.json_path)
    title = _required_text(payload, "title")
    payload_podcast_id = _required_text(payload, "podcast_id")
    payload_episode_ref = _required_text(payload, "episode_ref")
    if payload_podcast_id != podcast_id or payload_episode_ref != episode_ref:
        raise TranscriptParseError("逐字稿 JSON 的 podcast_id 或 episode_ref 不符合請求。")

    segment_count = _required_int(payload, "segment_count")
    segments = _normalize_segments(payload.get("segments"))
    summary_path = semantic_summary_asset_path(podcast_id, episode_ref, title)
    if summary_path.exists() and not force:
        return _summary_asset(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            summary_path=summary_path,
            transcript_json_path=transcript_paths.json_path,
            transcript_text_path=transcript_paths.text_path,
            segment_count=segment_count,
            provider=provider,
            model=model,
            chunk_count=None,
            evidence_count=None,
            generated=False,
            already_exists=True,
        )

    chunks = _chunk_segments(
        [segment for segment in segments if segment["text"]],
        chunk_seconds=chunk_seconds,
        max_segments_per_chunk=max_segments_per_chunk,
    )
    if not chunks:
        markdown = _render_empty_markdown(
            summary_profile=summary_profile,
            display_name=profile.display_name,
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            segment_count=segment_count,
            validation_status=validation.status,
            validation_warnings=validation.warnings,
            provider_name=provider,
            model_name=model,
        )
        _write_summary(summary_path, markdown)
        return _summary_asset(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            summary_path=summary_path,
            transcript_json_path=transcript_paths.json_path,
            transcript_text_path=transcript_paths.text_path,
            segment_count=segment_count,
            provider=provider,
            model=model,
            chunk_count=0,
            evidence_count=0,
            generated=True,
            already_exists=False,
        )

    llm_provider = _build_provider(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
        reasoning_effort=reasoning_effort,
        read_timeout_seconds=read_timeout_seconds,
        api_cost_ack=api_cost_ack,
        summary_profile=summary_profile.name,
    )
    try:
        if progress_callback is not None:
            progress_callback("chunk_count", chunk_count=len(chunks), llm_requests=len(chunks) + 1)
        chunk_summaries = []
        for index, chunk in enumerate(chunks, start=1):
            if progress_callback is not None:
                progress_callback("chunk_start", index=index, total=len(chunks))
            chunk_summaries.append(llm_provider.summarize_chunk(chunk))
            if progress_callback is not None:
                progress_callback("chunk_done", index=index, total=len(chunks))
        if progress_callback is not None:
            progress_callback("final_start")
        final_summary = llm_provider.summarize_final(
            podcast_display_name=profile.display_name,
            episode_ref=episode_ref,
            title=title,
            chunk_summaries=chunk_summaries,
        )
        if progress_callback is not None:
            progress_callback("final_done")
    except (LLMProviderConfigError, LLMProviderRequestError):
        raise
    except Exception as exc:
        raise SemanticSummaryFailedError(f"語意摘要產生失敗：{exc}") from exc

    markdown = _render_semantic_markdown(
        summary_profile=summary_profile,
        display_name=profile.display_name,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        segment_count=segment_count,
        last_segment_end_seconds=validation.last_segment_end_seconds,
        validation_status=validation.status,
        validation_warnings=validation.warnings,
        provider_name=getattr(llm_provider, "provider_name", provider),
        model_name=getattr(llm_provider, "model", model),
        chunk_summaries=chunk_summaries,
        final_summary=final_summary,
    )
    _write_summary(summary_path, markdown)

    return _summary_asset(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        summary_path=summary_path,
        transcript_json_path=transcript_paths.json_path,
        transcript_text_path=transcript_paths.text_path,
        segment_count=segment_count,
        provider=getattr(llm_provider, "provider_name", provider),
        model=getattr(llm_provider, "model", model),
        chunk_count=len(chunks),
        evidence_count=_count_timestamp_evidence(final_summary),
        generated=True,
        already_exists=False,
    )


def _build_provider(
    *,
    provider: str,
    model: str | None,
    base_url: str | None,
    api_key_env: str,
    reasoning_effort: str | None,
    read_timeout_seconds: int,
    api_cost_ack: str,
    summary_profile: str,
) -> SemanticSummaryProvider:
    return create_provider(
        provider,
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
        reasoning_effort=reasoning_effort,
        read_timeout_seconds=read_timeout_seconds,
        api_cost_ack=api_cost_ack,
        summary_profile=summary_profile,
    )


def _raise_for_invalid_transcript(status: str, problems: list[str], allow_partial: bool) -> None:
    details = "; ".join(problems)
    if status == "missing":
        raise TranscriptMissingError(f"找不到逐字稿：{details}")
    if status == "incomplete_outputs":
        raise TranscriptMissingError(f"逐字稿輸出不完整：{details}")
    if status == "corrupt":
        raise TranscriptParseError(f"逐字稿 JSON 格式錯誤：{details}")
    if status == "partial" and not allow_partial:
        raise TranscriptParseError("transcript validation status is partial；請使用 --allow-partial。")


def _summary_asset(
    *,
    podcast_id: str,
    episode_ref: str,
    title: str,
    summary_path: Path,
    transcript_json_path: Path,
    transcript_text_path: Path,
    segment_count: int,
    provider: str | None,
    model: str | None,
    chunk_count: int | None,
    evidence_count: int | None,
    generated: bool,
    already_exists: bool,
) -> SummaryAsset:
    return SummaryAsset(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        summary_path=summary_path,
        transcript_json_path=transcript_json_path,
        transcript_text_path=transcript_text_path,
        segment_count=segment_count,
        summary_mode=SUMMARY_MODE,
        generated=generated,
        already_exists=already_exists,
        provider=provider,
        model=model,
        chunk_count=chunk_count,
        evidence_count=evidence_count,
    )


def _load_transcript_payload(json_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TranscriptParseError(f"逐字稿 JSON 格式錯誤：{json_path}") from exc
    except OSError as exc:
        raise TranscriptMissingError(f"無法讀取逐字稿 JSON：{exc}") from exc
    if not isinstance(payload, dict):
        raise TranscriptParseError("逐字稿 JSON 必須是 object。")
    return payload


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TranscriptParseError(f"逐字稿 JSON 缺少有效欄位：{key}")
    return value


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise TranscriptParseError(f"逐字稿 JSON 缺少有效欄位：{key}")
    return value


def _normalize_segments(raw_segments: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_segments, list):
        raise TranscriptParseError("逐字稿 JSON 的 segments 必須是 list。")

    segments: list[dict[str, Any]] = []
    for index, segment in enumerate(raw_segments, start=1):
        if not isinstance(segment, dict):
            raise TranscriptParseError("逐字稿 JSON 的每個 segment 必須是 object。")
        try:
            start = float(segment["start"])
            end = float(segment["end"])
            text = str(segment.get("text", "")).strip()
        except (KeyError, TypeError, ValueError) as exc:
            raise TranscriptParseError("逐字稿 segment 缺少 start、end 或 text。") from exc
        segments.append(
            {
                "id": segment.get("id", index),
                "start": start,
                "end": end,
                "text": text,
            }
        )
    return segments


def _chunk_segments(
    segments: list[dict[str, Any]],
    *,
    chunk_seconds: int,
    max_segments_per_chunk: int,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_window_start: int | None = None

    for segment in segments:
        segment_window_start = int(segment["start"] // chunk_seconds) * chunk_seconds
        should_start_new = current and (
            segment["start"] >= (current_window_start or 0) + chunk_seconds or len(current) >= max_segments_per_chunk
        )
        if should_start_new:
            chunks.append(_build_chunk(len(chunks) + 1, current))
            current = []
            current_window_start = segment_window_start
        elif current_window_start is None:
            current_window_start = segment_window_start
        current.append(segment)

    if current:
        chunks.append(_build_chunk(len(chunks) + 1, current))
    return chunks


def _build_chunk(index: int, segments: list[dict[str, Any]]) -> dict[str, Any]:
    start = segments[0]["start"]
    end = segments[-1]["end"]
    lines = [
        f"[{_format_clock(segment['start'])} - {_format_clock(segment['end'])}] {segment['text']}"
        for segment in segments
    ]
    return {
        "index": index,
        "start": start,
        "end": end,
        "start_time": _format_clock(start),
        "end_time": _format_clock(end),
        "segment_ids": [segment["id"] for segment in segments],
        "text": "\n".join(lines),
    }


def _render_empty_markdown(
    *,
    summary_profile: SummaryProfile,
    display_name: str,
    podcast_id: str,
    episode_ref: str,
    title: str,
    segment_count: int,
    validation_status: str,
    validation_warnings: list[str],
    provider_name: str | None,
    model_name: str | None,
) -> str:
    return _render_semantic_markdown(
        summary_profile=summary_profile,
        display_name=display_name,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        segment_count=segment_count,
        last_segment_end_seconds=None,
        validation_status=validation_status,
        validation_warnings=validation_warnings,
        provider_name=provider_name,
        model_name=model_name,
        chunk_summaries=[],
        final_summary="此 transcript 沒有可摘要的語音 segments。",
    )


def _render_semantic_markdown(
    *,
    summary_profile: SummaryProfile,
    display_name: str,
    podcast_id: str,
    episode_ref: str,
    title: str,
    segment_count: int,
    last_segment_end_seconds: float | None,
    validation_status: str,
    validation_warnings: list[str],
    provider_name: str | None,
    model_name: str | None,
    chunk_summaries: list[str],
    final_summary: str,
) -> str:
    lines = [
        f"# {display_name} - {episode_ref} 語意摘要",
        "",
        "## Metadata",
        "",
        f"- Podcast: {display_name}",
        f"- Podcast ID: {podcast_id}",
        f"- Episode: {episode_ref}",
        f"- Title: {title}",
        f"- Transcript status: {validation_status}",
        f"- Segment count: {segment_count}",
        f"- Last segment end: {_format_optional_seconds(last_segment_end_seconds)}",
        f"- Summary mode: {SUMMARY_MODE}",
        f"- Provider: {provider_name or ''}",
        f"- Model: {model_name or ''}",
        f"- Chunk count: {len(chunk_summaries)}",
        "",
        "## 摘要限制",
        "",
        *summary_profile.limitation_lines,
        "",
    ]
    if validation_warnings:
        lines.extend(["## Validation Warnings", ""])
        lines.extend(f"- {warning}" for warning in validation_warnings)
        lines.append("")

    lines.extend(
        [
            final_summary.strip(),
            "",
            "## Chunk Summaries",
            "",
        ]
    )
    if chunk_summaries:
        for index, chunk_summary in enumerate(chunk_summaries, start=1):
            lines.extend([f"### Chunk {index}", "", chunk_summary.strip(), ""])
    else:
        lines.extend(["此 transcript 沒有可摘要的語音 segments。", ""])
    return "\n".join(lines)


def _format_optional_seconds(seconds: float | None) -> str:
    if seconds is None:
        return ""
    return f"{seconds:.2f}"


def _format_clock(seconds: float) -> str:
    whole_seconds = max(0, int(seconds))
    hours, remainder = divmod(whole_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _count_timestamp_evidence(markdown: str) -> int:
    return len(_TIMESTAMP_EVIDENCE_PATTERN.findall(markdown))


def _write_summary(summary_path: Path, markdown: str) -> None:
    part_path = summary_path.with_name(f"{summary_path.name}.part")
    try:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        part_path.unlink(missing_ok=True)
        part_path.write_text(markdown, encoding="utf-8")
        part_path.replace(summary_path)
    except OSError as exc:
        try:
            part_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise SemanticSummaryFailedError(f"寫入語意摘要失敗：{exc}") from exc
