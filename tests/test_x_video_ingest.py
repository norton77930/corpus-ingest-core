from pathlib import Path
from types import SimpleNamespace

import pytest

from podcast_ingest_core.x_video_ingest import build_seed, derive_identity


def test_derives_podcast_id_and_episode_ref_from_a_status_url():
    identity = derive_identity("https://x.com/Raytar/status/2071290493581840707")

    assert identity.podcast_id == "x-raytar"
    assert identity.episode_ref == "2071290493581840707"
    assert identity.canonical_url == "https://x.com/Raytar/status/2071290493581840707"


def test_accepts_twitter_com_and_ignores_tracking_query_and_media_suffix():
    """The same post reaches people in several URL shapes; all must normalise."""

    for url in (
        "https://twitter.com/Raytar/status/2071290493581840707",
        "https://x.com/Raytar/status/2071290493581840707?s=20&t=abc",
        "https://x.com/Raytar/status/2071290493581840707/photo/1",
    ):
        identity = derive_identity(url)
        assert identity.podcast_id == "x-raytar"
        assert identity.episode_ref == "2071290493581840707"


def test_handle_underscores_become_hyphens_to_satisfy_the_podcast_id_slug():
    """X allows ``_`` in handles; ``storage`` rejects it in a podcast_id."""

    identity = derive_identity("https://x.com/Some_User/status/123")

    assert identity.podcast_id == "x-some-user"


def test_a_url_that_is_not_a_status_link_is_refused():
    with pytest.raises(ValueError, match="X"):
        derive_identity("https://example.com/not-a-post")


def _identity():
    return derive_identity("https://x.com/Raytar/status/2071290493581840707")


def test_seed_is_built_from_resolved_metadata():
    seed = build_seed(
        _identity(),
        {
            "title": "Code with Claude   Prompt\nEngineering Breakout",
            "upload_date": "20260630",
            "duration": 2003.925,
        },
    )

    assert seed.podcast_id == "x-raytar"
    assert seed.episode_ref == "2071290493581840707"
    # Whitespace runs collapse so the derived filename slug stays sane.
    assert seed.title == "Code with Claude Prompt Engineering Breakout"
    assert seed.published_at == "2026-06-30"
    assert seed.duration == "33:24"
    assert seed.seed_source == "x-video"
    assert seed.selector == "https://x.com/Raytar/status/2071290493581840707"
    assert seed.guid_status == "present"
    assert seed.has_audio_url is True
    assert seed.warning_count == 0
    assert seed.warnings == []


def test_the_uploader_prefix_and_yt_dlp_ellipsis_are_stripped_from_the_title():
    """yt-dlp reports an X post's title as ``{uploader} - {truncated text}...``.

    Observed on a real resolve: the uploader is already encoded in ``podcast_id``,
    and the trailing ellipsis is yt-dlp's own truncation marker, so both are noise
    in a filename. What remains is still tweet text, not a real title — hence the
    operator override.
    """

    seed = build_seed(
        _identity(),
        {
            "title": "Raytar - My friend makes $1.2 million a year as an engineer.  I aske...",
            "uploader": "Raytar",
            "upload_date": "20260628",
            "duration": 2003.868,
        },
    )

    assert seed.title == (
        "My friend makes $1.2 million a year as an engineer. I aske"
    )


def test_a_title_that_does_not_carry_the_uploader_prefix_is_left_alone():
    seed = build_seed(
        _identity(),
        {"title": "A properly titled talk", "uploader": "Raytar", "duration": 10},
    )

    assert seed.title == "A properly titled talk"


def test_a_whitespace_only_title_falls_back_instead_of_becoming_empty():
    """``--title "   "`` must not produce an empty seed title.

    Filenames survive because ``title_slug`` has its own fallback, but the seed and
    the result object would carry an empty string.
    """

    seed = build_seed(_identity(), {"title": "metadata title", "duration": 10}, title="   ")

    assert seed.title == "metadata title"


def test_an_explicit_title_overrides_the_metadata_title():
    seed = build_seed(
        _identity(),
        {"title": "auto title", "upload_date": "20260630", "duration": 10},
        title="Operator chosen title",
    )

    assert seed.title == "Operator chosen title"


def test_missing_upload_date_is_recorded_as_a_warning_not_invented():
    """The prototype ran yt-dlp without --write-info-json and had no date.

    An absent date must stay absent and be reported, never guessed.
    """

    seed = build_seed(_identity(), {"title": "No date available", "duration": 10})

    assert seed.published_at is None
    assert seed.warning_count == 1
    assert len(seed.warnings) == 1
    assert "published_at" in seed.warnings[0]


