"""共用的公開影片取得：metadata、guest 下載、抽出 16 kHz 單聲道 WAV。

X 與 YouTube 各自擁有身分與 seed；這裡不認識 source_type。
"""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
from typing import Any
import wave

from .errors import (
    PodcastIngestCoreError,
    VideoAcquireDependencyError,
    VideoAcquireFailedError,
)

METADATA_OPTIONS: dict[str, Any] = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "ignoreconfig": True,
}

DOWNLOAD_OPTION_KEYS: tuple[str, ...] = (
    "quiet",
    "no_warnings",
    "outtmpl",
    "ignoreconfig",
)
_FORBIDDEN_CREDENTIAL_KEYS = frozenset(
    {"cookiefile", "cookiesfrombrowser", "username", "password", "videopassword"}
)


def guest_download_options(target_dir: Path) -> dict[str, Any]:
    return {
        "quiet": True,
        "no_warnings": True,
        "ignoreconfig": True,
        "outtmpl": str(target_dir / "%(id)s.%(ext)s"),
    }


def resolve_metadata(
    url: str,
    *,
    failed_error: type[PodcastIngestCoreError] = VideoAcquireFailedError,
    dependency_error: type[PodcastIngestCoreError] = VideoAcquireDependencyError,
) -> dict[str, Any]:
    """只取 metadata，不下載影片。"""

    _assert_guest_options(METADATA_OPTIONS)
    yt_dlp = _load_yt_dlp(dependency_error)
    with yt_dlp.YoutubeDL(METADATA_OPTIONS) as client:
        info = client.extract_info(url, download=False)
    if not isinstance(info, dict):
        raise failed_error(f"無法解析來源 metadata：{url}")
    return info


def download_video(
    url: str,
    target_dir: Path,
    *,
    failed_error: type[PodcastIngestCoreError] = VideoAcquireFailedError,
    dependency_error: type[PodcastIngestCoreError] = VideoAcquireDependencyError,
    load_yt_dlp: Any = None,
) -> Path:
    """以 guest token 下載；不帶任何登入憑證。"""

    yt_dlp = load_yt_dlp() if load_yt_dlp is not None else _load_yt_dlp(dependency_error)
    target_dir.mkdir(parents=True, exist_ok=True)
    options = guest_download_options(target_dir)
    _assert_guest_options(options)
    with yt_dlp.YoutubeDL(options) as client:
        info = client.extract_info(url, download=True)
        if not isinstance(info, dict):
            raise failed_error(f"下載失敗：{url}")
        return downloaded_path(client, info)


def downloaded_path(client: Any, info: dict[str, Any]) -> Path:
    downloads = info.get("requested_downloads")
    if isinstance(downloads, list) and downloads and isinstance(downloads[0], dict):
        filepath = downloads[0].get("filepath")
        if filepath:
            return Path(filepath)
    return Path(client.prepare_filename(info))


def extract_audio(
    video_path: Path,
    audio_path: Path,
    *,
    failed_error: type[PodcastIngestCoreError] = VideoAcquireFailedError,
    dependency_error: type[PodcastIngestCoreError] = VideoAcquireDependencyError,
) -> None:
    av = _load_av(dependency_error)
    container = av.open(str(video_path))
    try:
        audio_stream = next(
            (stream for stream in container.streams if stream.type == "audio"), None
        )
        if audio_stream is None:
            raise failed_error(f"影片沒有音軌：{video_path}")

        resampler = av.audio.resampler.AudioResampler(
            format="s16", layout="mono", rate=16000
        )
        with wave.open(str(audio_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            for packet in container.demux(audio_stream):
                for frame in packet.decode():
                    write_resampled(wav, resampler.resample(frame))
            write_resampled(wav, resampler.resample(None))
    finally:
        container.close()


def write_resampled(wav: Any, resampled: Any) -> None:
    if not resampled:
        return
    if not isinstance(resampled, list):
        resampled = [resampled]
    for frame in resampled:
        samples = frame.to_ndarray().astype("int16", copy=False)
        wav.writeframes(samples.reshape(-1).tobytes())


def acquire_wav(
    url: str,
    audio_target: Path,
    work_dir: str | Path | None,
    *,
    failed_error: type[PodcastIngestCoreError] = VideoAcquireFailedError,
    dependency_error: type[PodcastIngestCoreError] = VideoAcquireDependencyError,
    work_prefix: str = "video-",
) -> None:
    owns_work_dir = work_dir is None
    resolved_work_dir = (
        Path(tempfile.mkdtemp(prefix=work_prefix)) if owns_work_dir else Path(work_dir)
    )
    part_path = audio_target.with_suffix(audio_target.suffix + ".part")
    try:
        video_path = download_video(
            url,
            resolved_work_dir,
            failed_error=failed_error,
            dependency_error=dependency_error,
        )
        audio_target.parent.mkdir(parents=True, exist_ok=True)
        part_path.unlink(missing_ok=True)
        extract_audio(
            video_path,
            part_path,
            failed_error=failed_error,
            dependency_error=dependency_error,
        )
        part_path.replace(audio_target)
    except PodcastIngestCoreError:
        raise
    except Exception as exc:
        raise failed_error(f"取得音訊失敗：{exc}") from exc
    finally:
        try:
            part_path.unlink(missing_ok=True)
        except OSError:
            pass
        if owns_work_dir:
            shutil.rmtree(resolved_work_dir, ignore_errors=True)


def _assert_guest_options(options: dict[str, Any]) -> None:
    forbidden = _FORBIDDEN_CREDENTIAL_KEYS.intersection(options)
    if forbidden:
        raise VideoAcquireFailedError(
            f"取得選項不得含憑證鍵：{', '.join(sorted(forbidden))}"
        )
    if options.get("ignoreconfig") is not True:
        raise VideoAcquireFailedError("取得選項必須 ignoreconfig，以免讀到使用者 yt-dlp 設定")


def _load_yt_dlp(dependency_error: type[PodcastIngestCoreError]):
    try:
        import yt_dlp
    except ImportError as exc:  # pragma: no cover
        raise dependency_error(
            "需要 yt-dlp 才能取得影片，請先安裝：pip install yt-dlp"
        ) from exc
    return yt_dlp


def _load_av(dependency_error: type[PodcastIngestCoreError]):
    try:
        import av
    except ImportError as exc:  # pragma: no cover
        raise dependency_error(
            "需要 PyAV 才能抽出音軌，請先安裝：pip install av"
        ) from exc
    return av
