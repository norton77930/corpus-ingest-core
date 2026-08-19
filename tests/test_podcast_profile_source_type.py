from pathlib import Path

import pytest

from podcast_ingest_core.config import load_podcast_profiles


def _write_config(tmp_path: Path, body: str) -> Path:
    config_path = tmp_path / "podcasts.yaml"
    config_path.write_text(body, encoding="utf-8")
    return config_path


def test_youtube_profile_parses_without_rss_fields(tmp_path):
    config_path = _write_config(
        tmp_path,
        """
podcasts:
  yt-foo-bar:
    display_name: Foo Bar
    source_type: yt-video
    language: en
""",
    )

    profile = load_podcast_profiles(config_path)["yt-foo-bar"]
    assert profile.source_type == "yt-video"
    assert profile.language == "en"
    assert profile.rss_url is None
    assert profile.default_episode_prefix is None


def test_non_rss_profile_parses_without_rss_fields(tmp_path):
    """A non-RSS source has no feed, so the RSS-only fields must be optional."""

    config_path = _write_config(
        tmp_path,
        """
podcasts:
  x-raytar:
    display_name: "@Raytar (X)"
    source_type: x-video
    language: en
""",
    )

    profiles = load_podcast_profiles(config_path)

    profile = profiles["x-raytar"]
    assert profile.source_type == "x-video"
    assert profile.language == "en"
    assert profile.rss_url is None
    assert profile.default_episode_prefix is None


def test_profile_without_source_type_defaults_to_rss_and_still_requires_feed_fields(tmp_path):
    """Every profile written before this feature must keep behaving identically."""

    config_path = _write_config(
        tmp_path,
        """
podcasts:
  gooaye:
    display_name: Gooaye
    rss_url: https://example.invalid/feed.xml
    language: zh
    default_episode_prefix: EP
""",
    )

    profile = load_podcast_profiles(config_path)["gooaye"]

    assert profile.source_type == "rss"
    assert profile.rss_url == "https://example.invalid/feed.xml"
    assert profile.default_episode_prefix == "EP"


def test_rss_profile_missing_its_feed_url_is_still_rejected(tmp_path):
    """Optional-for-non-RSS must not weaken the RSS case into silence."""

    config_path = _write_config(
        tmp_path,
        """
podcasts:
  gooaye:
    display_name: Gooaye
    language: zh
    default_episode_prefix: EP
""",
    )

    with pytest.raises(ValueError, match="rss_url"):
        load_podcast_profiles(config_path)


def test_language_is_required_even_for_a_non_rss_source(tmp_path):
    """Transcription reads only ``profile.language``, so it cannot be optional."""

    config_path = _write_config(
        tmp_path,
        """
podcasts:
  x-raytar:
    display_name: "@Raytar (X)"
    source_type: x-video
""",
    )

    with pytest.raises(ValueError, match="language"):
        load_podcast_profiles(config_path)


# --- Spec 037: summary_profile -----------------------------------------------


def test_profile_without_summary_profile_defaults_to_finance(tmp_path):
    """Every profile written before Spec 037 must keep the finance shape."""

    config_path = _write_config(
        tmp_path,
        """
podcasts:
  gooaye:
    display_name: Gooaye
    rss_url: https://example.invalid/feed.xml
    language: zh
    default_episode_prefix: EP
""",
    )

    assert load_podcast_profiles(config_path)["gooaye"].summary_profile == "finance"


def test_summary_profile_is_independent_of_source_type(tmp_path):
    """An RSS source may want learning notes; that is the whole point of the
    field being separate from ``source_type``."""

    config_path = _write_config(
        tmp_path,
        """
podcasts:
  x-raytar:
    display_name: "@Raytar (X)"
    source_type: x-video
    language: en
    summary_profile: learning-notes
  lecture-feed:
    display_name: Lecture Feed
    rss_url: https://example.invalid/feed.xml
    language: en
    default_episode_prefix: EP
    summary_profile: learning-notes
""",
    )

    profiles = load_podcast_profiles(config_path)

    assert profiles["x-raytar"].summary_profile == "learning-notes"
    assert profiles["lecture-feed"].source_type == "rss"
    assert profiles["lecture-feed"].summary_profile == "learning-notes"


def test_unknown_summary_profile_is_refused_at_load(tmp_path):
    """A typo must fail before it can cost an LLM call, and must name both the
    bad value and the known ones."""

    from podcast_ingest_core.errors import UnknownSummaryProfileError

    config_path = _write_config(
        tmp_path,
        """
podcasts:
  x-raytar:
    display_name: "@Raytar (X)"
    source_type: x-video
    language: en
    summary_profile: leraning-notes
""",
    )

    with pytest.raises(UnknownSummaryProfileError) as excinfo:
        load_podcast_profiles(config_path)

    message = str(excinfo.value)
    assert "leraning-notes" in message
    assert "learning-notes" in message
    assert "finance" in message


def test_non_string_summary_profile_is_refused_not_silently_defaulted(tmp_path):
    """``_optional_text`` turns a non-string into None. Routing summary_profile
    through it would make ``summary_profile: 123`` silently mean finance."""

    from podcast_ingest_core.errors import UnknownSummaryProfileError

    config_path = _write_config(
        tmp_path,
        """
podcasts:
  x-raytar:
    display_name: "@Raytar (X)"
    source_type: x-video
    language: en
    summary_profile: 123
""",
    )

    with pytest.raises(UnknownSummaryProfileError):
        load_podcast_profiles(config_path)


def test_explicit_null_summary_profile_is_refused(tmp_path):
    """An operator who writes the key and leaves it empty wrote something
    deliberate. Treating that as "unconfigured" was the last silent path."""

    from podcast_ingest_core.errors import UnknownSummaryProfileError

    config_path = _write_config(
        tmp_path,
        """
podcasts:
  x-raytar:
    display_name: "@Raytar (X)"
    source_type: x-video
    language: en
    summary_profile:
""",
    )

    with pytest.raises(UnknownSummaryProfileError):
        load_podcast_profiles(config_path)