def test_duration_over_an_hour_keeps_the_hour_component():
    seed = build_seed(_identity(), {"title": "Long", "duration": 3661})

    assert seed.duration == "1:01:01"


_SAMPLE_INFO = {
    "title": "Code with Claude Prompt Engineering Breakout",
    "upload_date": "20260630",
    "duration": 2003.925,
}
_SAMPLE_URL = "https://x.com/Raytar/status/2071290493581840707"


def _stub_acquisition(monkeypatch, module, *, info=None):
    """Keep every test off the network and off ffmpeg/PyAV."""

    def refuse_acquisition(*_args, **_kwargs):
        raise AssertionError("this test must not download or extract")

    monkeypatch.setattr(module, "_resolve_metadata", lambda _url: dict(info or _SAMPLE_INFO))
    monkeypatch.setattr(module, "_download_video", refuse_acquisition)
    monkeypatch.setattr(module, "_extract_audio", refuse_acquisition)


def test_dry_run_returns_a_plan_and_touches_nothing(monkeypatch, tmp_data_dirs):
    """FR-014: the plan comes from metadata alone — no video, no transcription."""

    from podcast_ingest_core import x_video_ingest

    _stub_acquisition(monkeypatch, x_video_ingest)

    result = x_video_ingest.run_x_video_ingest(_SAMPLE_URL)

    assert result.confirmed is False
    assert result.podcast_id == "x-raytar"
    assert result.episode_ref == "2071290493581840707"
    assert result.title == "Code with Claude Prompt Engineering Breakout"
    assert result.audio_path is None
    assert result.seed_path is None
    assert result.transcript_json_path is None

    planned = " ".join(result.planned_writes)
    assert "episode-seeds" in planned
    assert ".wav" in planned
    # FR-015: the operator must be told the episode is not searchable yet.
    assert any("rebuild" in warning.lower() for warning in result.warnings)

    assert not (tmp_data_dirs / "corpus").exists()
    assert not (tmp_data_dirs / "audio").exists()
    assert not (tmp_data_dirs / "transcripts").exists()


def test_unregistered_source_is_refused_before_anything_is_downloaded(
    monkeypatch, tmp_data_dirs
):
    """A 260 MB download must not happen only to fail on a missing profile.

    ``_stub_acquisition`` makes any download attempt an assertion failure, so
    this test fails loudly if the check ever moves after acquisition.
    """

    from podcast_ingest_core import x_video_ingest
    from podcast_ingest_core.errors import XVideoIngestFailedError

    _stub_acquisition(monkeypatch, x_video_ingest)

    with pytest.raises(XVideoIngestFailedError, match="podcasts.yaml"):
        x_video_ingest.run_x_video_ingest(
            "https://x.com/Nobody/status/123", confirm=True
        )


def test_a_profile_registered_as_rss_is_refused_by_the_x_surface(
    monkeypatch, tmp_data_dirs
):
    """The X surface must enforce the discriminant it introduced.

    RSS entry points check ``source_type``; without the mirror check here the
    enforcement is one-sided — an RSS profile whose id happens to match a derived
    ``x-{handle}`` would silently receive X artifacts, and a typo'd source_type
    would be refused by RSS surfaces yet accepted by this one.
    """

    from podcast_ingest_core import x_video_ingest
    from podcast_ingest_core.errors import XVideoIngestFailedError
    from podcast_ingest_core.models import PodcastProfile

    _stub_acquisition(monkeypatch, x_video_ingest)
    monkeypatch.setattr(
        x_video_ingest,
        "load_podcast_profile",
        lambda _podcast_id: PodcastProfile(
            podcast_id="x-raytar",
            display_name="Not actually an X source",
            rss_url="https://example.invalid/feed.xml",
            language="en",
            default_episode_prefix="EP",
            source_type="rss",
        ),
    )

    with pytest.raises(XVideoIngestFailedError, match="source_type"):
        x_video_ingest.run_x_video_ingest(_SAMPLE_URL, confirm=True)


def test_unregistered_source_is_only_a_warning_during_a_dry_run(
    monkeypatch, tmp_data_dirs
):
    from podcast_ingest_core import x_video_ingest

    _stub_acquisition(monkeypatch, x_video_ingest)

    result = x_video_ingest.run_x_video_ingest("https://x.com/Nobody/status/123")

    assert result.confirmed is False
    assert any("podcasts.yaml" in warning for warning in result.warnings)


