"""把 X 影片取得成 corpus 音訊資產。

只有「取得」是新的：抓下影片、抽出音軌、寫下 episode seed。之後的轉錄、
逐字稿落地、索引與搜尋全部沿用既有路徑，本模組不重寫任何一段。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any
from urllib.parse import urlparse
import wave

from . import storage
from .config import load_podcast_profile
from .errors import (
    PodcastIngestCoreError,
    XVideoIngestDependencyError,
    XVideoIngestFailedError,
)
from .models import CorpusEpisodeSeed
from .transcriber import transcribe_episode


X_SOURCE_TYPE = "x-video"
_WHITESPACE_PATTERN = re.compile(r"\s+")
_UPLOAD_DATE_PATTERN = re.compile(r"^(\d{4})(\d{2})(\d{2})$")
_TRAILING_ELLIPSIS_PATTERN = re.compile(r"(?:\.{3}|…)\s*$")

_X_HOSTS = {
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "mobile.twitter.com",
}
# X handle：字母、數字、底線，最長 15 字。底線在 podcast_id slug 不合法，
# 因此下面會換成連字號。
_STATUS_PATH_PATTERN = re.compile(
    r"^/(?P<handle>[A-Za-z0-9_]{1,15})/status/(?P<status_id>\d+)"
)


@dataclass(frozen=True)
class XVideoIdentity:
    """一支 X 影片在 corpus 裡的身分。"""

    podcast_id: str
    episode_ref: str
    handle: str
    canonical_url: str


def derive_identity(url: str) -> XVideoIdentity:
    """從 X 貼文網址推導 podcast_id 與 episode_ref。

    episode_ref 直接用 tweet status id：它就是這則貼文的正規識別碼，
    而且不必轉換就符合 ``storage`` 的 episode_ref 規則。
    """

    parsed = urlparse(url.strip())
    match = (
        _STATUS_PATH_PATTERN.match(parsed.path)
        if parsed.netloc.lower() in _X_HOSTS
        else None
    )
    if match is None:
        raise ValueError(f"不是 X 貼文網址：{url}")

    handle = match.group("handle")
    status_id = match.group("status_id")
    return XVideoIdentity(
        podcast_id=f"x-{handle.replace('_', '-').lower()}",
        episode_ref=status_id,
        handle=handle,
        canonical_url=f"https://x.com/{handle}/status/{status_id}",
    )


def build_seed(
    identity: XVideoIdentity,
    info: dict[str, Any],
    title: str | None = None,
) -> CorpusEpisodeSeed:
    """由解析到的來源 metadata 組出 corpus episode seed。

    缺漏的欄位一律留空並記進 warnings，不猜、不補。
    """

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
        # status id 就是這則貼文的 guid，而影片網址本身即可取得音訊。
        guid_status="present",
        has_audio_url=True,
        seed_source=X_SOURCE_TYPE,
        selector=identity.canonical_url,
        warning_count=len(warnings),
        warnings=warnings,
        not_investment_advice=True,
    )


@dataclass(frozen=True)
class XVideoIngestResult:
    """一次取得流程的結果；dry-run 時所有落地路徑都是 None。"""

    podcast_id: str
    episode_ref: str
    title: str
    canonical_url: str
    confirmed: bool
    planned_writes: list[str]
    audio_path: str | None
    seed_path: str | None
    transcript_json_path: str | None
    warnings: list[str]


# 措辭刻意用空格的「rebuild cache」而非那個函式名：core 模組只要出現該函式名的
# 字面，快取守衛測試就會判定為未經審查的自動重建風險（憲章原則 VIII）。其他
# runner 也是這樣表達同一件事。註解本身同樣不能出現該字面。
CACHE_STALE_WARNING = (
    "SQLite cache may be stale; rebuild cache manually. "
    "本流程不會自動重建，這一集要等你手動重建 cache 之後才搜尋得到。"
)


def run_x_video_ingest(
    url: str,
    *,
    confirm: bool = False,
    title: str | None = None,
    model: str | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
    force: bool = False,
    work_dir: str | Path | None = None,
) -> XVideoIngestResult:
    """把一支 X 影片取得成 corpus 資產；預設是 dry-run。

    dry-run 只解析 metadata，不下載影片也不轉錄，因此可以先看清楚要寫哪些檔案。
    """

    identity = derive_identity(url)
    try:
        info = _resolve_metadata(identity.canonical_url)
    except PodcastIngestCoreError:
        raise
    except Exception as exc:
        # 這是整條流程最先、也最常失敗的一步：貼文沒有影片、已刪除、轉私密，
        # 或 yt-dlp 的 X extractor 壞掉。它同時位在 dry-run 路徑上，所以第三方
        # 例外若不在這裡收斂，使用者第一次執行看到的就會是 traceback。
        raise XVideoIngestFailedError(f"解析來源 metadata 失敗：{exc}") from exc

    seed = build_seed(identity, info, title)

    audio_target = storage.audio_asset_path(
        identity.podcast_id, identity.episode_ref, seed.title, ".wav"
    )
    seed_target = storage.corpus_episode_seed_asset_path(
        identity.podcast_id, identity.episode_ref
    )
    transcript_targets = storage.transcript_asset_paths(
        identity.podcast_id, identity.episode_ref, seed.title
    )
    warnings = [*seed.warnings, CACHE_STALE_WARNING]
    registration_problem = _registration_problem(identity.podcast_id)
    if registration_problem is not None:
        warnings.append(registration_problem)

    # 抽好的音訊就是耐久產物。轉錄失敗後重跑不應該再下載一次整支影片；
    # 要重新取得就自行刪掉這個檔案。這個判斷必須在 dry-run 回傳之前做，
    # 否則計畫會預告一個實際不會發生的寫入。
    audio_exists = audio_target.exists()
    if audio_exists:
        warnings.append(f"沿用既有音訊，未重新下載：{audio_target}")

    planned_writes = [str(seed_target)]
    if not audio_exists:
        planned_writes.append(str(audio_target))
    planned_writes.extend(
        [
            str(transcript_targets.text_path),
            str(transcript_targets.srt_path),
            str(transcript_targets.json_path),
        ]
    )

    if not confirm:
        return XVideoIngestResult(
            podcast_id=identity.podcast_id,
            episode_ref=identity.episode_ref,
            title=seed.title,
            canonical_url=identity.canonical_url,
            confirmed=False,
            planned_writes=planned_writes,
            audio_path=None,
            seed_path=None,
            transcript_json_path=None,
            warnings=warnings,
        )

    # 先攔在這裡，不要下載幾百 MB 之後才發現沒登記。
    if registration_problem is not None:
        raise XVideoIngestFailedError(registration_problem)

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

    return XVideoIngestResult(
        podcast_id=identity.podcast_id,
        episode_ref=identity.episode_ref,
        title=seed.title,
        canonical_url=identity.canonical_url,
        confirmed=True,
        planned_writes=planned_writes,
        audio_path=str(audio_target),
        seed_path=str(seed_target),
        transcript_json_path=str(transcript.json_path),
        warnings=warnings,
    )


def _write_seed(seed_target: Path, seed: CorpusEpisodeSeed) -> None:
    """照 corpus_episode_intake 的慣例走 ``.part`` → replace。

    直接 ``write_text`` 若寫到一半失敗，會在正規路徑留下半截 JSON；corpus_index
    只會把它標成 unreadable，但那是可以避免的髒資料。
    """

    seed_target.parent.mkdir(parents=True, exist_ok=True)
    part_path = seed_target.with_name(f"{seed_target.name}.part")
    try:
        part_path.unlink(missing_ok=True)
        part_path.write_text(
            json.dumps(asdict(seed), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        part_path.replace(seed_target)
    except OSError:
        part_path.unlink(missing_ok=True)
        raise


def _acquire_audio(url: str, audio_target: Path, work_dir: str | Path | None) -> None:
    """下載影片並抽出音軌；影片本身絕不落在 data/ 底下。"""

    owns_work_dir = work_dir is None
    resolved_work_dir = (
        Path(tempfile.mkdtemp(prefix="x-video-")) if owns_work_dir else Path(work_dir)
    )
    part_path = audio_target.with_suffix(audio_target.suffix + ".part")
    try:
        video_path = _download_video(url, resolved_work_dir)
        audio_target.parent.mkdir(parents=True, exist_ok=True)
        part_path.unlink(missing_ok=True)
        _extract_audio(video_path, part_path)
        part_path.replace(audio_target)
    except PodcastIngestCoreError:
        # 已經是本專案的錯誤型別，維持原訊息，不要再包一層。
        raise
    except Exception as exc:
        # yt-dlp 的 DownloadError 與 PyAV 的 FFmpegError 都直接繼承 Exception，
        # 不是 OSError；X 的 extractor 又特別常壞。只接 OSError 會讓第三方例外
        # 直接拋穿到 CLI，而 CLI 只處理本專案的錯誤型別。
        raise XVideoIngestFailedError(f"取得音訊失敗：{exc}") from exc
    finally:
        # 成功時 replace 已經把 .part 移走，這裡是 no-op；失敗時無論哪種例外
        # 都不會有殘留檔案留在 data/audio/。
        try:
            part_path.unlink(missing_ok=True)
        except OSError:
            pass
        if owns_work_dir:
            shutil.rmtree(resolved_work_dir, ignore_errors=True)


def _registration_problem(podcast_id: str) -> str | None:
    """確認這個 podcast_id 確實被登記成 X 影片來源。

    RSS 入口會強制檢查 ``source_type``（見 ``config.require_rss_profile``），這裡
    是對稱的另一半。少了它，一個 id 恰好等於 ``x-{handle}`` 的 RSS profile 會被
    默默寫入 X 產物，而打錯字的 source_type 也會在這條路徑上被放行。
    """

    try:
        profile = load_podcast_profile(podcast_id)
    except KeyError:
        return (
            f"config/podcasts.yaml 還沒有 {podcast_id}。請先加入一段："
            f"{podcast_id}: display_name / source_type: {X_SOURCE_TYPE} / language。"
        )
    if profile.source_type != X_SOURCE_TYPE:
        return (
            f"{podcast_id} 的 source_type 是 {profile.source_type}，不是 "
            f"{X_SOURCE_TYPE}；這條擷取流程只處理 X 影片來源。"
        )
    return None


def _load_yt_dlp():
    try:
        import yt_dlp
    except ImportError as exc:  # pragma: no cover - 依賴缺失才會走到
        raise XVideoIngestDependencyError(
            "需要 yt-dlp 才能取得 X 影片，請先安裝：pip install yt-dlp"
        ) from exc
    return yt_dlp


def _load_av():
    try:
        import av
    except ImportError as exc:  # pragma: no cover - 依賴缺失才會走到
        raise XVideoIngestDependencyError(
            "需要 PyAV 才能抽出音軌，請先安裝：pip install av"
        ) from exc
    return av


def _resolve_metadata(url: str) -> dict[str, Any]:
    """只取 metadata，不下載影片。這是 dry-run 得以成立的原因。"""

    yt_dlp = _load_yt_dlp()
    options = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(options) as client:
        info = client.extract_info(url, download=False)
    if not isinstance(info, dict):
        raise XVideoIngestFailedError(f"無法解析來源 metadata：{url}")
    return info


def _download_video(url: str, target_dir: Path) -> Path:
    """以 guest token 下載；不帶任何登入憑證。"""

    yt_dlp = _load_yt_dlp()
    target_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": str(target_dir / "%(id)s.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(options) as client:
        info = client.extract_info(url, download=True)
        if not isinstance(info, dict):
            raise XVideoIngestFailedError(f"下載失敗：{url}")
        return _downloaded_path(client, info)


def _downloaded_path(client, info: dict[str, Any]) -> Path:
    """回傳 yt-dlp 實際寫出的檔案路徑。

    有 ffmpeg 時 yt-dlp 預設會合併 bestvideo+bestaudio，合併後容器的副檔名
    可能與 ``prepare_filename`` 推測的不同；那會回一個不存在的路徑，接著在
    抽音軌時才爆掉。``requested_downloads`` 記的是真正寫出的檔案，優先採用。
    """

    downloads = info.get("requested_downloads")
    if isinstance(downloads, list) and downloads and isinstance(downloads[0], dict):
        filepath = downloads[0].get("filepath")
        if filepath:
            return Path(filepath)
    return Path(client.prepare_filename(info))


def _extract_audio(video_path: Path, audio_path: Path) -> None:
    """抽出 16 kHz 單聲道 PCM WAV，也就是 faster-whisper 要的格式。"""

    av = _load_av()
    container = av.open(str(video_path))
    try:
        audio_stream = next(
            (stream for stream in container.streams if stream.type == "audio"), None
        )
        if audio_stream is None:
            raise XVideoIngestFailedError(f"影片沒有音軌：{video_path}")

        resampler = av.audio.resampler.AudioResampler(
            format="s16", layout="mono", rate=16000
        )
        with wave.open(str(audio_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            for packet in container.demux(audio_stream):
                for frame in packet.decode():
                    _write_resampled(wav, resampler.resample(frame))
            _write_resampled(wav, resampler.resample(None))
    finally:
        container.close()


def _write_resampled(wav, resampled) -> None:
    if not resampled:
        return
    if not isinstance(resampled, list):
        resampled = [resampled]
    for frame in resampled:
        samples = frame.to_ndarray().astype("int16", copy=False)
        wav.writeframes(samples.reshape(-1).tobytes())


def _resolve_title(
    explicit: str | None, info: dict[str, Any], identity: XVideoIdentity
) -> str:
    """決定要用哪個標題。

    yt-dlp 對 X 貼文回的 ``title`` 其實是 ``{uploader} - {截斷的推文}...``。
    帳號已經編在 podcast_id 裡，末尾的刪節號則是 yt-dlp 自己截斷的記號，
    兩者放進檔名都只是雜訊。去掉之後剩下的仍是推文內文而非真正的標題，
    所以呼叫端可以用 ``title`` 直接覆寫。
    """

    if explicit and explicit.strip():
        return _normalize_title(explicit)

    raw = str(info.get("title") or "").strip()
    uploader = str(info.get("uploader") or "").strip()
    prefix = f"{uploader} - "
    if uploader and raw.startswith(prefix):
        raw = raw[len(prefix) :]
    raw = _TRAILING_ELLIPSIS_PATTERN.sub("", raw)
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
