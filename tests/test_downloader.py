from pathlib import Path
import json
import sys

import pytest

from podcast_ingest_core.models import Episode


class FakeResponse:
    def __init__(self, status_code=200, headers=None, chunks=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._chunks = chunks or [b"audio", b"-bytes"]
        self.closed = False

    def iter_content(self, chunk_size=1024 * 1024):
        yield from self._chunks

    def close(self):
        self.closed = True


def _episode(audio_url="https://example.com/audio/EP672.mp3", title="EP672 又新高拉"):
    return Episode(
        podcast_id="gooaye",
        episode_ref="EP672",
        title=title,
        audio_url=audio_url,
        link="https://example.com/episode/EP672",
    )


def _use_tmp_audio_dir(monkeypatch, tmp_path):
    from podcast_ingest_core import storage

    audio_dir = tmp_path / "audio"
    monkeypatch.setattr(storage, "AUDIO_DIR", audio_dir)
    return audio_dir


def test_download_audio_uses_episode_audio_url(monkeypatch, tmp_path):
    from podcast_ingest_core import downloader

    _use_tmp_audio_dir(monkeypatch, tmp_path)
    requested_urls = []
    monkeypatch.setattr(downloader, "get_episode", lambda *_args: _episode())
    monkeypatch.setattr(
        downloader.requests,
        "get",
        lambda url, **_kwargs: requested_urls.append(url)
        or FakeResponse(headers={"Content-Type": "audio/mpeg"}),
    )

    asset = downloader.download_audio("gooaye", "EP672")

    assert requested_urls == ["https://example.com/audio/EP672.mp3"]
    assert asset.source_url == "https://example.com/audio/EP672.mp3"


def test_download_audio_raises_when_audio_url_missing(monkeypatch):
    from podcast_ingest_core import downloader
    from podcast_ingest_core.errors import AudioUrlMissingError

    monkeypatch.setattr(downloader, "get_episode", lambda *_args: _episode(audio_url=None))

    with pytest.raises(AudioUrlMissingError, match="EP672"):
        downloader.download_audio("gooaye", "EP672")


def test_download_audio_streams_to_target_and_removes_part(monkeypatch, tmp_path):
    from podcast_ingest_core import downloader

    _use_tmp_audio_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(downloader, "get_episode", lambda *_args: _episode())
    monkeypatch.setattr(
        downloader.requests,
        "get",
        lambda *_args, **_kwargs: FakeResponse(headers={"Content-Type": "audio/mpeg"}),
    )

    asset = downloader.download_audio("gooaye", "EP672")

    assert asset.local_path.exists()
    assert asset.local_path.read_bytes() == b"audio-bytes"
    assert not asset.local_path.with_suffix(asset.local_path.suffix + ".part").exists()
    assert asset.downloaded is True
    assert asset.already_exists is False
    assert asset.size_bytes == len(b"audio-bytes")
    assert asset.content_type == "audio/mpeg"


def test_download_audio_skips_existing_target_without_http(monkeypatch, tmp_path):
    from podcast_ingest_core import downloader
    from podcast_ingest_core.storage import audio_asset_path

    _use_tmp_audio_dir(monkeypatch, tmp_path)
    episode = _episode()
    target = audio_asset_path("gooaye", "EP672", episode.title, ".mp3")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"existing")
    monkeypatch.setattr(downloader, "get_episode", lambda *_args: episode)

    def fail_get(*_args, **_kwargs):
        raise AssertionError("HTTP should not be called for existing URL-extension target")

    monkeypatch.setattr(downloader.requests, "get", fail_get)

    asset = downloader.download_audio("gooaye", "EP672")

    assert asset.local_path == target
    assert asset.already_exists is True
    assert asset.downloaded is False
    assert asset.size_bytes == len(b"existing")


def test_download_audio_raises_for_non_2xx(monkeypatch, tmp_path):
    from podcast_ingest_core import downloader
    from podcast_ingest_core.errors import DownloadFailedError

    _use_tmp_audio_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(downloader, "get_episode", lambda *_args: _episode())
    monkeypatch.setattr(
        downloader.requests,
        "get",
        lambda *_args, **_kwargs: FakeResponse(status_code=404),
    )

    with pytest.raises(DownloadFailedError, match="404"):
        downloader.download_audio("gooaye", "EP672")

    assert list((tmp_path / "audio").rglob("*")) == []


