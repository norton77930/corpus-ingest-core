from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import load_podcast_profile
from .downloader import download_audio
from .errors import (
    AudioFileMissingError,
    TranscriptionDependencyError,
    TranscriptionFailedError,
)
from .models import AudioAsset, TranscriptAsset
from .storage import transcript_asset_paths
from .episode_claim import episode_writer_claimed
from .validator import validate_transcript


DEFAULT_TRANSCRIPTION_MODEL = "tiny"
PROGRESS_WRITE_INTERVAL = 25


@episode_writer_claimed
def transcribe_episode(
    podcast_id: str,
    episode_ref: str,
    model: str | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
    vad_filter: bool = False,
    force: bool = False,
    *,
    audio_path: str | Path | None = None,
    progress_callback: Callable[[int, float | None], None] | None = None,
) -> TranscriptAsset:
    """使用 faster-whisper 將已下載的 episode 音檔轉成逐字稿。"""

    model_name = model or DEFAULT_TRANSCRIPTION_MODEL
    profile = load_podcast_profile(podcast_id)
    audio_asset = (
        _audio_asset_from_path(podcast_id, episode_ref, audio_path)
        if audio_path is not None
        else download_audio(podcast_id, episode_ref)
    )
    if not audio_asset.local_path.exists():
        raise AudioFileMissingError(f"找不到本機音檔：{audio_asset.local_path}")

    paths = transcript_asset_paths(
        audio_asset.podcast_id, audio_asset.episode_ref, audio_asset.title
    )
    if not force and _all_transcript_outputs_exist(paths):
        validation = validate_transcript(audio_asset.podcast_id, audio_asset.episode_ref)
        if validation.status not in {"valid", "empty"}:
            raise TranscriptionFailedError(
                f"既有逐字稿狀態為 {validation.status}，請使用 --force 重新轉錄。"
            )
        return TranscriptAsset(
            podcast_id=audio_asset.podcast_id,
            episode_ref=audio_asset.episode_ref,
            title=audio_asset.title,
            audio_path=audio_asset.local_path,
            text_path=paths.text_path,
            srt_path=paths.srt_path,
            json_path=paths.json_path,
            model=model_name,
            language=profile.language,
            segment_count=_existing_segment_count(paths.json_path),
            device=device,
            compute_type=compute_type,
            vad_filter=vad_filter,
            transcribed=False,
            already_exists=True,
        )

    whisper_model_class = _load_whisper_model_class()
    try:
        _cleanup_paths(_transcript_part_paths(paths))
        whisper_model = whisper_model_class(
            model_name, device=device, compute_type=compute_type
        )
        raw_segments, _info = whisper_model.transcribe(
            str(audio_asset.local_path),
            language=profile.language,
            beam_size=5,
            vad_filter=vad_filter,
        )
        segments = _consume_segments(
            raw_segments=raw_segments,
            paths=paths,
            audio_asset=audio_asset,
            model_name=model_name,
            language=profile.language,
            device=device,
            compute_type=compute_type,
            vad_filter=vad_filter,
            progress_callback=progress_callback,
        )
        _write_transcript_outputs(
            paths=paths,
            audio_asset=audio_asset,
            model_name=model_name,
            language=profile.language,
            device=device,
            compute_type=compute_type,
            vad_filter=vad_filter,
            segments=segments,
            completed=True,
        )
    except TranscriptionFailedError:
        raise
    except Exception as exc:
        raise TranscriptionFailedError(f"轉錄失敗：{exc}") from exc

    return TranscriptAsset(
        podcast_id=audio_asset.podcast_id,
        episode_ref=audio_asset.episode_ref,
        title=audio_asset.title,
        audio_path=audio_asset.local_path,
        text_path=paths.text_path,
        srt_path=paths.srt_path,
        json_path=paths.json_path,
        model=model_name,
        language=profile.language,
        segment_count=len(segments),
        device=device,
        compute_type=compute_type,
        vad_filter=vad_filter,
        transcribed=True,
        already_exists=False,
    )


def _audio_asset_from_path(
    podcast_id: str, episode_ref: str, audio_path: str | Path
) -> AudioAsset:
    local_path = Path(audio_path)
    size_bytes = local_path.stat().st_size if local_path.exists() else None
    return AudioAsset(
        podcast_id=podcast_id,
        episode_ref=episode_ref,
        title=episode_ref,
        source_url=str(local_path),
        local_path=local_path,
        size_bytes=size_bytes,
        downloaded=False,
        already_exists=True,
    )


def _load_whisper_model_class():
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise TranscriptionDependencyError("faster-whisper 未安裝。") from exc
    return WhisperModel


def _all_transcript_outputs_exist(paths) -> bool:
    return paths.text_path.exists() and paths.srt_path.exists() and paths.json_path.exists()


def _existing_segment_count(json_path) -> int:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    value = payload.get("segment_count", 0)
    return value if isinstance(value, int) else 0


