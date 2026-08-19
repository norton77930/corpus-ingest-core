from __future__ import annotations

from podcast_ingest_core.corpus_audio_download_runner import (
    CorpusAudioDownloadRunFilter,
    _audio_outcome,
    _row_for_episode_audio,
)
from podcast_ingest_core.corpus_local_transcription_runner import (
    CorpusLocalTranscriptionRunFilter,
    _planned_transcript_writes,
    _row_for_episode_transcript,
)
from podcast_ingest_core.corpus_remediation_plan import _build_action
from podcast_ingest_core.storage import transcript_asset_paths


def _seed_meta(seed_source: str, selector: str, *, has_audio_url: bool = True) -> dict:
    return {
        "episode_seed": {
            "status": "available",
            "has_audio_url": has_audio_url,
            "seed_source": seed_source,
            "selector": selector,
            "title": "Real Title",
        }
    }


def test_x_video_missing_audio_is_blocked_for_rss_download() -> None:
    action = _build_action(
        "x-raytar",
        "123",
        "audio",
        {"audio": {"status": "missing"}},
        _seed_meta("x-video", "https://x.com/a/status/123"),
    )
    assert action.status == "blocked"
    assert "source_ingest" in action.blocking_artifacts
    assert "run_x_video_ingest.py" in action.suggested_command
    assert "https://x.com/a/status/123" in action.suggested_command
    assert "download_episode.py" not in action.suggested_command


def test_yt_video_missing_audio_is_blocked_for_rss_download() -> None:
    action = _build_action(
        "yt-foo-bar",
        "dQw4w9WgXcQ",
        "audio",
        {"audio": {"status": "missing"}},
        _seed_meta("yt-video", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    )
    assert action.status == "blocked"
    assert "source_ingest" in action.blocking_artifacts
    assert "run_youtube_video_ingest.py" in action.suggested_command
    assert "dQw4w9WgXcQ" in action.suggested_command


def test_rss_missing_enclosure_still_uses_feed_audio_blocker() -> None:
    action = _build_action(
        "gooaye",
        "EP677",
        "audio",
        {"audio": {"status": "missing"}},
        _seed_meta("rss", "latest", has_audio_url=False),
    )
    assert action.status == "blocked"
    assert action.blocking_artifacts == ["feed_audio_url"]
    assert "download_episode.py" in action.suggested_command


def test_rss_missing_audio_with_enclosure_stays_ready() -> None:
    action = _build_action(
        "gooaye",
        "EP677",
        "audio",
        {"audio": {"status": "missing"}},
        _seed_meta("rss", "latest", has_audio_url=True),
    )
    assert action.status == "ready"
    assert action.suggested_command.startswith("python scripts/download_episode.py")


def test_audio_runner_refuses_video_seed_even_if_plan_says_ready() -> None:
    episode = {
        "episode_ref": "123",
        "source_metadata": _seed_meta("x-video", "https://x.com/a/status/123"),
        "artifact_status": {"audio": {"status": "missing"}},
        "actions": [
            {
                "action_id": "123:audio",
                "artifact_family": "audio",
                "status": "ready",
            }
        ],
    }
    status, reason = _audio_outcome(
        action_payload=episode["actions"][0],
        filters=CorpusAudioDownloadRunFilter(episode_ref="123"),
        confirmed=True,
        episode_ref="123",
        audio_status="missing",
        episode_payload=episode,
    )
    assert status == "rejected"
    assert "run_x_video_ingest.py" in reason
    row = _row_for_episode_audio(
        podcast_id="x-raytar",
        episode_payload=episode,
        filters=CorpusAudioDownloadRunFilter(episode_ref="123"),
        confirmed=False,
        source_plan_paths=[],
    )
    assert row.outcome_status == "skipped"


def test_audio_runner_reason_names_youtube_ingest_cli() -> None:
    episode = {
        "episode_ref": "dQw4w9WgXcQ",
        "source_metadata": _seed_meta(
            "yt-video", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ),
        "artifact_status": {"audio": {"status": "missing"}},
        "actions": [
            {
                "action_id": "dQw4w9WgXcQ:audio",
                "artifact_family": "audio",
                "status": "ready",
            }
        ],
    }
    _status, reason = _audio_outcome(
        action_payload=episode["actions"][0],
        filters=CorpusAudioDownloadRunFilter(episode_ref="dQw4w9WgXcQ"),
        confirmed=False,
        episode_ref="dQw4w9WgXcQ",
        audio_status="missing",
        episode_payload=episode,
    )
    assert "run_youtube_video_ingest.py" in reason


def test_local_transcription_planned_writes_use_plan_title() -> None:
    episode = {
        "episode_ref": "123",
        "title": "Real Title",
        "artifact_status": {
            "transcript": {"status": "missing"},
            "audio": {"status": "available", "path": "data/audio/x-raytar/123.wav"},
        },
        "actions": [
            {
                "action_id": "123:transcript",
                "artifact_family": "transcript",
                "status": "ready",
            }
        ],
    }
    row = _row_for_episode_transcript(
        podcast_id="x-raytar",
        episode_payload=episode,
        filters=CorpusLocalTranscriptionRunFilter(episode_ref="123"),
        confirmed=False,
        source_plan_reads=[],
    )
    expected = transcript_asset_paths("x-raytar", "123", "Real Title")
    assert row.title == "Real Title"
    assert str(expected.json_path) in row.planned_writes
    assert str(expected.text_path) in row.planned_writes
    assert "123__123." not in " ".join(row.planned_writes)
    writes = _planned_transcript_writes("x-raytar", "123", "Real Title")
    assert writes == row.planned_writes
