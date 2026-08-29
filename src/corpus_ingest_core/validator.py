from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import storage
from .canonical_transcript import resolve_canonical_transcript_asset_paths
from .models import TranscriptValidationResult

VALIDATION_STATUSES = {
    "missing",
    "valid",
    "empty",
    "partial",
    "corrupt",
    "incomplete_outputs",
}


def validate_transcript(podcast_id: str, episode_ref: str) -> TranscriptValidationResult:
    """檢查指定 episode 的 transcript outputs 是否完整且可用。"""

    paths = resolve_canonical_transcript_asset_paths(podcast_id, episode_ref)
    if paths is None:
        part_paths = _candidate_part_paths(podcast_id, episode_ref)
        warnings = [
            f"發現殘留 .part 檔：{part_path}" for part_path in part_paths if part_path.exists()
        ]
        return TranscriptValidationResult(
            podcast_id=podcast_id,
            episode_ref=episode_ref,
            valid=False,
            status="missing",
            segment_count=0,
            last_segment_end_seconds=None,
            transcript_text_length=0,
            problems=[f"找不到 transcript JSON：{podcast_id}/{episode_ref}"],
            warnings=warnings,
            paths=_paths_dict(None, part_paths),
        )

    part_paths = [
        _part_path(paths.text_path),
        _part_path(paths.srt_path),
        _part_path(paths.json_path),
    ]
    problems: list[str] = []
    warnings = [
        f"發現殘留 .part 檔：{part_path}" for part_path in part_paths if part_path.exists()
    ]

    missing_outputs = []
    if not paths.json_path.exists():
        missing_outputs.append("JSON")
    if not paths.text_path.exists():
        missing_outputs.append("TXT")
    if not paths.srt_path.exists():
        missing_outputs.append("SRT")
    if missing_outputs:
        problems.extend(f"缺少 transcript {name} 輸出。" for name in missing_outputs)
        return _result(
            podcast_id,
            episode_ref,
            "incomplete_outputs",
            False,
            0,
            None,
            _text_length(paths.text_path),
            problems,
            warnings,
            paths,
            part_paths,
        )

    payload = _load_json(paths.json_path, problems)
    if payload is None:
        return _result(
            podcast_id,
            episode_ref,
            "corrupt",
            False,
            0,
            None,
            _text_length(paths.text_path),
            problems,
            warnings,
            paths,
            part_paths,
        )

    segments = payload.get("segments")
    if not isinstance(segments, list):
        problems.append("逐字稿 JSON 的 segments 必須是 list。")
        return _result(
            podcast_id,
            episode_ref,
            "corrupt",
            False,
            _safe_int(payload.get("segment_count")),
            None,
            _text_length(paths.text_path),
            problems,
            warnings,
            paths,
            part_paths,
        )

    normalized_segments = _normalize_segments(segments, problems)
    if problems:
        return _result(
            podcast_id,
            episode_ref,
            "corrupt",
            False,
            _safe_int(payload.get("segment_count")),
            None,
            _text_length(paths.text_path),
            problems,
            warnings,
            paths,
            part_paths,
        )

    segment_count = _safe_int(payload.get("segment_count"))
    last_segment_end = normalized_segments[-1]["end"] if normalized_segments else None
    text_length = _text_length(paths.text_path)
    srt_length = _text_length(paths.srt_path)
    _add_legacy_metadata_warnings(payload, warnings)

    partial_problems: list[str] = []
    if payload.get("completed") is False:
        partial_problems.append("transcript JSON 標示 completed=false。")
    if segment_count != len(normalized_segments):
        partial_problems.append(
            f"segment_count={segment_count} 與 segments 長度 {len(normalized_segments)} 不一致。"
        )
    if normalized_segments and text_length == 0:
        partial_problems.append("segments 非空但 TXT 沒有內容。")
    if normalized_segments and srt_length == 0:
        partial_problems.append("segments 非空但 SRT 沒有內容。")
    if partial_problems:
        problems.extend(partial_problems)
        return _result(
            podcast_id,
            episode_ref,
            "partial",
            False,
            segment_count,
            last_segment_end,
            text_length,
            problems,
            warnings,
            paths,
            part_paths,
        )

    status = "empty" if not normalized_segments else "valid"
    return _result(
        podcast_id,
        episode_ref,
        status,
        True,
        segment_count,
        last_segment_end,
        text_length,
        problems,
        warnings,
        paths,
        part_paths,
    )


