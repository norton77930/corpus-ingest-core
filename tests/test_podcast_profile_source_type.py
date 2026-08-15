from pathlib import Path

import pytest

from podcast_ingest_core.config import load_podcast_profiles


def _write_config(tmp_path: Path, body: str) -> Path:
    config_path = tmp_path / "podcasts.yaml"
    config_path.write_text(body, encoding="utf-8")
    return config_path


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
