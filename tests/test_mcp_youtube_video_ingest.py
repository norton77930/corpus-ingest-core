from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

from podcast_ingest_core.models import PodcastProfile


_VIDEO_ID = "dQw4w9WgXcQ"
_WATCH_URL = f"https://www.youtube.com/watch?v={_VIDEO_ID}"
_SAMPLE_INFO = {
    "title": "Uploader - Keep This Prefix",
    "upload_date": "20260630",
    "duration": 125.4,
    "uploader_id": "@raytar",
    "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx",
}


def _yt_profile(podcast_id: str) -> PodcastProfile:
    return PodcastProfile(
        podcast_id=podcast_id,
        display_name=podcast_id,
        rss_url=None,
        language="en",
        default_episode_prefix=None,
        source_type="yt-video",
    )


def _stub_preview(monkeypatch) -> None:
    from podcast_ingest_core import youtube_video_ingest

    def refuse(*_args, **_kwargs):
        raise AssertionError("preview must not download or extract")

    monkeypatch.setattr(
        youtube_video_ingest, "_resolve_metadata", lambda _url: dict(_SAMPLE_INFO)
    )
    monkeypatch.setattr(youtube_video_ingest, "_download_video", refuse)
    monkeypatch.setattr(youtube_video_ingest, "_extract_audio", refuse)
    monkeypatch.setattr(
        youtube_video_ingest,
        "load_podcast_profile",
        lambda podcast_id, path=None: _yt_profile(podcast_id),
    )


def test_preview_returns_network_read_plan_and_writes_nothing(monkeypatch, tmp_data_dirs: Path):
    from podcast_ingest_core import mcp_server

    _stub_preview(monkeypatch)
    before = {path.relative_to(tmp_data_dirs) for path in tmp_data_dirs.rglob("*") if path.is_file()}

    response = mcp_server.ingest_youtube_video(url=_WATCH_URL, confirm=False)

    after = {path.relative_to(tmp_data_dirs) for path in tmp_data_dirs.rglob("*") if path.is_file()}
    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["tool"] == "ingest_youtube_video"
    assert response["run_mode"] == "preview"
    assert response["network_read"] is True
    assert response["network_read_scope"] == "public_metadata_only"
    assert response["not_investment_advice"] is True
    assert any("zero-network" in risk for risk in response["risks"])
    assert any("episode-seeds" in write for write in response["writes"])
    assert any("youtube-video-ingest-runs" in write for write in response["writes"])
    assert after == before


def test_confirm_writes_storage_paths_and_warns_cache_stale(monkeypatch, tmp_data_dirs: Path):
    from podcast_ingest_core import mcp_server, storage, youtube_video_ingest

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
    monkeypatch.setattr(
        youtube_video_ingest,
        "transcribe_episode",
        lambda *args, **kwargs: SimpleNamespace(
            json_path=tmp_data_dirs / "transcripts" / "fake.json"
        ),
    )

    response = mcp_server.ingest_youtube_video(url=_WATCH_URL, confirm=True)

    assert response["ok"] is True
    data = response["data"]
    assert data["run_mode"] == "confirmed"
    assert data["not_investment_advice"] is True
    assert Path(data["audio_path"]).is_file()
    assert Path(data["seed_path"]).is_file()
    assert Path(data["report_json_path"]).is_file()
    assert Path(data["report_markdown_path"]).is_file()
    assert not list((tmp_data_dirs / "audio").rglob("*.mp4"))
    assert any("rebuild cache" in warning.lower() for warning in response["warnings"])
    expected_audio = storage.audio_asset_path(
        "yt-raytar", _VIDEO_ID, data["title"], ".wav"
    )
    assert Path(data["audio_path"]) == expected_audio


def test_invalid_url_preview_returns_error_envelope():
    from podcast_ingest_core import mcp_server

    response = mcp_server.ingest_youtube_video(
        url="https://example.com/not-youtube", confirm=False
    )

    assert response["ok"] is False
    assert response["error_type"] in {"ValueError", "YoutubeVideoIngestFailedError"}
    assert "traceback" not in str(response).lower()


def test_wrong_source_type_confirm_returns_error_envelope(monkeypatch, tmp_data_dirs: Path):
    from podcast_ingest_core import mcp_server, youtube_video_ingest

    monkeypatch.setattr(
        youtube_video_ingest, "_resolve_metadata", lambda _url: dict(_SAMPLE_INFO)
    )
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

    response = mcp_server.ingest_youtube_video(url=_WATCH_URL, confirm=True)

    assert response["ok"] is False
    assert response["error_type"] == "YoutubeVideoIngestFailedError"


def test_mcp_signature_hides_work_dir_and_device():
    from podcast_ingest_core import mcp_server

    parameters = inspect.signature(mcp_server.ingest_youtube_video).parameters
    assert list(parameters) == ["url", "confirm", "title", "force"]


def test_live_registry_appends_youtube_ingest_as_tool_24():
    import asyncio

    from podcast_ingest_core import mcp_server

    names = [tool.name for tool in asyncio.run(mcp_server.mcp.list_tools())]
    # Slots, not tail positions: this registry is append-only, so asserting
    # "youtube is last" breaks on the next tool rather than on a real change.
    assert names[23] == "ingest_youtube_video"
    assert names[22] == "ingest_x_video"
    assert names[21] == "generate_stock_lens_report"
    assert len(names) >= 24
