from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
from typing import Any

from .config import load_podcast_profile
from .errors import SummaryFailedError, TranscriptMissingError, TranscriptParseError
from .models import SummaryAsset
from .storage import (
    find_transcript_asset_paths,
    summary_asset_path,
)
from .validator import validate_transcript


SUMMARY_MODE = "extractive-template"


def summarize_episode(
    podcast_id: str,
    episode_ref: str,
    *,
    force: bool = False,
    max_quotes: int = 10,
    window_seconds: int = 300,
    allow_partial: bool = False,
) -> SummaryAsset:
    """從既有逐字稿產生 deterministic Markdown 摘要。"""

    if max_quotes < 0:
        raise ValueError("max_quotes 不可小於 0。")
    if window_seconds < 1:
        raise ValueError("window_seconds 必須大於 0。")

    profile = load_podcast_profile(podcast_id)
    validation = validate_transcript(podcast_id, episode_ref)
    if validation.status == "missing":
        raise TranscriptMissingError(f"找不到逐字稿 JSON：{podcast_id}/{episode_ref}")
    if validation.status == "incomplete_outputs":
        raise TranscriptMissingError(
            f"逐字稿輸出不完整：{'; '.join(validation.problems)}"
        )
    if validation.status == "corrupt":
        raise TranscriptParseError(f"逐字稿 JSON 格式錯誤：{'; '.join(validation.problems)}")
    if validation.status == "partial" and not allow_partial:
        raise TranscriptParseError("transcript validation status is partial；請使用 --allow-partial。")

    transcript_paths = find_transcript_asset_paths(podcast_id, episode_ref)
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
    summary_path = summary_asset_path(podcast_id, episode_ref, title)
    if summary_path.exists() and not force:
        return _summary_asset(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            title=title,
            summary_path=summary_path,
            transcript_json_path=transcript_paths.json_path,
            transcript_text_path=transcript_paths.text_path,
            segment_count=segment_count,
            generated=False,
            already_exists=True,
        )

    try:
        transcript_text = transcript_paths.text_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TranscriptMissingError(f"無法讀取逐字稿 TXT：{exc}") from exc

    markdown = _render_markdown(
        display_name=profile.display_name,
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=title,
        segment_count=segment_count,
        transcript_text=transcript_text,
        segments=segments,
        max_quotes=max_quotes,
        window_seconds=window_seconds,
        validation_status=validation.status,
        validation_warnings=validation.warnings,
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
        generated=True,
        already_exists=False,
    )


def _summary_asset(
    *,
    podcast_id: str,
    episode_ref: str,
    title: str,
    summary_path: Path,
    transcript_json_path: Path,
    transcript_text_path: Path,
    segment_count: int,
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
            text = str(segment["text"]).strip()
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


def _render_markdown(
    *,
    display_name: str,
    podcast_id: str,
    episode_ref: str,
    title: str,
    segment_count: int,
    transcript_text: str,
    segments: list[dict[str, Any]],
    max_quotes: int,
    window_seconds: int,
    validation_status: str,
    validation_warnings: list[str],
) -> str:
    non_empty_segments = [segment for segment in segments if segment["text"]]
    lines = [
        f"# {display_name} - {episode_ref} 摘要",
        "",
        "## Metadata",
        "",
        f"- Podcast: {display_name}",
        f"- Podcast ID: {podcast_id}",
        f"- Episode: {episode_ref}",
        f"- Title: {title}",
        f"- Transcript segments: {segment_count}",
        f"- Summary mode: {SUMMARY_MODE}",
        f"- Validation status: {validation_status}",
        "",
        "## 摘要狀態",
        "",
        "本摘要由 deterministic extractive-template summarizer 產生。",
        "它不使用外部 LLM，因此不會產生無法追溯到逐字稿的主觀推論。",
        "",
        "## 本集概覽",
        "",
        f"- 逐字稿總段落數：{segment_count}",
        f"- 估計音檔長度：{_estimated_duration(segments)}",
        f"- 可用文字長度：{len(transcript_text)} 字元",
        "",
        "## 時間軸摘要",
        "",
    ]
    if validation_warnings:
        lines.extend(["### Validation warnings", ""])
        lines.extend(f"- {warning}" for warning in validation_warnings)
        lines.append("")

    if not non_empty_segments:
        lines.extend(["此 transcript 沒有可摘要的語音 segments。", ""])
    else:
        lines.extend(_timeline_lines(non_empty_segments, window_seconds))

    lines.extend(["## 可引用片段", ""])
    if not non_empty_segments or max_quotes == 0:
        lines.extend(["沒有可引用片段。", ""])
    else:
        for index, segment in enumerate(non_empty_segments[:max_quotes], start=1):
            lines.append(
                f"{index}. `[{_format_clock(segment['start'])} - {_format_clock(segment['end'])}]` {segment['text']}"
            )
        lines.append("")

    lines.extend(
        [
            "## 待 LLM 深度摘要 Prompt",
            "",
            "請根據本集逐字稿整理：",
            "1. 本集主題",
            "2. 市場觀點",
            "3. 提到的公司 / 股票 / 產業",
            "4. 總經觀點",
            "5. 生活閒聊",
            "6. 廣告段落",
            "7. 可驗證時間戳引用",
            "",
            "限制：",
            "- 不要產生投資建議。",
            "- 所有判斷都要能回到逐字稿。",
            "",
        ]
    )
    return "\n".join(lines)


def _timeline_lines(segments: list[dict[str, Any]], window_seconds: int) -> list[str]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for segment in segments:
        window_start = int(segment["start"] // window_seconds) * window_seconds
        grouped[window_start].append(segment)

    lines: list[str] = []
    for window_start in sorted(grouped):
        window_end = window_start + window_seconds
        lines.extend(
            [
                f"### {_format_clock(window_start)} - {_format_clock(window_end)}",
                "",
            ]
        )
        for segment in grouped[window_start][:3]:
            lines.extend(["- 代表片段：", f"  > {segment['text']}", ""])
    return lines


def _estimated_duration(segments: list[dict[str, Any]]) -> str:
    if not segments:
        return "0 秒"
    return _format_clock(max(segment["end"] for segment in segments))


def _format_clock(seconds: float) -> str:
    whole_seconds = max(0, int(seconds))
    hours, remainder = divmod(whole_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


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
        raise SummaryFailedError(f"寫入摘要失敗：{exc}") from exc
