from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from podcast_ingest_core.errors import YoutubeVideoIngestFailedError
from podcast_ingest_core.models import PodcastProfile
from podcast_ingest_core.youtube_video_ingest import (
    build_seed,
    derive_youtube_identity,
    parse_youtube_video_id,
)

_VIDEO_ID = "dQw4w9WgXcQ"
_UNDERSCORE_ID = "abc_def-hij"
_SAMPLE_INFO = {
    "title": "Uploader - Keep This Prefix",
    "upload_date": "20260630",
    "duration": 125.4,
    "uploader_id": "@raytar",
    "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
}
_WATCH_URL = f"https://www.youtube.com/watch?v={_VIDEO_ID}"


def test_parse_youtube_video_id_accepts_common_url_forms() -> None:
    urls = (
        f"https://www.youtube.com/watch?v={_VIDEO_ID}",
        f"https://youtu.be/{_VIDEO_ID}",
        f"https://www.youtube.com/shorts/{_VIDEO_ID}",
        f"https://www.youtube.com/embed/{_VIDEO_ID}",
        f"https://www.youtube.com/live/{_VIDEO_ID}",
        f"https://m.youtube.com/watch?v={_VIDEO_ID}",
        f"https://music.youtube.com/watch?v={_VIDEO_ID}&list=PLxxx",
    )
    for url in urls:
        assert parse_youtube_video_id(url) == _VIDEO_ID


def test_playlist_without_video_id_is_refused() -> None:
    with pytest.raises(ValueError, match="YouTube"):
        parse_youtube_video_id("https://www.youtube.com/playlist?list=PLxxxx")


def test_video_id_with_underscore_is_kept() -> None:
    identity = derive_youtube_identity(
        f"https://youtu.be/{_UNDERSCORE_ID}",
        {"uploader_id": "@raytar"},
    )
    assert identity.episode_ref == _UNDERSCORE_ID
    assert identity.canonical_url == f"https://www.youtube.com/watch?v={_UNDERSCORE_ID}"


def test_display_name_is_not_used_as_handle() -> None:
    identity = derive_youtube_identity(
        _WATCH_URL,
        {
            "channel": "The Verge",
            "uploader": "The Verge",
            "channel_id": "UCuVHPbpNM18XW3Jn2XdX1-A",
        },
    )
    assert identity.podcast_id == "yt-ucuvhpbpnm18xw3jn2xdx1-a"
    assert "theverge" not in identity.podcast_id


def test_lossy_handle_falls_back_to_channel_id() -> None:
    identity = derive_youtube_identity(
        _WATCH_URL,
        {"uploader_id": "@Foo.Bar", "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx"},
    )
    assert identity.podcast_id == "yt-ucxxxxxxxxxxxxxxxxxxxxxx"


def test_lossless_handle_becomes_podcast_id() -> None:
    identity = derive_youtube_identity(_WATCH_URL, {"uploader_id": "@3blue1brown"})
    assert identity.podcast_id == "yt-3blue1brown"


def test_hyphenated_handle_is_lossless() -> None:
    identity = derive_youtube_identity(_WATCH_URL, {"uploader_id": "@foo-bar"})
    assert identity.podcast_id == "yt-foo-bar"


def test_channel_id_with_underscore_fails_closed() -> None:
    with pytest.raises(ValueError, match="不折損"):
        derive_youtube_identity(
            _WATCH_URL,
            {"channel": "The Verge", "channel_id": "UCabc_defghijklmnopqrstu"},
        )


def test_handle_from_channel_url() -> None:
    identity = derive_youtube_identity(
        _WATCH_URL,
        {"channel_url": "https://www.youtube.com/@3blue1brown"},
    )
    assert identity.podcast_id == "yt-3blue1brown"


def test_video_id_starting_with_hyphen_or_underscore_is_refused() -> None:
    with pytest.raises(ValueError, match="不能以"):
        parse_youtube_video_id("https://youtu.be/-abcdefghij")
    with pytest.raises(ValueError, match="不能以"):
        parse_youtube_video_id("https://youtu.be/_abcdefghij")


