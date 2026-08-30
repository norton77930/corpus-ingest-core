"""把 YouTube 影片取得成 corpus 音訊資產。

取得邏輯與 X 共用 ``video_acquire``；本模組只負責身分、seed 與 source_type。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from . import storage, video_acquire
from .config import load_podcast_profile
from .errors import (
    PodcastIngestCoreError,
    YoutubeVideoIngestDependencyError,
    YoutubeVideoIngestFailedError,
)
from .models import CorpusEpisodeSeed, YoutubeVideoIdentity, YoutubeVideoIngestResult
from .run_report_io import write_part_staged_report_pair
from .transcriber import transcribe_episode

YT_SOURCE_TYPE = "yt-video"
RUN_MODE_PREVIEW = "preview"
RUN_MODE_CONFIRMED = "confirmed"
_WHITESPACE_PATTERN = re.compile(r"\s+")
_UPLOAD_DATE_PATTERN = re.compile(r"^(\d{4})(\d{2})(\d{2})$")
_VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
_HANDLE_IN_PATH = re.compile(r"/@(?P<handle>[^/]+)")
_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}

CACHE_STALE_WARNING = (
    "SQLite cache may be stale; rebuild cache manually. 本流程不會自動重建，這一集要等你手動重建 cache 之後才搜尋得到。"
)


def derive_youtube_identity(url: str, info: dict[str, Any] | None = None) -> YoutubeVideoIdentity:
    """從網址（以及必要時的 metadata）推導 podcast_id 與 episode_ref。"""

    video_id = parse_youtube_video_id(url)
    handle = _usable_handle(url, info)
    if handle is not None:
        channel_slug = _handle_slug(handle)
        podcast_id = f"yt-{channel_slug}"
    else:
        channel_id = _channel_id_from_info(info)
        if channel_id is None:
            raise ValueError(f"Could not derive a YouTube podcast_id: {url}")
        channel_slug = _channel_id_slug(channel_id)
        podcast_id = f"yt-{channel_slug}"
    storage._safe_slug(podcast_id, "podcast_id")
    storage._safe_episode_ref(video_id)
    return YoutubeVideoIdentity(
        podcast_id=podcast_id,
        episode_ref=video_id,
        channel_slug=channel_slug,
        canonical_url=canonical_watch_url(video_id),
    )


def parse_youtube_video_id(url: str) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if host not in _YOUTUBE_HOSTS:
        raise ValueError(f"Not a YouTube video URL: {url}")

    candidate = ""
    if host in {"youtu.be", "www.youtu.be"}:
        candidate = parsed.path.strip("/").split("/", 1)[0]
    else:
        query_id = parse_qs(parsed.query).get("v", [""])[0]
        if query_id:
            candidate = query_id
        else:
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live", "v"}:
                candidate = parts[1]
    if candidate[:1] in {"-", "_"}:
        raise ValueError("A YouTube video id must not start with - or _")
    if not _VIDEO_ID_PATTERN.fullmatch(candidate):
        raise ValueError(f"Not a YouTube video URL: {url}")
    return candidate


def canonical_watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def build_seed(
    identity: YoutubeVideoIdentity,
    info: dict[str, Any],
    title: str | None = None,
) -> CorpusEpisodeSeed:
    warnings: list[str] = []
    published_at = _published_at(info.get("upload_date"))
    if published_at is None:
        warnings.append("published_at 未知：來源 metadata 沒有 upload_date。")

    return CorpusEpisodeSeed(
        podcast_id=identity.podcast_id,
        episode_ref=identity.episode_ref,
        title=_resolve_title(title, info, identity),
        published_at=published_at,
        duration=_duration_label(info.get("duration")),
        guid_status="present",
        has_audio_url=True,
        seed_source=YT_SOURCE_TYPE,
        selector=identity.canonical_url,
        warning_count=len(warnings),
        warnings=warnings,
        not_investment_advice=True,
    )


def run_youtube_video_ingest(
    url: str,
    *,
    confirm: bool = False,
    title: str | None = None,
    model: str | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
    force: bool = False,
    work_dir: str | Path | None = None,
) -> YoutubeVideoIngestResult:
    parse_youtube_video_id(url)
    try:
        info = _resolve_metadata(url)
    except PodcastIngestCoreError:
        raise
    except Exception as exc:
        raise YoutubeVideoIngestFailedError(f"Failed to resolve source metadata: {exc}") from exc

    identity = derive_youtube_identity(url, info)
    seed = build_seed(identity, info, title)

    audio_target = storage.audio_asset_path(identity.podcast_id, identity.episode_ref, seed.title, ".wav")
    seed_target = storage.corpus_episode_seed_asset_path(identity.podcast_id, identity.episode_ref)
    transcript_targets = storage.transcript_asset_paths(identity.podcast_id, identity.episode_ref, seed.title)
    warnings = [*seed.warnings, CACHE_STALE_WARNING]
    registration_problem = _registration_problem(identity.podcast_id)
    if registration_problem is not None:
        warnings.append(registration_problem)

    audio_exists = audio_target.exists()
    if audio_exists:
        warnings.append(f"沿用既有音訊，未重新下載：{audio_target}")

    report_paths = storage.youtube_video_ingest_run_asset_paths(identity.podcast_id, identity.episode_ref)
    planned_writes = [str(seed_target)]
    if not audio_exists:
        planned_writes.append(str(audio_target))
    planned_writes.extend(
        [
            str(transcript_targets.text_path),
            str(transcript_targets.srt_path),
            str(transcript_targets.json_path),
            str(report_paths.json_path),
            str(report_paths.markdown_path),
        ]
    )

    if not confirm:
        return YoutubeVideoIngestResult(
            podcast_id=identity.podcast_id,
            episode_ref=identity.episode_ref,
            title=seed.title,
            canonical_url=identity.canonical_url,
            confirmed=False,
            run_mode=RUN_MODE_PREVIEW,
            planned_writes=planned_writes,
            audio_path=None,
            seed_path=None,
            transcript_json_path=None,
            report_json_path=None,
            report_markdown_path=None,
            warnings=warnings,
            not_investment_advice=True,
        )

    if registration_problem is not None:
        raise YoutubeVideoIngestFailedError(registration_problem)

    if not audio_exists:
        _acquire_audio(identity.canonical_url, audio_target, work_dir)

    _write_seed(seed_target, seed)

    transcript = transcribe_episode(
        identity.podcast_id,
        identity.episode_ref,
        model=model,
        device=device,
        compute_type=compute_type,
        vad_filter=True,
        force=force,
        audio_path=audio_target,
        title=seed.title,
    )

    result = YoutubeVideoIngestResult(
        podcast_id=identity.podcast_id,
        episode_ref=identity.episode_ref,
        title=seed.title,
        canonical_url=identity.canonical_url,
        confirmed=True,
        run_mode=RUN_MODE_CONFIRMED,
        planned_writes=planned_writes,
        audio_path=str(audio_target),
        seed_path=str(seed_target),
        transcript_json_path=str(transcript.json_path),
        report_json_path=str(report_paths.json_path),
        report_markdown_path=str(report_paths.markdown_path),
        warnings=warnings,
        not_investment_advice=True,
    )
    _write_run_report(result)
    return result


def _resolve_metadata(url: str) -> dict[str, Any]:
    return video_acquire.resolve_metadata(
        url,
        failed_error=YoutubeVideoIngestFailedError,
        dependency_error=YoutubeVideoIngestDependencyError,
    )


def _download_video(url: str, target_dir: Path) -> Path:
    return video_acquire.download_video(
        url,
        target_dir,
        failed_error=YoutubeVideoIngestFailedError,
        dependency_error=YoutubeVideoIngestDependencyError,
    )


def _extract_audio(video_path: Path, audio_path: Path) -> None:
    video_acquire.extract_audio(
        video_path,
        audio_path,
        failed_error=YoutubeVideoIngestFailedError,
        dependency_error=YoutubeVideoIngestDependencyError,
    )


def _work_dir_is_under_data(work_dir: str | Path) -> bool:
    """Lexical containment, same algorithm as the catalog helper.

    Use abspath+normcase+commonpath on the path we will actually pass to
    yt-dlp. resolve() follows junctions and can conclude a data/ path is
    outside, then the download still writes through the data/ path.
    """

    try:
        root = os.path.normcase(os.path.abspath(str(storage.DATA_DIR)))
        candidate = os.path.normcase(os.path.abspath(str(work_dir)))
        return os.path.commonpath((root, candidate)) == root
    except (OSError, ValueError):
        return False


def _acquire_audio(url: str, audio_target: Path, work_dir: str | Path | None) -> None:
    owns_work_dir = work_dir is None
    if work_dir is None:
        resolved_work_dir = Path(tempfile.mkdtemp(prefix="yt-video-"))
    else:
        if _work_dir_is_under_data(work_dir):
            raise YoutubeVideoIngestFailedError(
                "work_dir must not sit under data/; source video must never be written into the corpus tree."
            )
        resolved_work_dir = Path(os.path.abspath(str(work_dir)))
    part_path = audio_target.with_suffix(audio_target.suffix + ".part")
    try:
        video_path = _download_video(url, resolved_work_dir)
        audio_target.parent.mkdir(parents=True, exist_ok=True)
        part_path.unlink(missing_ok=True)
        _extract_audio(video_path, part_path)
        part_path.replace(audio_target)
    except PodcastIngestCoreError:
        raise
    except Exception as exc:
        raise YoutubeVideoIngestFailedError(f"Audio acquisition failed: {exc}") from exc
    finally:
        try:
            part_path.unlink(missing_ok=True)
        except OSError:
            pass
        if owns_work_dir:
            shutil.rmtree(resolved_work_dir, ignore_errors=True)


def _write_run_report(result: YoutubeVideoIngestResult) -> None:
    if result.report_json_path is None or result.report_markdown_path is None:
        return
    payload = asdict(result)
    markdown = "\n".join(
        [
            f"# YouTube Video Ingest - {payload['podcast_id']} / {payload['episode_ref']}",
            "",
            f"- Run mode: {payload['run_mode']}",
            f"- Title: {payload['title']}",
            f"- Canonical URL: {payload['canonical_url']}",
            f"- Audio: {payload['audio_path']}",
            f"- Seed: {payload['seed_path']}",
            f"- Transcript JSON: {payload['transcript_json_path']}",
            f"- Not investment advice: {payload['not_investment_advice']}",
            "",
        ]
    )
    try:
        write_part_staged_report_pair(
            Path(result.report_json_path),
            Path(result.report_markdown_path),
            payload,
            markdown,
        )
    except OSError as exc:
        raise YoutubeVideoIngestFailedError(
            f"failed to write youtube-video ingest run report: {type(exc).__name__}"
        ) from exc


def _write_seed(seed_target: Path, seed: CorpusEpisodeSeed) -> None:
    seed_target.parent.mkdir(parents=True, exist_ok=True)
    part_path = seed_target.with_name(f"{seed_target.name}.part")
    try:
        part_path.unlink(missing_ok=True)
        part_path.write_text(json.dumps(asdict(seed), ensure_ascii=False, indent=2), encoding="utf-8")
        part_path.replace(seed_target)
    except OSError:
        part_path.unlink(missing_ok=True)
        raise


def _registration_problem(podcast_id: str) -> str | None:
    try:
        profile = load_podcast_profile(podcast_id)
    except KeyError:
        return (
            f"config/podcasts.yaml 還沒有 {podcast_id}。請先加入一段："
            f"{podcast_id}: display_name / source_type: {YT_SOURCE_TYPE} / language。"
        )
    if profile.source_type != YT_SOURCE_TYPE:
        return (
            f"{podcast_id} 的 source_type 是 {profile.source_type}，不是 "
            f"{YT_SOURCE_TYPE}；這條擷取流程只處理 YouTube 影片來源。"
        )
    return None


def _handle_from_url(url: str) -> str | None:
    match = _HANDLE_IN_PATH.search(urlparse(url.strip()).path)
    return match.group("handle") if match else None


def _usable_handle(url: str, info: dict[str, Any] | None) -> str | None:
    candidates = [_handle_from_url(url)]
    if isinstance(info, dict):
        for key in ("channel_url", "uploader_url"):
            raw = info.get(key)
            if isinstance(raw, str) and raw.strip():
                candidates.append(_handle_from_url(raw))
        uploader_id = info.get("uploader_id")
        if isinstance(uploader_id, str) and uploader_id.strip():
            candidates.append(uploader_id.strip())
    for candidate in candidates:
        if candidate is not None and _is_lossless_handle(candidate):
            return candidate
    return None


def _is_lossless_handle(value: str) -> bool:
    body = value.strip().lstrip("@")
    if not body or " " in body:
        return False
    if body.startswith("UC") and len(body) >= 20:
        return False
    return re.fullmatch(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", body) is not None


def _channel_id_from_info(info: dict[str, Any] | None) -> str | None:
    if not isinstance(info, dict):
        return None
    raw = info.get("channel_id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _channel_id_slug(channel_id: str) -> str:
    cleaned = channel_id.strip().lower()
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", cleaned) is None:
        raise ValueError(f"channel_id cannot become a podcast_id slug without dropping characters: {channel_id}")
    return cleaned


def _handle_slug(handle: str) -> str:
    cleaned = handle.strip().lstrip("@").lower()
    cleaned = re.sub(r"[^a-z0-9-]", "", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    if not cleaned:
        raise ValueError(f"Could not derive a slug from handle: {handle}")
    return cleaned


def _resolve_title(explicit: str | None, info: dict[str, Any], identity: YoutubeVideoIdentity) -> str:
    if explicit and explicit.strip():
        return _normalize_title(explicit)
    raw = str(info.get("title") or "").strip()
    return _normalize_title(raw) or identity.episode_ref


def _normalize_title(value: str) -> str:
    return _WHITESPACE_PATTERN.sub(" ", str(value)).strip()


def _published_at(upload_date: Any) -> str | None:
    match = _UPLOAD_DATE_PATTERN.match(str(upload_date or "").strip())
    if match is None:
        return None
    return "-".join(match.groups())


def _duration_label(duration: Any) -> str | None:
    try:
        total_seconds = round(float(duration))
    except (TypeError, ValueError):
        return None
    if total_seconds < 0:
        return None
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"
