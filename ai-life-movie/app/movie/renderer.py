"""Low-level ffmpeg rendering primitives.

Everything here shells out to ffmpeg (CPU-only, H.264/AAC output). Kept
deterministic and debuggable: every intermediate clip is a real file on disk,
so a failure can be inspected/reproduced by re-running the printed command.
"""
from __future__ import annotations

import random
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.utils.logging import get_logger

log = get_logger(__name__)

ASPECT_RESOLUTIONS = {
    "16:9": (1280, 720),
    "9:16": (720, 1280),
    "1:1": (960, 960),
}

FPS = 25


class RenderError(RuntimeError):
    """Raised with a human-readable message; technical detail is logged separately."""


def _run(cmd: list[str], timeout: int = 300) -> None:
    log.debug("ffmpeg command: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="ignore")
        log.error("ffmpeg failed (%s): %s", cmd[0], stderr[-2000:])
        raise RenderError("A step in movie rendering failed. See logs for technical detail.")


@dataclass
class KenBurnsPlan:
    zoom_start: float
    zoom_end: float
    pan_x: float  # -1..1 (left..right)
    pan_y: float  # -1..1 (up..down)


_KEN_BURNS_VARIANTS = [
    KenBurnsPlan(1.0, 1.12, 0.0, 0.0),    # slow zoom in, centered
    KenBurnsPlan(1.12, 1.0, 0.0, 0.0),    # slow zoom out
    KenBurnsPlan(1.05, 1.05, -1.0, 0.0),  # pan left
    KenBurnsPlan(1.05, 1.05, 1.0, 0.0),   # pan right
    KenBurnsPlan(1.0, 1.08, 0.0, -0.6),   # slight upward drift + zoom
]


def pick_ken_burns(index: int) -> KenBurnsPlan:
    return _KEN_BURNS_VARIANTS[index % len(_KEN_BURNS_VARIANTS)]


def render_image_clip(
    src: Path, dst: Path, duration: float, aspect_ratio: str, index: int = 0
) -> None:
    """Render a still image into a short H.264 clip with a subtle Ken Burns
    (zoom/pan) effect, cropped/padded to the target aspect ratio without
    stretching the source content.
    """
    w, h = ASPECT_RESOLUTIONS.get(aspect_ratio, ASPECT_RESOLUTIONS["16:9"])
    plan = pick_ken_burns(index)
    total_frames = max(1, int(duration * FPS))

    # Oversized canvas so zoompan has room to move without exposing edges.
    upscale_w, upscale_h = w * 2, h * 2

    zoom_expr = f"'{plan.zoom_start}+({plan.zoom_end}-{plan.zoom_start})*on/{total_frames}'"
    max_dx = (upscale_w - w) / 2
    max_dy = (upscale_h - h) / 2
    x_expr = f"'(iw-ow)/2+{plan.pan_x}*{max_dx}*on/{total_frames}'"
    y_expr = f"'(ih-oh)/2+{plan.pan_y}*{max_dy}*on/{total_frames}'"

    vf = (
        f"scale={upscale_w}:{upscale_h}:force_original_aspect_ratio=increase,"
        f"crop={upscale_w}:{upscale_h},"
        f"zoompan=z={zoom_expr}:x={x_expr}:y={y_expr}:d={total_frames}:s={w}x{h}:fps={FPS},"
        f"format=yuv420p"
    )
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(src),
        "-t", str(duration), "-vf", vf,
        "-r", str(FPS), "-pix_fmt", "yuv420p", "-an",
        "-c:v", "libx264", "-preset", "veryfast", str(dst),
    ]
    _run(cmd)


def render_video_clip(
    src: Path, dst: Path, start: float, end: float, aspect_ratio: str
) -> None:
    """Trim a video to [start, end], scale/crop to target aspect ratio (no
    stretching), strip audio (final audio is narration+music, mixed separately).
    """
    w, h = ASPECT_RESOLUTIONS.get(aspect_ratio, ASPECT_RESOLUTIONS["16:9"])
    duration = max(0.5, end - start)
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},format=yuv420p"
    )
    cmd = [
        "ffmpeg", "-y", "-ss", str(start), "-i", str(src), "-t", str(duration),
        "-vf", vf, "-r", str(FPS), "-pix_fmt", "yuv420p", "-an",
        "-c:v", "libx264", "-preset", "veryfast", str(dst),
    ]
    _run(cmd)