def test_title_does_not_strip_uploader_prefix() -> None:
    identity = derive_youtube_identity(_WATCH_URL, _SAMPLE_INFO)
    seed = build_seed(identity, _SAMPLE_INFO)
    assert seed.title == "Uploader - Keep This Prefix"
    assert seed.seed_source == "yt-video"
    assert seed.selector == f"https://www.youtube.com/watch?v={_VIDEO_ID}"
    assert seed.has_audio_url is True


def _stub_acquisition(monkeypatch, module, *, info=None) -> None:
    def refuse(*_args, **_kwargs):
        raise AssertionError("this test must not download or extract")

    monkeypatch.setattr(module, "_resolve_metadata", lambda _url: dict(info or _SAMPLE_INFO))
    monkeypatch.setattr(module, "_download_video", refuse)
    monkeypatch.setattr(module, "_extract_audio", refuse)


def _yt_profile(podcast_id: str) -> PodcastProfile:
    return PodcastProfile(
        podcast_id=podcast_id,
        display_name=podcast_id,
        rss_url=None,
        language="en",
        default_episode_prefix=None,
        source_type="yt-video",
    )


def test_dry_run_returns_a_plan_and_touches_nothing(monkeypatch, tmp_data_dirs: Path) -> None:
    from podcast_ingest_core import youtube_video_ingest

    _stub_acquisition(monkeypatch, youtube_video_ingest)
    result = youtube_video_ingest.run_youtube_video_ingest(_WATCH_URL)

    assert result.confirmed is False
    assert result.podcast_id == "yt-raytar"
    assert result.episode_ref == _VIDEO_ID
    assert result.audio_path is None
    assert result.seed_path is None
    planned = " ".join(result.planned_writes)
    assert "episode-seeds" in planned
    assert ".wav" in planned
    assert any("rebuild" in warning.lower() for warning in result.warnings)
    assert not (tmp_data_dirs / "corpus").exists()
    assert not (tmp_data_dirs / "audio").exists()


def test_dry_run_reuses_existing_wav(monkeypatch, tmp_data_dirs: Path) -> None:
    from podcast_ingest_core import storage, youtube_video_ingest

    _stub_acquisition(monkeypatch, youtube_video_ingest)
    identity = derive_youtube_identity(_WATCH_URL, _SAMPLE_INFO)
    seed = build_seed(identity, _SAMPLE_INFO)
    audio = storage.audio_asset_path(identity.podcast_id, identity.episode_ref, seed.title, ".wav")
    audio.parent.mkdir(parents=True, exist_ok=True)
    audio.write_bytes(b"RIFFfake")

    result = youtube_video_ingest.run_youtube_video_ingest(_WATCH_URL)

    assert str(audio) not in result.planned_writes
    assert any("沿用既有音訊" in warning for warning in result.warnings)


def test_unregistered_source_is_refused_before_download(monkeypatch, tmp_data_dirs: Path) -> None:
    from podcast_ingest_core import youtube_video_ingest

    _stub_acquisition(monkeypatch, youtube_video_ingest)
    with pytest.raises(YoutubeVideoIngestFailedError, match="podcasts.yaml"):
        youtube_video_ingest.run_youtube_video_ingest(_WATCH_URL, confirm=True)


def test_wrong_source_type_is_refused_before_download(monkeypatch, tmp_data_dirs: Path) -> None:
    from podcast_ingest_core import youtube_video_ingest

    _stub_acquisition(monkeypatch, youtube_video_ingest)
    monkeypatch.setattr(
        youtube_video_ingest,
        "load_podcast_profile",
        lambda podcast_id, path=None: PodcastProfile(
            podcast_id=podcast_id,
            display_name=podcast_id,
            rss_url=None,
            language="en",
            default_episode_prefix=None,
            source_type="x-video",
        ),
    )
    with pytest.raises(YoutubeVideoIngestFailedError, match="x-video"):
        youtube_video_ingest.run_youtube_video_ingest(_WATCH_URL, confirm=True)


