"""Video processing: representative frame extraction, intelligent frame sampling,
scene-change detection, and best-segment selection — without decoding every frame.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.media.image_processor import analyze_quality
from app.utils.logging import get_logger

log = get_logger(__name__)

MAX_SAMPLES = 24  # cap sampled frames regardless of video length


@dataclass
class SampledFrame:
    timestamp: float
    quality_score: float
    brightness: float
    is_scene_change: bool


def extract_thumbnail(video_path: Path, dst: Path, at_seconds: float = 0.0) -> bool:
    """Grab a single representative frame via ffmpeg (cheap, no full decode)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-ss", str(max(0.0, at_seconds)), "-i", str(video_path),
        "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "3", str(dst),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    return result.returncode == 0 and dst.exists()


def _sample_timestamps(duration: float, n: int) -> list[float]:
    if duration <= 0:
        return [0.0]
    n = max(1, min(n, MAX_SAMPLES))
    # Avoid the very first/last 2% (often black frames / transitions)
    start, end = duration * 0.02, duration * 0.98
    if end <= start:
        return [duration / 2]
    return list(np.linspace(start, end, n))


def sample_and_score_frames(video_path: Path, duration: float) -> list[SampledFrame]:
    """Intelligently sample frames (not every frame) and score each for quality
    and scene-change likelihood, using OpenCV's frame-accurate seek.
    """
    # Sample roughly 1 frame every 2 seconds, capped at MAX_SAMPLES
    target_count = max(4, min(MAX_SAMPLES, int(duration / 2) or 4))
    timestamps = _sample_timestamps(duration, target_count)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        log.warning("Could not open video for sampling: %s", video_path.name)
        return []

    frames: list[SampledFrame] = []
    prev_hist = None
    try:
        for ts in timestamps:
            cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000.0)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            small = cv2.resize(frame, (160, 90))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            brightness = float(np.mean(gray))
            laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            quality = min(laplacian_var / 10.0, 100.0)

            hist = cv2.calcHist([gray], [0], None, [32], [0, 256])
            cv2.normalize(hist, hist)
            is_scene_change = False
            if prev_hist is not None:
                similarity = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                is_scene_change = similarity < 0.6
            prev_hist = hist

            frames.append(SampledFrame(ts, round(quality, 1), round(brightness, 1), is_scene_change))
    finally:
        cap.release()
    return frames


def select_best_segment(
    frames: list[SampledFrame], duration: float, clip_length: float = 5.0
) -> tuple[float, float]:
    """Pick the best `clip_length`-second window based on sampled frame quality,
    preferring windows right after a detected scene change (a new, interesting moment).
    """
    if duration <= clip_length or not frames:
        return 0.0, min(duration, clip_length) if duration else 0.0

    best_start = 0.0
    best_score = -1.0
    for f in frames:
        window_start = max(0.0, min(f.timestamp, duration - clip_length))
        window_end = window_start + clip_length
        window_frames = [x for x in frames if window_start <= x.timestamp <= window_end]
        if not window_frames:
            continue
        avg_quality = sum(x.quality_score for x in window_frames) / len(window_frames)
        scene_bonus = 15.0 if f.is_scene_change else 0.0
        brightness_penalty = 0.0
        avg_brightness = sum(x.brightness for x in window_frames) / len(window_frames)
        if avg_brightness < 30 or avg_brightness > 235:
            brightness_penalty = 20.0
        score = avg_quality + scene_bonus - brightness_penalty
        if score > best_score:
            best_score = score
            best_start = window_start

    return round(best_start, 2), round(min(best_start + clip_length, duration), 2)


def video_overall_quality(video_path: Path, thumbnail_path: Path) -> float:
    """Approximate overall quality score for a video using its representative thumbnail."""
    if thumbnail_path.exists():
        q = analyze_quality(thumbnail_path)
        return q.quality_score
    return 50.0