def _candidate_part_paths(podcast_id: str, episode_ref: str) -> list[Path]:
    transcript_dir = storage.TRANSCRIPTS_DIR / podcast_id
    return sorted(transcript_dir.glob(f"{episode_ref}__*.part"))


def _part_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.part")


def _paths_dict(paths, part_paths: list[Path]) -> dict[str, str]:
    result: dict[str, str] = {}
    if paths is not None:
        result.update(
            {
                "text": str(paths.text_path),
                "srt": str(paths.srt_path),
                "json": str(paths.json_path),
            }
        )
    for part_path in part_paths:
        if not part_path.exists():
            continue
        if part_path.name.endswith(".txt.part"):
            key = "text_part"
        elif part_path.name.endswith(".srt.part"):
            key = "srt_part"
        elif part_path.name.endswith(".json.part"):
            key = "json_part"
        else:
            key = f"part_{len(result)}"
        result[key] = str(part_path)
    return result


def _result(
    podcast_id: str,
    episode_ref: str,
    status: str,
    valid: bool,
    segment_count: int,
    last_segment_end_seconds: float | None,
    transcript_text_length: int,
    problems: list[str],
    warnings: list[str],
    paths,
    part_paths: list[Path],
) -> TranscriptValidationResult:
    if status not in VALIDATION_STATUSES:
        raise ValueError(f"未知 transcript validation status：{status}")
    return TranscriptValidationResult(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        valid=valid,
        status=status,
        segment_count=segment_count,
        last_segment_end_seconds=last_segment_end_seconds,
        transcript_text_length=transcript_text_length,
        problems=problems,
        warnings=warnings,
        paths=_paths_dict(paths, part_paths),
    )


def _load_json(json_path: Path, problems: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        problems.append(f"transcript JSON 無法 parse：{json_path}")
        return None
    except OSError as exc:
        problems.append(f"transcript JSON 無法讀取：{exc}")
        return None
    if not isinstance(payload, dict):
        problems.append("transcript JSON 必須是 object。")
        return None
    return payload


def _normalize_segments(
    segments: list[Any], problems: list[str]
) -> list[dict[str, float | str | int]]:
    normalized = []
    previous_start = 0.0
    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            problems.append(f"segment {index} 不是 object。")
            continue
        try:
            start = float(segment["start"])
            end = float(segment["end"])
            text = str(segment.get("text", "")).strip()
        except (KeyError, TypeError, ValueError):
            problems.append(f"segment {index} 缺少可解析 start/end/text。")
            continue
        if start < 0 or end < 0 or end < start:
            problems.append(f"segment {index} 時間戳不合理。")
            continue
        if start < previous_start:
            problems.append(f"segment {index} start 時間倒退。")
            continue
        previous_start = start
        normalized.append(
            {"id": segment.get("id", index), "start": start, "end": end, "text": text}
        )
    return normalized


def _text_length(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8"))
    except OSError:
        return 0


def _safe_int(value: Any) -> int:
    return value if isinstance(value, int) else 0


def _add_legacy_metadata_warnings(payload: dict[str, Any], warnings: list[str]) -> None:
    legacy_keys = [
        "completed",
        "generated_at",
        "source_audio_path",
        "source_audio_size_bytes",
    ]
    missing = [key for key in legacy_keys if key not in payload]
    if missing:
        warnings.append(f"legacy transcript metadata missing: {', '.join(missing)}")