def chain_xfade(clip_paths: list[Path], durations: list[float], transition: str, transition_duration: float, dst: Path) -> None:
    """Concatenate normalized clips with crossfade transitions via ffmpeg's xfade filter."""
    if len(clip_paths) == 1:
        cmd = ["ffmpeg", "-y", "-i", str(clip_paths[0]), "-c", "copy", str(dst)]
        _run(cmd)
        return

    inputs = []
    for p in clip_paths:
        inputs += ["-i", str(p)]

    filter_parts = []
    prev_label = "0:v"
    cumulative = durations[0]
    for i in range(1, len(clip_paths)):
        offset = max(0.05, cumulative - transition_duration)
        out_label = f"v{i}"
        filter_parts.append(
            f"[{prev_label}][{i}:v]xfade=transition={transition}:duration={transition_duration}:offset={offset:.3f}[{out_label}]"
        )
        cumulative = cumulative + durations[i] - transition_duration
        prev_label = out_label

    filter_complex = ";".join(filter_parts)
    cmd = [
        "ffmpeg", "-y", *inputs, "-filter_complex", filter_complex,
        "-map", f"[{prev_label}]", "-r", str(FPS), "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", str(dst),
    ]
    _run(cmd, timeout=600)


def delay_audio(src: Path, dst: Path, delay_ms: int) -> None:
    """Pad an audio file with silence so it starts at `delay_ms` into the track."""
    delay_ms = max(0, delay_ms)
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-af", f"adelay={delay_ms}|{delay_ms}",
        "-ac", "2", str(dst),
    ]
    _run(cmd)


def mix_audio_tracks(tracks: list[Path], weights: list[float], total_duration: float, dst: Path) -> bool:
    """Mix several (already time-aligned) audio tracks into one, trimmed to total_duration."""
    if not tracks:
        return False
    inputs = []
    for t in tracks:
        inputs += ["-i", str(t)]
    filter_parts = [f"[{i}:a]volume={w}[a{i}]" for i, w in enumerate(weights)]
    mix_in = "".join(f"[a{i}]" for i in range(len(tracks)))
    filter_complex = ";".join(filter_parts) + f";{mix_in}amix=inputs={len(tracks)}:duration=longest:dropout_transition=0[mixed]"
    cmd = [
        "ffmpeg", "-y", *inputs, "-filter_complex", filter_complex,
        "-map", "[mixed]", "-t", str(total_duration), str(dst),
    ]
    _run(cmd)
    return dst.exists()


def mux_video_audio(video: Path, audio: Path | None, dst: Path) -> None:
    """Combine final video with final mixed audio track into the deliverable MP4."""
    if audio and audio.exists():
        cmd = [
            "ffmpeg", "-y", "-i", str(video), "-i", str(audio),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k",
            "-shortest", str(dst),
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-i", str(video),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-an", str(dst),
        ]
    _run(cmd, timeout=600)


def burn_subtitles(video: Path, srt_path: Path, dst: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-i", str(video),
        "-vf", f"subtitles={srt_path}:force_style='FontName=DejaVu Sans,FontSize=22,PrimaryColour=&HFFFFFF&'",
        "-c:a", "copy", str(dst),
    ]
    _run(cmd, timeout=600)


def extract_movie_thumbnail(video: Path, dst: Path, at_fraction: float = 0.3) -> bool:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        duration = float(result.stdout.strip() or 1.0)
    except Exception:
        duration = 1.0
    at = max(0.0, duration * at_fraction)
    cmd = ["ffmpeg", "-y", "-ss", str(at), "-i", str(video), "-frames:v", "1", "-vf", "scale=480:-2", str(dst)]
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    return result.returncode == 0 and dst.exists()
