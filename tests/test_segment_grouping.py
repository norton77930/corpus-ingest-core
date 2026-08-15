from podcast_ingest_core.segment_grouping import group_segments


def _segment(segment_id: int, start: float, end: float, text: str) -> dict:
    return {"id": segment_id, "start": start, "end": end, "text": text}


def test_breaks_at_a_sentence_boundary_once_the_minimum_duration_is_reached():
    """A group closes on the first sentence end at or after ``min_duration``.

    The three early sentence ends are all under 30s, so they must not split the
    group; the one at 32s must.
    """

    segments = [
        _segment(1, 0.0, 8.0, "First sentence ends here."),
        _segment(2, 8.0, 16.0, "Second one too."),
        _segment(3, 16.0, 24.0, "Third as well."),
        _segment(4, 24.0, 32.0, "Fourth crosses thirty seconds."),
        _segment(5, 32.0, 40.0, "Next group starts."),
    ]

    groups = group_segments(segments)

    assert len(groups) == 2
    assert groups[0]["start"] == 0.0
    assert groups[0]["end"] == 32.0
    assert groups[0]["text"] == (
        "First sentence ends here. Second one too. Third as well. "
        "Fourth crosses thirty seconds."
    )
    assert [segment["id"] for segment in groups[0]["segments"]] == [1, 2, 3, 4]
    assert [segment["id"] for segment in groups[1]["segments"]] == [5]


def test_breaks_at_full_width_sentence_endings(monkeypatch):
    """The primary corpus is zh, whose sentences end with 。？！ not .?!

    With ASCII-only endings a Chinese transcript never soft-breaks and every group
    runs to the 90s hard cap, which defeats the point of grouping.
    """

    segments = [
        _segment(1, 0.0, 8.0, "第一句話在這裡結束。"),
        _segment(2, 8.0, 16.0, "第二句也是。"),
        _segment(3, 16.0, 24.0, "第三句同樣如此。"),
        _segment(4, 24.0, 32.0, "第四句跨過三十秒。"),
        _segment(5, 32.0, 40.0, "下一組從這裡開始。"),
    ]

    groups = group_segments(segments)

    assert len(groups) == 2
    assert [segment["id"] for segment in groups[0]["segments"]] == [1, 2, 3, 4]
    assert groups[0]["end"] == 32.0


def test_no_segments_yields_no_groups():
    assert group_segments([]) == []


def test_a_single_segment_longer_than_the_cap_is_not_split():
    """The cap closes a group; it cannot cut inside one segment.

    Pins a subtle property of the ported rule: the first segment of a group is
    admitted without a break check, so an over-long segment stays whole instead
    of being dropped or truncated.
    """

    segments = [
        _segment(1, 0.0, 200.0, "one very long unbroken stretch of speech"),
        _segment(2, 200.0, 205.0, "and a short follow up"),
    ]

    groups = group_segments(segments)

    assert len(groups) == 1
    assert [segment["id"] for segment in groups[0]["segments"]] == [1, 2]
    assert groups[0]["start"] == 0.0
    assert groups[0]["end"] == 205.0


def test_breaks_at_the_maximum_duration_even_without_a_sentence_ending():
    """Speech that never punctuates must still be capped, not grow unbounded."""

    segments = [
        _segment(index, float(index * 20), float((index + 1) * 20), "and then we keep going")
        for index in range(6)
    ]

    groups = group_segments(segments)

    assert len(groups) == 2
    # Segment 4 is the first whose end (100.0) reaches the 90s cap.
    assert [segment["id"] for segment in groups[0]["segments"]] == [0, 1, 2, 3, 4]
    assert groups[0]["end"] == 100.0
    assert [segment["id"] for segment in groups[1]["segments"]] == [5]