def test_confirmed_run_lands_audio_and_seed_then_transcribes_under_the_title(
    monkeypatch, tmp_data_dirs
):
    """The confirmed path must produce real artifacts at the derived paths."""

    import json
    from types import SimpleNamespace

    from podcast_ingest_core import storage, x_video_ingest

    monkeypatch.setattr(
        x_video_ingest, "_resolve_metadata", lambda _url: dict(_SAMPLE_INFO)
    )
    monkeypatch.setattr(
        x_video_ingest,
        "_download_video",
        lambda _url, work_dir: _fake_video(work_dir),
    )
    monkeypatch.setattr(
        x_video_ingest,
        "_extract_audio",
        lambda _video, audio_path: audio_path.write_bytes(b"RIFFfake"),
    )

    captured = {}

    def fake_transcribe(podcast_id, episode_ref, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(json_path=tmp_data_dirs / "transcripts" / "fake.json")

    monkeypatch.setattr(x_video_ingest, "transcribe_episode", fake_transcribe)

    result = x_video_ingest.run_x_video_ingest(_SAMPLE_URL, confirm=True)

    assert result.confirmed is True

    expected_audio = storage.audio_asset_path(
        "x-raytar", "2071290493581840707", result.title, ".wav"
    )
    assert expected_audio.exists()
    assert "Code_with_Claude_Prompt_Engineering_Breakout" in expected_audio.name
    # FR-003: the source video never becomes a corpus artifact.
    assert not list((tmp_data_dirs / "audio").rglob("*.mp4"))

    seed_path = storage.corpus_episode_seed_asset_path(
        "x-raytar", "2071290493581840707"
    )
    seed_payload = json.loads(seed_path.read_text(encoding="utf-8"))
    assert seed_payload["seed_source"] == "x-video"
    assert seed_payload["published_at"] == "2026-06-30"
    assert seed_payload["selector"] == _SAMPLE_URL

    # Transcription is reused, and it is told the real title.
    assert captured["audio_path"] == expected_audio
    assert captured["title"] == "Code with Claude Prompt Engineering Breakout"


def test_download_uses_the_real_merged_filepath_not_the_predicted_name(
    monkeypatch, tmp_path
):
    """yt-dlp merges bestvideo+bestaudio when ffmpeg is present.

    The merged container's extension can differ from what ``prepare_filename``
    predicts, so trusting it can hand back a path that does not exist and kill the
    run in audio extraction. ``requested_downloads[0]['filepath']`` is the field
    that reports what was actually written.
    """

    from podcast_ingest_core import x_video_ingest

    real_path = tmp_path / "work" / "2071290493581840707.mkv"
    predicted_path = tmp_path / "work" / "2071290493581840707.mp4"

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def extract_info(self, _url, download=False):
            real_path.parent.mkdir(parents=True, exist_ok=True)
            real_path.write_bytes(b"merged video")
            return {"requested_downloads": [{"filepath": str(real_path)}]}

        def prepare_filename(self, _info):
            return str(predicted_path)

    monkeypatch.setattr(
        x_video_ingest,
        "_load_yt_dlp",
        lambda: SimpleNamespace(YoutubeDL=lambda _options: FakeClient()),
    )

    result = x_video_ingest._download_video("https://x.com/a/status/1", tmp_path / "work")

    assert result == real_path
    assert result.exists()


def test_a_metadata_failure_is_wrapped_even_in_a_dry_run(monkeypatch, tmp_data_dirs):
    """Metadata resolution is the first step and the likeliest to fail.

    A post with no video, a deleted post, or a broken extractor all surface here —
    on the dry-run path, which is the first thing anyone runs. Observed for real:
    ``ERROR: [twitter] 1: No video could be found in this tweet``.
    """

    from podcast_ingest_core import x_video_ingest
    from podcast_ingest_core.errors import XVideoIngestFailedError

    def explode(*_args, **_kwargs):
        raise RuntimeError("No video could be found in this tweet")

    monkeypatch.setattr(x_video_ingest, "_resolve_metadata", explode)

    with pytest.raises(XVideoIngestFailedError, match="No video could be found"):
        x_video_ingest.run_x_video_ingest(_SAMPLE_URL)


def test_a_download_failure_is_wrapped_not_leaked_raw(monkeypatch, tmp_data_dirs):
    """yt-dlp raises ``DownloadError``, which derives from ``Exception``, not ``OSError``.

    X extractors break often. The caller must get a core error it can handle, not a
    third-party traceback the CLI's `except PodcastIngestCoreError` will miss.
    """

    from podcast_ingest_core import x_video_ingest
    from podcast_ingest_core.errors import XVideoIngestFailedError

    class FakeDownloadError(Exception):
        pass

    monkeypatch.setattr(
        x_video_ingest, "_resolve_metadata", lambda _url: dict(_SAMPLE_INFO)
    )

    def explode(*_args, **_kwargs):
        raise FakeDownloadError("unable to extract video url")

    monkeypatch.setattr(x_video_ingest, "_download_video", explode)

    with pytest.raises(XVideoIngestFailedError, match="unable to extract video url"):
        x_video_ingest.run_x_video_ingest(_SAMPLE_URL, confirm=True)


def test_an_extraction_failure_leaves_no_part_file_behind(monkeypatch, tmp_data_dirs):
    """PyAV raises ``FFmpegError`` — also not an ``OSError``.

    ``wave.open`` has already created the ``.part`` file by the time extraction can
    fail, so cleanup must not hang off an ``OSError``-only branch.
    """

    from podcast_ingest_core import storage, x_video_ingest
    from podcast_ingest_core.errors import XVideoIngestFailedError

    monkeypatch.setattr(
        x_video_ingest, "_resolve_metadata", lambda _url: dict(_SAMPLE_INFO)
    )
    monkeypatch.setattr(
        x_video_ingest, "_download_video", lambda _url, work_dir: _fake_video(work_dir)
    )

    def explode_after_creating_the_file(_video, audio_path):
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(b"partial")
        raise RuntimeError("codec not supported")

    monkeypatch.setattr(
        x_video_ingest, "_extract_audio", explode_after_creating_the_file
    )

    with pytest.raises(XVideoIngestFailedError, match="codec not supported"):
        x_video_ingest.run_x_video_ingest(_SAMPLE_URL, confirm=True)

    audio_dir = storage.AUDIO_DIR / "x-raytar"
    assert not list(audio_dir.glob("*.part")), "a stale .part was left in data/audio"


def test_an_existing_audio_asset_is_not_downloaded_again(monkeypatch, tmp_data_dirs):
    """Recovery from a failed transcription must not re-fetch a 260 MB video.

    The extracted WAV is already the durable artifact; re-running should resume from
    it rather than starting over at the network.
    """

    from types import SimpleNamespace

    from podcast_ingest_core import storage, x_video_ingest

    monkeypatch.setattr(
        x_video_ingest, "_resolve_metadata", lambda _url: dict(_SAMPLE_INFO)
    )

    def refuse(*_args, **_kwargs):
        raise AssertionError("existing audio must not trigger another download")

    monkeypatch.setattr(x_video_ingest, "_download_video", refuse)
    monkeypatch.setattr(x_video_ingest, "_extract_audio", refuse)
    monkeypatch.setattr(
        x_video_ingest,
        "transcribe_episode",
        lambda *_a, **_k: SimpleNamespace(json_path=tmp_data_dirs / "t.json"),
    )

    existing = storage.audio_asset_path(
        "x-raytar",
        "2071290493581840707",
        "Code with Claude Prompt Engineering Breakout",
        ".wav",
    )
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_bytes(b"already extracted")

    result = x_video_ingest.run_x_video_ingest(_SAMPLE_URL, confirm=True)

    assert result.confirmed is True
    assert result.audio_path == str(existing)


def test_a_failed_seed_write_leaves_no_partial_seed(monkeypatch, tmp_data_dirs):
    """The intake bootstrap stages seeds through .part; this path must match.

    A bare write_text leaves truncated JSON at the real path if it dies mid-write.
    """

    from types import SimpleNamespace

    from podcast_ingest_core import storage, x_video_ingest

    monkeypatch.setattr(
        x_video_ingest, "_resolve_metadata", lambda _url: dict(_SAMPLE_INFO)
    )
    monkeypatch.setattr(
        x_video_ingest, "_download_video", lambda _url, work_dir: _fake_video(work_dir)
    )
    monkeypatch.setattr(
        x_video_ingest,
        "_extract_audio",
        lambda _video, audio_path: audio_path.write_bytes(b"RIFFfake"),
    )
    monkeypatch.setattr(
        x_video_ingest,
        "transcribe_episode",
        lambda *_a, **_k: SimpleNamespace(json_path=tmp_data_dirs / "t.json"),
    )

    original_write_text = Path.write_text

    def fail_on_the_seed(self, *args, **kwargs):
        if self.name.endswith(".episode-seed.json.part"):
            raise OSError("disk full")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_on_the_seed)

    with pytest.raises(Exception):
        x_video_ingest.run_x_video_ingest(_SAMPLE_URL, confirm=True)

    seed_path = storage.corpus_episode_seed_asset_path(
        "x-raytar", "2071290493581840707"
    )
    assert not seed_path.exists(), "a partial seed was left at the canonical path"


def _fake_video(work_dir):
    work_dir.mkdir(parents=True, exist_ok=True)
    video_path = work_dir / "video.mp4"
    video_path.write_bytes(b"video")
    return video_path