def test_confirm_writes_seed_wav_and_reuses_transcriber(monkeypatch, tmp_data_dirs: Path) -> None:
    from podcast_ingest_core import storage, youtube_video_ingest

    sibling = tmp_data_dirs / "corpus" / "gooaye" / "keep.txt"
    sibling.parent.mkdir(parents=True, exist_ok=True)
    sibling.write_text("untouched", encoding="utf-8")

    monkeypatch.setattr(
        youtube_video_ingest, "_resolve_metadata", lambda _url: dict(_SAMPLE_INFO)
    )
    monkeypatch.setattr(
        youtube_video_ingest,
        "_download_video",
        lambda _url, work_dir: Path(work_dir) / "video.mp4",
    )
    monkeypatch.setattr(
        youtube_video_ingest,
        "_extract_audio",
        lambda _video, audio_path: Path(audio_path).write_bytes(b"RIFFfake"),
    )
    monkeypatch.setattr(
        youtube_video_ingest,
        "load_podcast_profile",
        lambda podcast_id, path=None: _yt_profile(podcast_id),
    )

    captured: dict = {}

    def fake_transcribe(podcast_id, episode_ref, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(json_path=tmp_data_dirs / "transcripts" / "fake.json")

    monkeypatch.setattr(youtube_video_ingest, "transcribe_episode", fake_transcribe)

    result = youtube_video_ingest.run_youtube_video_ingest(_WATCH_URL, confirm=True)

    assert result.confirmed is True
    expected_audio = storage.audio_asset_path(
        "yt-raytar", _VIDEO_ID, result.title, ".wav"
    )
    assert expected_audio.exists()
    assert not list((tmp_data_dirs / "audio").rglob("*.mp4"))
    seed_path = storage.corpus_episode_seed_asset_path("yt-raytar", _VIDEO_ID)
    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    assert payload["seed_source"] == "yt-video"
    assert captured["title"] == "Uploader - Keep This Prefix"
    assert captured["audio_path"] == expected_audio
    assert sibling.read_text(encoding="utf-8") == "untouched"
    assert any("rebuild" in warning.lower() for warning in result.warnings)


def test_work_dir_alt_case_under_data_is_refused(monkeypatch, tmp_data_dirs: Path) -> None:
    import os

    from podcast_ingest_core import storage, youtube_video_ingest

    _stub_acquisition(monkeypatch, youtube_video_ingest)
    monkeypatch.setattr(
        youtube_video_ingest,
        "load_podcast_profile",
        lambda podcast_id, path=None: _yt_profile(podcast_id),
    )
    data = Path(os.path.abspath(str(storage.DATA_DIR)))
    swapped = data.with_name(data.name.swapcase())
    if swapped.name == data.name:
        pytest.skip("path name has no case variant")
    forbidden = swapped / "scratch"
    with pytest.raises(YoutubeVideoIngestFailedError, match="data"):
        youtube_video_ingest.run_youtube_video_ingest(
            _WATCH_URL, confirm=True, work_dir=forbidden
        )


def test_work_dir_under_data_is_refused_before_download(monkeypatch, tmp_data_dirs: Path) -> None:
    from podcast_ingest_core import storage, youtube_video_ingest

    _stub_acquisition(monkeypatch, youtube_video_ingest)
    monkeypatch.setattr(
        youtube_video_ingest,
        "load_podcast_profile",
        lambda podcast_id, path=None: _yt_profile(podcast_id),
    )
    forbidden = storage.DATA_DIR / "scratch"
    forbidden.mkdir(parents=True, exist_ok=True)
    with pytest.raises(YoutubeVideoIngestFailedError, match="data"):
        youtube_video_ingest.run_youtube_video_ingest(
            _WATCH_URL, confirm=True, work_dir=forbidden
        )