def test_audio_filename_removes_windows_illegal_characters(monkeypatch, tmp_path):
    from podcast_ingest_core import downloader

    _use_tmp_audio_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(
        downloader,
        "get_episode",
        lambda *_args: _episode(title=' bad <title> : / \\\\ | ? * name '),
    )
    monkeypatch.setattr(
        downloader.requests,
        "get",
        lambda *_args, **_kwargs: FakeResponse(headers={"Content-Type": "audio/mpeg"}),
    )

    asset = downloader.download_audio("gooaye", "EP672")

    assert not any(character in asset.local_path.name for character in '<>:"/\\|?*')
    assert asset.local_path.name == "EP672__bad_title_name.mp3"


def test_url_extension_mp3_wins(monkeypatch, tmp_path):
    from podcast_ingest_core import downloader

    _use_tmp_audio_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(downloader, "get_episode", lambda *_args: _episode())
    monkeypatch.setattr(
        downloader.requests,
        "get",
        lambda *_args, **_kwargs: FakeResponse(headers={"Content-Type": "audio/mp4"}),
    )

    asset = downloader.download_audio("gooaye", "EP672")

    assert asset.local_path.suffix == ".mp3"


def test_content_type_mp4_sets_m4a_when_url_has_no_extension(monkeypatch, tmp_path):
    from podcast_ingest_core import downloader

    _use_tmp_audio_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(
        downloader,
        "get_episode",
        lambda *_args: _episode(audio_url="https://example.com/download?id=EP672"),
    )
    monkeypatch.setattr(
        downloader.requests,
        "get",
        lambda *_args, **_kwargs: FakeResponse(headers={"Content-Type": "audio/mp4"}),
    )

    asset = downloader.download_audio("gooaye", "EP672")

    assert asset.local_path.suffix == ".m4a"


def test_download_cli_parses_podcast_and_episode(monkeypatch, capsys, tmp_path):
    from podcast_ingest_core.models import AudioAsset
    from scripts import download_episode

    asset = AudioAsset(
        podcast_id="gooaye",
        episode_ref="EP672",
        title="EP672 又新高拉",
        source_url="https://example.com/audio/EP672.mp3",
        local_path=tmp_path / "EP672.mp3",
        content_type="audio/mpeg",
        size_bytes=123,
        downloaded=True,
        already_exists=False,
    )
    monkeypatch.setattr(download_episode, "download_audio", lambda *_args: asset)
    monkeypatch.setattr(
        sys,
        "argv",
        ["download_episode.py", "--podcast", "gooaye", "--episode", "latest"],
    )

    download_episode.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["podcast_id"] == "gooaye"
    assert payload["episode_ref"] == "EP672"
    assert payload["downloaded"] is True


def test_download_audio_refuses_a_non_rss_source_with_a_source_aware_error():
    """Spec 036: HTTP enclosure download has no meaning for an X video.

    Acquisition for those sources goes through the yt-dlp path instead, and the
    error must point there rather than failing inside the RSS lookup.
    """

    from podcast_ingest_core import downloader
    from podcast_ingest_core.errors import UnsupportedSourceTypeError

    with pytest.raises(UnsupportedSourceTypeError, match="x-video"):
        downloader.download_audio("x-raytar", "2071290493581840707")


def test_download_audio_refuses_youtube_and_names_the_ingest_path(monkeypatch):
    from podcast_ingest_core import config, downloader
    from podcast_ingest_core.errors import UnsupportedSourceTypeError
    from podcast_ingest_core.models import PodcastProfile

    monkeypatch.setattr(
        config,
        "load_podcast_profile",
        lambda podcast_id, path=None: PodcastProfile(
            podcast_id=podcast_id,
            display_name="yt",
            rss_url=None,
            language="en",
            default_episode_prefix=None,
            source_type="yt-video",
        ),
    )
    with pytest.raises(UnsupportedSourceTypeError, match="run_youtube_video_ingest"):
        downloader.download_audio("yt-foo-bar", "dQw4w9WgXcQ")