def _segment_to_dict(segment: Any, index: int) -> dict[str, Any]:
    return {
        "id": getattr(segment, "id", index + 1),
        "start": float(getattr(segment, "start")),
        "end": float(getattr(segment, "end")),
        "text": str(getattr(segment, "text")).strip(),
    }


def _consume_segments(
    *,
    raw_segments,
    paths,
    audio_asset,
    model_name: str,
    language: str,
    device: str,
    compute_type: str,
    vad_filter: bool,
    progress_callback: Callable[[int, float | None], None] | None,
) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for index, segment in enumerate(raw_segments):
        segments.append(_segment_to_dict(segment, index))
        last_end = _last_segment_end(segments)
        if progress_callback is not None:
            progress_callback(len(segments), last_end)
        if len(segments) % PROGRESS_WRITE_INTERVAL == 0:
            _write_progress_output(
                paths=paths,
                audio_asset=audio_asset,
                model_name=model_name,
                language=language,
                device=device,
                compute_type=compute_type,
                vad_filter=vad_filter,
                segments=segments,
            )

    _write_progress_output(
        paths=paths,
        audio_asset=audio_asset,
        model_name=model_name,
        language=language,
        device=device,
        compute_type=compute_type,
        vad_filter=vad_filter,
        segments=segments,
    )
    return segments


def _write_transcript_outputs(
    *,
    paths,
    audio_asset,
    model_name: str,
    language: str,
    device: str,
    compute_type: str,
    vad_filter: bool,
    segments: list[dict[str, Any]],
    completed: bool,
) -> None:
    part_paths = _transcript_part_paths(paths)
    try:
        paths.text_path.parent.mkdir(parents=True, exist_ok=True)
        _cleanup_paths(part_paths)
        part_paths[0].write_text(
            "".join(f"{segment['text']}\n" for segment in segments),
            encoding="utf-8",
        )
        part_paths[1].write_text(_segments_to_srt(segments), encoding="utf-8")
        payload = {
            "podcast_id": audio_asset.podcast_id,
            "episode_ref": audio_asset.episode_ref,
            "title": audio_asset.title,
            "model": model_name,
            "language": language,
            "device": device,
            "compute_type": compute_type,
            "vad_filter": vad_filter,
            "generated_at": _utc_now_iso(),
            "source_audio_path": str(audio_asset.local_path),
            "source_audio_size_bytes": _audio_size_bytes(audio_asset),
            "last_segment_end_seconds": _last_segment_end(segments),
            "completed": completed,
            "audio_path": str(audio_asset.local_path),
            "text_path": str(paths.text_path),
            "srt_path": str(paths.srt_path),
            "json_path": str(paths.json_path),
            "segment_count": len(segments),
            "segments": segments,
        }
        part_paths[2].write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        for part_path, target_path in zip(
            part_paths, [paths.text_path, paths.srt_path, paths.json_path]
        ):
            part_path.replace(target_path)
    except OSError as exc:
        _cleanup_paths(part_paths)
        raise TranscriptionFailedError(f"寫入逐字稿失敗：{exc}") from exc


def _write_progress_output(
    *,
    paths,
    audio_asset,
    model_name: str,
    language: str,
    device: str,
    compute_type: str,
    vad_filter: bool,
    segments: list[dict[str, Any]],
) -> None:
    progress_path = _part_path(paths.json_path)
    payload = {
        "podcast_id": audio_asset.podcast_id,
        "episode_ref": audio_asset.episode_ref,
        "title": audio_asset.title,
        "model": model_name,
        "language": language,
        "device": device,
        "compute_type": compute_type,
        "vad_filter": vad_filter,
        "generated_at": _utc_now_iso(),
        "source_audio_path": str(audio_asset.local_path),
        "source_audio_size_bytes": _audio_size_bytes(audio_asset),
        "last_segment_end_seconds": _last_segment_end(segments),
        "completed": False,
        "segment_count": len(segments),
        "segments": segments,
    }
    try:
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        progress_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        raise TranscriptionFailedError(f"寫入轉錄進度失敗：{exc}") from exc


def _part_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.part")


def _transcript_part_paths(paths) -> list[Path]:
    return [_part_path(paths.text_path), _part_path(paths.srt_path), _part_path(paths.json_path)]


def _cleanup_paths(paths: list[Path]) -> None:
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _audio_size_bytes(audio_asset) -> int | None:
    if audio_asset.size_bytes is not None:
        return audio_asset.size_bytes
    try:
        return audio_asset.local_path.stat().st_size
    except OSError:
        return None


def _last_segment_end(segments: list[dict[str, Any]]) -> float | None:
    if not segments:
        return None
    return float(segments[-1]["end"])


def _segments_to_srt(segments: list[dict[str, Any]]) -> str:
    blocks = []
    for index, segment in enumerate(segments, start=1):
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{_format_srt_timestamp(segment['start'])} --> {_format_srt_timestamp(segment['end'])}",
                    segment["text"],
                ]
            )
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def _format_srt_timestamp(seconds: float) -> str:
    milliseconds_total = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds_total, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"
