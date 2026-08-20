from __future__ import annotations

import inspect

from podcast_ingest_core.x_video_ingest import XVideoIngestResult


_SAMPLE_URL = "https://x.com/Raytar/status/2071290493581840707"


def _preview_result() -> XVideoIngestResult:
    return XVideoIngestResult(
        podcast_id="x-raytar",
        episode_ref="2071290493581840707",
        title="Code with Claude Prompt Engineering Breakout",
        canonical_url=_SAMPLE_URL,
        confirmed=False,
        run_mode="preview",
        planned_writes=["data/corpus/x-raytar/episode-seeds/2071290493581840707.episode-seed.json"],
        audio_path=None,
        seed_path=None,
        transcript_json_path=None,
        report_json_path=None,
        report_markdown_path=None,
        warnings=["SQLite cache may be stale; rebuild cache manually."],
        not_investment_advice=True,
    )


def test_preview_returns_network_read_plan_and_does_not_confirm(monkeypatch):
    from podcast_ingest_core import mcp_server

    captured = {}

    def fake_ingest(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return _preview_result()

    monkeypatch.setattr(mcp_server.x_video_ingest, "run_x_video_ingest", fake_ingest)

    response = mcp_server.ingest_x_video(url=_SAMPLE_URL, confirm=False)

    assert response["ok"] is True
    assert response["dry_run"] is True
    assert response["tool"] == "ingest_x_video"
    assert response["run_mode"] == "preview"
    assert response["network_read"] is True
    assert response["network_read_scope"] == "public_metadata_only"
    assert response["not_investment_advice"] is True
    assert captured["kwargs"]["confirm"] is False
    assert any("zero-network" in risk for risk in response["risks"])
    assert any("episode-seeds" in write for write in response["writes"])


def test_confirm_delegates_to_core_once(monkeypatch):
    from podcast_ingest_core import mcp_server

    captured = {}

    def fake_ingest(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return XVideoIngestResult(
            podcast_id="x-raytar",
            episode_ref="2071290493581840707",
            title="Override",
            canonical_url=_SAMPLE_URL,
            confirmed=True,
            run_mode="confirmed",
            planned_writes=[],
            audio_path="data/audio/x-raytar/2071290493581840707__override.wav",
            seed_path="data/corpus/x-raytar/episode-seeds/2071290493581840707.episode-seed.json",
            transcript_json_path=None,
            report_json_path="data/corpus/x-raytar/x-video-ingest-runs/2071290493581840707.x-video-ingest.json",
            report_markdown_path="data/corpus/x-raytar/x-video-ingest-runs/2071290493581840707.x-video-ingest.md",
            warnings=["SQLite cache may be stale; rebuild cache manually."],
            not_investment_advice=True,
        )

    monkeypatch.setattr(mcp_server.x_video_ingest, "run_x_video_ingest", fake_ingest)

    response = mcp_server.ingest_x_video(url=_SAMPLE_URL, confirm=True, title="Override", force=True)

    assert response["ok"] is True
    data = response["data"]
    assert data["run_mode"] == "confirmed"
    assert data["not_investment_advice"] is True
    assert data["report_json_path"]
    assert data["report_markdown_path"]
    assert captured["url"] == _SAMPLE_URL
    assert captured["kwargs"]["confirm"] is True
    assert captured["kwargs"]["title"] == "Override"
    assert captured["kwargs"]["force"] is True
    assert "work_dir" not in captured["kwargs"]
    assert "device" not in captured["kwargs"]
    assert any("rebuild cache" in warning.lower() for warning in response["warnings"])


def test_invalid_url_preview_returns_error_envelope():
    from podcast_ingest_core import mcp_server

    response = mcp_server.ingest_x_video(url="https://example.com/not-x", confirm=False)

    assert response["ok"] is False
    assert response["error_type"] in {"ValueError", "XVideoIngestFailedError"}
    assert "traceback" not in str(response).lower()


def test_mcp_signature_hides_work_dir_and_device():
    from podcast_ingest_core import mcp_server

    parameters = inspect.signature(mcp_server.ingest_x_video).parameters
    assert list(parameters) == ["url", "confirm", "title", "force"]
