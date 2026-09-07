"""High-level movie-building orchestration.

Combines: selected images/clips + Ken Burns motion + transitions + narration
+ music + optional subtitles into a single deterministic rendering pipeline.
Each stage writes real intermediate files (nothing purely in-memory), so a
failure can be inspected and reproduced.
"""
from __future__ import annotations

import datetime as dt
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.ai.narration import estimate_duration_seconds, narration_available, synthesize_narration
from app.movie import music as music_module
from app.movie.renderer import (
    ASPECT_RESOLUTIONS,
    chain_xfade,
    delay_audio,
    extract_movie_thumbnail,
    mix_audio_tracks,
    mux_video_audio,
    render_image_clip,
    render_video_clip,
)
from app.movie.transitions import pick_transition, transition_duration
from app.utils.logging import get_logger

log = get_logger(__name__)

MIN_IMAGE_DURATION = 2.0
MAX_IMAGE_DURATION = 6.0
MIN_VIDEO_CLIP = 2.0
MAX_VIDEO_CLIP = 6.0
NARRATION_VOLUME = 1.0
MUSIC_VOLUME = 0.22


@dataclass
class ClipPlan:
    media_id: str
    media_type: str
    src_path: str
    duration: float
    start: float = 0.0
    end: float = 0.0
    event_id: str | None = None


@dataclass
class BuildResult:
    output_path: Path
    thumbnail_path: Path
    duration_seconds: float
    resolution: str
    subtitle_path: Path | None


def plan_clip_durations(items: list[dict], target_duration_seconds: int) -> list[ClipPlan]:
    """Decide each clip's on-screen duration: videos use their pre-selected
    best segment length (clamped); the remaining time budget is split evenly
    across images.
    """
    plans: list[ClipPlan] = []
    video_total = 0.0
    video_items = [m for m in items if m["media_type"] == "video"]
    image_items = [m for m in items if m["media_type"] == "image"]

    for m in video_items:
        seg = max(MIN_VIDEO_CLIP, min(MAX_VIDEO_CLIP, (m.get("selected_end", 0) - m.get("selected_start", 0)) or 3.0))
        video_total += seg

    remaining = max(0.0, target_duration_seconds - video_total)
    per_image = remaining / len(image_items) if image_items else 0.0
    per_image = max(MIN_IMAGE_DURATION, min(MAX_IMAGE_DURATION, per_image or MIN_IMAGE_DURATION))

    for m in items:  # preserve overall chronological/selected order
        if m["media_type"] == "video":
            seg = max(MIN_VIDEO_CLIP, min(MAX_VIDEO_CLIP, (m.get("selected_end", 0) - m.get("selected_start", 0)) or 3.0))
            plans.append(
                ClipPlan(
                    media_id=m["id"], media_type="video", src_path=m["storage_path"],
                    duration=seg, start=m.get("selected_start", 0.0),
                    end=m.get("selected_start", 0.0) + seg, event_id=m.get("event_id"),
                )
            )
        else:
            plans.append(
                ClipPlan(
                    media_id=m["id"], media_type="image", src_path=m["storage_path"],
                    duration=per_image, event_id=m.get("event_id"),
                )
            )
    return plans


def compute_clip_start_times(plans: list[ClipPlan], trans_duration: float) -> list[float]:
    starts = [0.0]
    for i in range(1, len(plans)):
        starts.append(starts[i - 1] + plans[i - 1].duration - trans_duration)
    return starts


def _write_srt(entries: list[tuple[float, float, str]], dst: Path) -> None:
    def fmt(t: float) -> str:
        t = max(0.0, t)
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, (start, end, text) in enumerate(entries, 1):
        lines.append(str(i))
        lines.append(f"{fmt(start)} --> {fmt(end)}")
        lines.append(text)
        lines.append("")
    dst.write_text("\n".join(lines), encoding="utf-8")


