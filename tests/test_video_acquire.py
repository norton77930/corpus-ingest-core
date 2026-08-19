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


def test_assert_guest_options_requires_ignoreconfig() -> None:
    with pytest.raises(VideoAcquireFailedError, match="ignoreconfig"):
        video_acquire._assert_guest_options(
            {"quiet": True, "no_warnings": True, "skip_download": True}
        )
