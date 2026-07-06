from types import SimpleNamespace

import pytest


def _entry(
    title,
    *,
    description="",
    published="Sun, 16 Jun 2024 01:02:03 GMT",
    duration=None,
    guid=None,
    link=None,
    audio_url=None,
):
    links = []
    if audio_url is not None:
        links.append({"href": audio_url, "type": "audio/mpeg", "rel": "enclosure"})

    entry = {
        "title": title,
        "description": description,
        "published": published,
        "links": links,
    }
    if duration is not None:
        entry["itunes_duration"] = duration
    if guid is not None:
        entry["id"] = guid
    if link is not None:
        entry["link"] = link
    return entry


def _fake_feed(entries):
    return SimpleNamespace(entries=entries, bozo=False)


def test_list_episodes_normalizes_mock_rss(monkeypatch):
    from podcast_ingest_core import feed_reader

    monkeypatch.setattr(
        feed_reader.feedparser,
        "parse",
        lambda _url: _fake_feed(
            [
                _entry(
                    "EP672 又新高拉",
                    description="<p>保留 HTML</p>",
                    duration="01:23:45",
                    guid="guid-672",
                    link="https://example.com/ep672",
                    audio_url="https://example.com/ep672.mp3",
                ),
                _entry("EP671 前一集"),
                _entry("沒有編號的特別集"),
            ]
        ),
    )

    episodes = feed_reader.list_episodes("gooaye", limit=5)

    assert len(episodes) == 3
    assert all(episode.title for episode in episodes)
    assert episodes[0].podcast_id == "gooaye"
    assert episodes[0].episode_ref == "EP672"
    assert episodes[0].description == "<p>保留 HTML</p>"
    assert episodes[0].published_at == "Sun, 16 Jun 2024 01:02:03 GMT"
    assert episodes[0].duration == "01:23:45"
    assert episodes[0].guid == "guid-672"
    assert episodes[0].link == "https://example.com/ep672"
    assert episodes[0].source_url == "https://example.com/ep672"
    assert episodes[0].audio_url == "https://example.com/ep672.mp3"
    assert episodes[2].audio_url is None


def test_list_episodes_respects_limit(monkeypatch):
    from podcast_ingest_core import feed_reader

    monkeypatch.setattr(
        feed_reader.feedparser,
        "parse",
        lambda _url: _fake_feed(
            [_entry("EP672 又新高拉"), _entry("EP671 前一集"), _entry("EP670 再前一集")]
        ),
    )

    episodes = feed_reader.list_episodes("gooaye", limit=2)

    assert [episode.episode_ref for episode in episodes] == ["EP672", "EP671"]


def test_get_episode_supports_latest_and_case_insensitive_lookup(monkeypatch):
    from podcast_ingest_core import feed_reader

    monkeypatch.setattr(
        feed_reader.feedparser,
        "parse",
        lambda _url: _fake_feed([_entry("EP672 又新高拉"), _entry("EP671 前一集")]),
    )

    latest = feed_reader.get_episode("gooaye", "latest")
    lower = feed_reader.get_episode("gooaye", "ep672")
    upper = feed_reader.get_episode("gooaye", "EP672")

    assert latest.episode_ref == "EP672"
    assert lower == upper


def test_get_episode_searches_beyond_default_list_limit(monkeypatch):
    from podcast_ingest_core import feed_reader

    entries = [_entry(f"EP{672 - index} 近期集數") for index in range(10)]
    entries.append(_entry("EP600 較舊集數"))
    monkeypatch.setattr(feed_reader.feedparser, "parse", lambda _url: _fake_feed(entries))

    episode = feed_reader.get_episode("gooaye", "EP600")

    assert episode.episode_ref == "EP600"


def test_get_episode_raises_clear_error_when_not_found(monkeypatch):
    from podcast_ingest_core import feed_reader
    from podcast_ingest_core.errors import EpisodeNotFoundError

    monkeypatch.setattr(
        feed_reader.feedparser,
        "parse",
        lambda _url: _fake_feed([_entry("EP672 又新高拉")]),
    )

    with pytest.raises(EpisodeNotFoundError, match="EP999"):
        feed_reader.get_episode("gooaye", "EP999")


def test_mapping_config_format_is_supported(tmp_path):
    from podcast_ingest_core.config import load_podcast_profiles

    config_path = tmp_path / "podcasts.yaml"
    config_path.write_text(
        """
podcasts:
  gooaye:
    display_name: "Gooaye 股癌"
    rss_url: "https://example.com/feed.xml"
    language: "zh"
    default_episode_prefix: "EP"
""".strip(),
        encoding="utf-8",
    )

    profiles = load_podcast_profiles(config_path)

    assert profiles["gooaye"].rss_url == "https://example.com/feed.xml"