def build_movie(
    *,
    project_id: str,
    items: list[dict],
    story: dict,
    style: str,
    aspect_ratio: str,
    target_duration_seconds: int,
    narration_enabled: bool,
    subtitles_enabled: bool,
    music_track: str,
    language: str,
    work_dir: Path,
    events: list[dict] | None = None,
    progress_cb=None,
) -> BuildResult:
    """Render the final movie. `progress_cb(message, percent)` is called for UI updates."""

    def report(msg: str, pct: int) -> None:
        if progress_cb:
            progress_cb(msg, pct)

    if not items:
        raise ValueError("No media items were selected for this movie.")

    clips_dir = work_dir / "clips"
    narr_dir = work_dir / "narration"
    music_dir = work_dir / "music"
    final_dir = work_dir / "final"
    for d in (clips_dir, narr_dir, music_dir, final_dir):
        d.mkdir(parents=True, exist_ok=True)

    trans_name_style = style
    trans_duration = transition_duration(style)

    report("Planning clip durations", 5)
    plans = plan_clip_durations(items, target_duration_seconds)

    report("Rendering individual clips", 15)
    rendered_paths: list[Path] = []
    durations: list[float] = []
    for i, plan in enumerate(plans):
        dst = clips_dir / f"clip_{i:03d}.mp4"
        src = Path(plan.src_path)
        if plan.media_type == "image":
            render_image_clip(src, dst, plan.duration, aspect_ratio, index=i)
        else:
            render_video_clip(src, dst, plan.start, plan.end, aspect_ratio)
        rendered_paths.append(dst)
        durations.append(plan.duration)
        report(f"Rendering clip {i + 1}/{len(plans)}", 15 + int(30 * (i + 1) / len(plans)))

    report("Applying transitions", 48)
    merged_video = final_dir / "merged_video.mp4"
    # A single consistent transition duration keeps the offset math correct;
    # we vary only the *type* of transition occasionally for texture.
    transition_name = pick_transition(trans_name_style, 0, vary=False)
    chain_xfade(rendered_paths, durations, transition_name, trans_duration, merged_video)

    total_duration = sum(durations) - trans_duration * max(0, len(durations) - 1)
    total_duration = max(1.0, total_duration)
    clip_starts = compute_clip_start_times(plans, trans_duration)

    report("Generating narration", 58)
    narration_tracks: list[Path] = []
    narration_weights: list[float] = []
    srt_entries: list[tuple[float, float, str]] = []

    if narration_enabled and narration_available():
        # Map each story chapter to the start time of the first clip belonging
        # to its event, giving coarse (event-level) audio/visual sync.
        event_first_start: dict[str, float] = {}
        for plan, start in zip(plans, clip_starts):
            if plan.event_id and plan.event_id not in event_first_start:
                event_first_start[plan.event_id] = start

        label_to_event_id: dict[str, str] = {e["label"]: e["id"] for e in (events or [])}
        chapters = story.get("chapters", [])
        cursor = 0.0
        # Opening narration at t=0
        opening_text = story.get("opening", "")
        if opening_text:
            wav = narr_dir / "opening.wav"
            if synthesize_narration(opening_text, wav, language=language):
                narration_tracks.append(wav)
                narration_weights.append(NARRATION_VOLUME)
                dur = estimate_duration_seconds(opening_text)
                srt_entries.append((0.0, dur, opening_text))
                cursor = dur + 0.5

        for idx, ch in enumerate(chapters):
            text = ch.get("narration", "")
            if not text:
                continue
            wav = narr_dir / f"chapter_{idx:02d}.wav"
            if not synthesize_narration(text, wav, language=language):
                continue
            # Prefer syncing to the matching event's visual start if we can
            # resolve the chapter's event_label to a real event's first clip —
            # but never start before the previous narration line has finished,
            # so lines never overlap even when two events start close together.
            ev_id = label_to_event_id.get(ch.get("event_label", ""))
            desired_start = event_first_start.get(ev_id, cursor) if ev_id else cursor
            target_start = max(desired_start, cursor)
            delayed = narr_dir / f"chapter_{idx:02d}_delayed.wav"
            delay_audio(wav, delayed, int(max(0.0, target_start) * 1000))
            narration_tracks.append(delayed)
            narration_weights.append(NARRATION_VOLUME)
            dur = estimate_duration_seconds(text)
            srt_entries.append((target_start, target_start + dur, text))
            cursor = target_start + dur + 0.5

        ending_text = story.get("ending", "")
        if ending_text:
            wav = narr_dir / "ending.wav"
            dur = estimate_duration_seconds(ending_text)
            # Prefer placing the ending near the finish, but never before the
            # last narration line has finished (avoids overlap on short movies).
            desired_start = max(0.0, total_duration - dur - 1.0)
            target_start = max(desired_start, cursor)
            if synthesize_narration(ending_text, wav, language=language):
                delayed = narr_dir / "ending_delayed.wav"
                delay_audio(wav, delayed, int(target_start * 1000))
                narration_tracks.append(delayed)
                narration_weights.append(NARRATION_VOLUME)
                srt_entries.append((target_start, target_start + dur, ending_text))
    else:
        report("Narration disabled or unavailable — skipping", 60)

    report("Selecting background music", 68)
    music_path = music_module.resolve_music_path(music_track, total_duration, music_dir)

    report("Mixing audio", 74)
    mix_tracks = list(narration_tracks)
    mix_weights = list(narration_weights)
    if music_path:
        mix_tracks.append(music_path)
        mix_weights.append(MUSIC_VOLUME)

    final_audio = None
    if mix_tracks:
        final_audio = final_dir / "final_audio.wav"
        ok = mix_audio_tracks(mix_tracks, mix_weights, total_duration, final_audio)
        if not ok:
            final_audio = None

    report("Finalizing render", 85)
    output_path = final_dir / "movie.mp4"
    mux_video_audio(merged_video, final_audio, output_path)

    subtitle_path = None
    if subtitles_enabled and srt_entries:
        srt_path = final_dir / "subtitles.srt"
        _write_srt(srt_entries, srt_path)
        burned_path = final_dir / "movie_subtitled.mp4"
        try:
            from app.movie.renderer import burn_subtitles

            burn_subtitles(output_path, srt_path, burned_path)
            output_path = burned_path
        except Exception as exc:
            log.warning("Subtitle burn-in failed, keeping unsubtitled movie + srt file: %s", exc)
        subtitle_path = srt_path

    report("Extracting preview thumbnail", 95)
    thumb_path = final_dir / "thumbnail.jpg"
    extract_movie_thumbnail(output_path, thumb_path)

    w, h = ASPECT_RESOLUTIONS.get(aspect_ratio, ASPECT_RESOLUTIONS["16:9"])
    return BuildResult(
        output_path=output_path,
        thumbnail_path=thumb_path,
        duration_seconds=round(total_duration, 1),
        resolution=f"{w}x{h}",
        subtitle_path=subtitle_path,
    )
