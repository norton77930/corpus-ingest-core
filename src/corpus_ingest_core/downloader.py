from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import requests

from .errors import AudioUrlMissingError, DownloadFailedError
from .feed_reader import get_episode
from .models import AudioAsset
from .storage import audio_asset_path

SUPPORTED_URL_EXTENSIONS = {".mp3", ".m4a"}
CONTENT_TYPE_EXTENSIONS = {
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
}
DOWNLOAD_TIMEOUT = (10, 60)
CHUNK_SIZE = 1024 * 1024


def download_audio(podcast_id: str, episode_ref: str) -> AudioAsset:
    """下載指定 episode 的音檔到 deterministic local path。"""

    episode = get_episode(podcast_id, episode_ref)
    if episode.audio_url is None:
        raise AudioUrlMissingError(f"episode {episode.podcast_id}/{episode.episode_ref} has no audio_url.")

    extension = _extension_from_url(episode.audio_url)
    if extension is not None:
        target_path = audio_asset_path(episode.podcast_id, episode.episode_ref, episode.title, extension)
        if target_path.exists():
            return _asset_for_existing_file(episode, target_path)
    else:
        target_path = None

    response = _open_stream(episode.audio_url)
    try:
        content_type = _content_type(response)
        if not _is_success(response.status_code):
            raise DownloadFailedError(f"Download failed: {episode.audio_url} returned HTTP {response.status_code}.")

        if target_path is None:
            extension = _extension_from_content_type(content_type)
            target_path = audio_asset_path(episode.podcast_id, episode.episode_ref, episode.title, extension)
            if target_path.exists():
                return _asset_for_existing_file(episode, target_path, content_type=content_type)

        _write_stream_to_file(response, target_path)
        return AudioAsset(
            podcast_id=episode.podcast_id,
            episode_ref=episode.episode_ref,
            title=episode.title,
            source_url=episode.audio_url,
            local_path=target_path,
            content_type=content_type,
            size_bytes=target_path.stat().st_size,
            downloaded=True,
            already_exists=False,
        )
    finally:
        response.close()


def _open_stream(url: str):
    try:
        return requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT)
    except requests.RequestException as exc:
        raise DownloadFailedError(f"Download failed: {url}: {exc}") from exc


def _write_stream_to_file(response, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    part_path = target_path.with_suffix(target_path.suffix + ".part")
    if part_path.exists():
        part_path.unlink()

    with part_path.open("wb") as output:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                output.write(chunk)

    part_path.replace(target_path)


def _asset_for_existing_file(episode, target_path: Path, content_type: str | None = None) -> AudioAsset:
    return AudioAsset(
        podcast_id=episode.podcast_id,
        episode_ref=episode.episode_ref,
        title=episode.title,
        source_url=episode.audio_url or "",
        local_path=target_path,
        content_type=content_type,
        size_bytes=target_path.stat().st_size,
        downloaded=False,
        already_exists=True,
    )


def _extension_from_url(url: str) -> str | None:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in SUPPORTED_URL_EXTENSIONS:
        return suffix
    return None


def _extension_from_content_type(content_type: str | None) -> str:
    if content_type is None:
        return ".mp3"
    media_type = content_type.split(";", 1)[0].strip().lower()
    return CONTENT_TYPE_EXTENSIONS.get(media_type, ".mp3")


def _content_type(response) -> str | None:
    return response.headers.get("Content-Type") or response.headers.get("content-type")


def _is_success(status_code: int) -> bool:
    return 200 <= status_code < 300
