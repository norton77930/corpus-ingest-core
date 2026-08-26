from __future__ import annotations

from pathlib import Path

import pytest

from podcast_ingest_core import video_acquire
from podcast_ingest_core.errors import VideoAcquireFailedError


def test_guest_metadata_options_have_no_credentials() -> None:
    forbidden = {"cookiefile", "cookiesfrombrowser", "username", "password", "videopassword"}
    assert forbidden.isdisjoint(video_acquire.METADATA_OPTIONS)
    assert video_acquire.METADATA_OPTIONS.get("ignoreconfig") is True


def test_guest_download_options_have_no_credentials(tmp_path: Path) -> None:
    forbidden = {"cookiefile", "cookiesfrombrowser", "username", "password", "videopassword"}
    options = video_acquire.guest_download_options(tmp_path)
    assert forbidden.isdisjoint(options)
    assert options.get("ignoreconfig") is True
    assert set(options) <= set(video_acquire.DOWNLOAD_OPTION_KEYS)


def test_guest_download_asks_for_audio_and_never_needs_a_muxer(tmp_path: Path) -> None:
    """The pipeline wants a 16 kHz mono WAV, never the video.

    Without an explicit format yt-dlp picks its default, and both sources then
    fetch far more than the pipeline keeps. On YouTube the default is a merged
    pair, so the run also needs ffmpeg: 32.30 MiB of video beside 1.26 MiB of
    audio. On X the default is one progressive stream -- no merge, no ffmpeg,
    but 2.42 GiB against a 30.58 MiB audio-only rendition of the same post.
    Both measured live on 2026-08-22 with ffmpeg off PATH.

    A selector containing + is a merge instruction, so asserting its absence
    is what actually pins the property; naming one exact string would not.
    """

    options = video_acquire.guest_download_options(tmp_path)
    selector = options.get("format")
    assert selector, "an explicit format is what keeps yt-dlp off its merging default"
    assert "+" not in selector, f"selector {selector!r} would require a muxer"
    primary = selector.split("/", 1)[0]
    assert primary == "bestaudio" or primary.startswith("bestaudio[")


def test_assert_guest_options_requires_ignoreconfig() -> None:
    with pytest.raises(VideoAcquireFailedError, match="ignoreconfig"):
        video_acquire._assert_guest_options(
            {"quiet": True, "no_warnings": True, "skip_download": True}
        )
