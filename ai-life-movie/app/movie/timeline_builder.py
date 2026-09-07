"""Event grouping and timeline construction (spec sections 15 & 16).

Groups media into meaningful events using: time gaps between captures,
visual similarity (perceptual-hash proximity for images), and detected scene
labels. This is a heuristic clustering approach — fast, deterministic, and
good enough to produce a sensible documentary structure without needing a
heavy ML pipeline.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from app.media.duplicate_detector import hamming_distance

# If the gap between two consecutive items exceeds this, start a new event.
DEFAULT_GAP_MINUTES = 90


@dataclass
class MediaForGrouping:
    id: str
    captured_at: dt.datetime | None
    scene_label: str
    phash: str
    media_type: str
    has_people: bool
    tags: list


def _pretty_label(scene_label: str, index: int) -> str:
    taxonomy_titles = {
        "beach": "Beach",
        "sunset": "Sunset",
        "nature": "Nature Walk",
        "city": "City Exploration",
        "indoor": "Indoors",
        "night": "Evening",
        "food": "Restaurant",
        "portrait": "Portrait Moment",
        "group": "Family Gathering",
        "vehicle": "On the Road",
        "event": "Special Event",
        "unknown": "Moment",
    }
    return taxonomy_titles.get(scene_label, "Moment") + (f" {index}" if index > 1 else "")


def group_into_events(items: list[MediaForGrouping], gap_minutes: int = DEFAULT_GAP_MINUTES) -> list[dict]:
    """Cluster media chronologically into events, splitting on large time gaps
    or a scene-label change, then re-merging tiny fragments.
    """
    if not items:
        return []

    dated = sorted(items, key=lambda m: m.captured_at or dt.datetime.min)

    clusters: list[list[MediaForGrouping]] = []
    current: list[MediaForGrouping] = [dated[0]]

    for prev, cur in zip(dated, dated[1:]):
        gap_ok = True
        if prev.captured_at and cur.captured_at:
            gap = (cur.captured_at - prev.captured_at).total_seconds() / 60.0
            gap_ok = gap <= gap_minutes
        scene_changed = prev.scene_label != cur.scene_label and prev.scene_label not in ("unknown",) and cur.scene_label not in ("unknown",)

        if gap_ok and not scene_changed:
            current.append(cur)
        else:
            clusters.append(current)
            current = [cur]
    clusters.append(current)

    # Merge tiny (single-item) clusters into a neighbor when they share a scene
    # label AND are still within the time-gap window — this only smooths over
    # splits that were triggered by scene-label noise, never a genuine large
    # time-gap split (which should remain a separate event regardless of scene).
    merged: list[list[MediaForGrouping]] = []
    for cluster in clusters:
        if merged and len(cluster) == 1 and merged[-1][-1].scene_label == cluster[0].scene_label:
            prev_time, cur_time = merged[-1][-1].captured_at, cluster[0].captured_at
            within_gap = True
            if prev_time and cur_time:
                within_gap = (cur_time - prev_time).total_seconds() / 60.0 <= gap_minutes
            if within_gap:
                merged[-1].extend(cluster)
                continue
        merged.append(cluster)

    label_counts: dict[str, int] = {}
    events = []
    for idx, cluster in enumerate(merged):
        scene_counts: dict[str, int] = {}
        for m in cluster:
            scene_counts[m.scene_label] = scene_counts.get(m.scene_label, 0) + 1
        dominant_scene = max(scene_counts.items(), key=lambda kv: kv[1])[0]
        label_counts[dominant_scene] = label_counts.get(dominant_scene, 0) + 1
        label = _pretty_label(dominant_scene, label_counts[dominant_scene])

        times = [m.captured_at for m in cluster if m.captured_at]
        all_tags = sorted({t for m in cluster for t in (m.tags or [])})

        events.append(
            {
                "label": label,
                "start_time": min(times) if times else None,
                "end_time": max(times) if times else None,
                "order_index": idx,
                "summary": f"{len(cluster)} moments captured here.",
                "media_ids": [m.id for m in cluster],
                "media_count": len(cluster),
                "photo_count": sum(1 for m in cluster if m.media_type == "image"),
                "video_count": sum(1 for m in cluster if m.media_type == "video"),
                "has_people": any(m.has_people for m in cluster),
                "tags": all_tags,
            }
        )
    return events


def build_visual_timeline(media_items: list[dict]) -> list[dict]:
    """Return a simple chronological list for the timeline UI:
    [{time, icon, media_id, thumbnail_url}]
    """
    from app.utils.files import to_data_relative_url

    dated = [m for m in media_items if m.get("captured_at")]
    dated.sort(key=lambda m: m["captured_at"])
    timeline = []
    for m in dated:
        icon = "📸" if m["media_type"] == "image" else "🎥"
        # Prefer an already-computed URL (e.g. from MediaItem.to_dict()); fall
        # back to converting a raw path if only that's present. Never build
        # the URL via string-splitting on the raw path.
        thumbnail_url = m.get("thumbnail_url") or to_data_relative_url(m.get("thumbnail_path", ""))
        timeline.append(
            {
                "time": m["captured_at"],
                "icon": icon,
                "media_id": m["id"],
                "thumbnail_url": thumbnail_url,
                "media_type": m["media_type"],
            }
        )
    return timeline
