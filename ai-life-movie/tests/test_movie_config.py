"""Tests for movie clip-duration planning and transition config."""
from __future__ import annotations

from app.movie.movie_builder import compute_clip_start_times, plan_clip_durations, ClipPlan
from app.movie.transitions import pick_transition, transition_duration


def test_plan_clip_durations_gives_videos_their_segment_length():
    items = [
        {"id": "v1", "media_type": "video", "storage_path": "/tmp/v1.mp4", "selected_start": 0.0, "selected_end": 4.0},
    ]
    plans = plan_clip_durations(items, target_duration_seconds=60)
    assert plans[0].duration == 4.0


def test_plan_clip_durations_splits_remaining_budget_across_images():
    # Budget of 20s over 2 images = 10s each, but image duration is clamped
    # to a MAX_IMAGE_DURATION of 6.0s (keeps individual stills from lingering
    # too long on screen), so both should land at the clamp.
    items = [
        {"id": "i1", "media_type": "image", "storage_path": "/tmp/i1.jpg"},
        {"id": "i2", "media_type": "image", "storage_path": "/tmp/i2.jpg"},
    ]
    plans = plan_clip_durations(items, target_duration_seconds=20)
    assert plans[0].duration == plans[1].duration == 6.0


def test_plan_clip_durations_clamps_image_duration():
    items = [{"id": f"i{i}", "media_type": "image", "storage_path": f"/tmp/i{i}.jpg"} for i in range(20)]
    plans = plan_clip_durations(items, target_duration_seconds=10)
    for p in plans:
        assert 2.0 <= p.duration <= 6.0


def test_compute_clip_start_times_accounts_for_transition_overlap():
    plans = [
        ClipPlan(media_id="a", media_type="image", src_path="", duration=5.0),
        ClipPlan(media_id="b", media_type="image", src_path="", duration=5.0),
        ClipPlan(media_id="c", media_type="image", src_path="", duration=5.0),
    ]
    starts = compute_clip_start_times(plans, trans_duration=1.0)
    assert starts == [0.0, 4.0, 8.0]


def test_pick_transition_returns_style_default():
    assert pick_transition("cinematic", 0, vary=False) == "fade"
    assert pick_transition("minimal", 3, vary=False) == "fade"


def test_transition_duration_known_styles():
    assert transition_duration("dynamic") < transition_duration("cinematic")
