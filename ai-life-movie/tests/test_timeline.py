"""Tests for chronological event grouping and timeline construction."""
from __future__ import annotations

import datetime as dt

from app.movie.timeline_builder import MediaForGrouping, build_visual_timeline, group_into_events


def _m(id_, minutes_offset, scene="city", media_type="image"):
    base = dt.datetime(2026, 6, 15, 8, 0, 0)
    return MediaForGrouping(
        id=id_,
        captured_at=base + dt.timedelta(minutes=minutes_offset),
        scene_label=scene,
        phash="",
        media_type=media_type,
        has_people=False,
        tags=[],
    )


def test_group_into_events_splits_on_large_time_gap():
    items = [
        _m("a", 0, scene="beach"),
        _m("b", 10, scene="beach"),
        _m("c", 300, scene="beach"),  # 5 hour gap -> new event
    ]
    events = group_into_events(items, gap_minutes=90)
    assert len(events) == 2
    assert events[0]["media_ids"] == ["a", "b"]
    assert events[1]["media_ids"] == ["c"]


def test_group_into_events_splits_on_scene_change():
    items = [
        _m("a", 0, scene="beach"),
        _m("b", 5, scene="city"),  # scene change, small gap
    ]
    events = group_into_events(items, gap_minutes=90)
    assert len(events) == 2


def test_group_into_events_keeps_same_scene_together():
    items = [_m("a", 0, scene="nature"), _m("b", 5, scene="nature"), _m("c", 10, scene="nature")]
    events = group_into_events(items, gap_minutes=90)
    assert len(events) == 1
    assert set(events[0]["media_ids"]) == {"a", "b", "c"}


def test_group_into_events_empty_input():
    assert group_into_events([]) == []


def test_build_visual_timeline_sorts_chronologically():
    media = [
        {"id": "b", "media_type": "image", "captured_at": dt.datetime(2026, 1, 1, 10, 0), "thumbnail_path": ""},
        {"id": "a", "media_type": "video", "captured_at": dt.datetime(2026, 1, 1, 9, 0), "thumbnail_path": ""},
    ]
    timeline = build_visual_timeline(media)
    assert [t["media_id"] for t in timeline] == ["a", "b"]
    assert timeline[0]["icon"] == "🎥"
    assert timeline[1]["icon"] == "📸"
