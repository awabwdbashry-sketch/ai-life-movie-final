"""Orchestrates the full analysis pipeline for one media item.

Combines: metadata extraction, quality scoring, duplicate hashing, face
detection, scene classification and coarse object tagging. Heavy per-frame
work is intentionally minimized (see app.media.video_processor for video
frame sampling strategy).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

from app.media.image_processor import analyze_quality, compute_phash, make_thumbnail
from app.media.metadata import extract_image_metadata, extract_video_metadata
from app.media.video_processor import (
    extract_thumbnail,
    sample_and_score_frames,
    select_best_segment,
    video_overall_quality,
)
from app.vision.face_analysis import detect_faces
from app.vision.object_detection import detect_objects
from app.vision.quality_analysis import QualityFactors, compute_final_score
from app.vision.scene_analysis import heuristic_scene_label
from app.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class AnalysisResult:
    media_type: str
    width: int = 0
    height: int = 0
    file_size: int = 0
    duration_seconds: float = 0.0
    fps: float = 0.0
    codec: str = ""
    has_audio: bool = False
    captured_at: dt.datetime | None = None
    thumbnail_path: str = ""
    quality_score: float = 0.0
    blur_score: float = 0.0
    brightness_score: float = 0.0
    phash: str = ""
    has_people: bool = False
    face_count: int = 0
    scene_label: str = "unknown"
    tags: list = field(default_factory=list)
    selected_start: float = 0.0
    selected_end: float = 0.0
    raw: dict = field(default_factory=dict)


def analyze_image(src_path: Path, thumbnail_dst: Path) -> AnalysisResult:
    meta = extract_image_metadata(src_path)
    make_thumbnail(src_path, thumbnail_dst)
    quality = analyze_quality(src_path)
    phash = compute_phash(src_path)
    faces = detect_faces(src_path)
    scene = heuristic_scene_label(src_path, meta.captured_at, faces.has_people, faces.face_count)
    tags = detect_objects(src_path)

    final_score = compute_final_score(
        QualityFactors(
            blur_score=quality.blur_score,
            brightness_score=100.0 if 90 <= quality.brightness_score <= 200 else max(
                0.0, 100.0 - min(abs(quality.brightness_score - 90), abs(quality.brightness_score - 200)) * 1.2
            ),
            contrast_score=quality.contrast_score,
            has_people=faces.has_people,
            face_count=faces.face_count,
            is_duplicate=False,  # duplicate clustering happens at the project level afterwards
            is_corrupted=(meta.width == 0 or meta.height == 0),
        )
    )

    return AnalysisResult(
        media_type="image",
        width=meta.width,
        height=meta.height,
        file_size=meta.file_size,
        captured_at=meta.captured_at,
        thumbnail_path=str(thumbnail_dst),
        quality_score=final_score,
        blur_score=quality.blur_score,
        brightness_score=quality.brightness_score,
        phash=phash,
        has_people=faces.has_people,
        face_count=faces.face_count,
        scene_label=scene,
        tags=tags,
        raw={"format": meta.format, "orientation": meta.orientation},
    )


def analyze_video(src_path: Path, thumbnail_dst: Path) -> AnalysisResult:
    meta = extract_video_metadata(src_path)
    mid_point = meta.duration_seconds * 0.3 if meta.duration_seconds else 0.0
    extract_thumbnail(src_path, thumbnail_dst, at_seconds=mid_point)

    frames = sample_and_score_frames(src_path, meta.duration_seconds)
    clip_length = min(5.0, meta.duration_seconds) if meta.duration_seconds else 0.0
    start, end = select_best_segment(frames, meta.duration_seconds, clip_length=clip_length or 3.0)

    overall_quality = video_overall_quality(src_path, thumbnail_dst)
    faces = detect_faces(thumbnail_dst) if thumbnail_dst.exists() else None
    has_people = faces.has_people if faces else False
    face_count = faces.face_count if faces else 0
    scene = (
        heuristic_scene_label(thumbnail_dst, meta.captured_at, has_people, face_count)
        if thumbnail_dst.exists()
        else "unknown"
    )
    tags = detect_objects(thumbnail_dst) if thumbnail_dst.exists() else []

    avg_brightness = sum(f.brightness for f in frames) / len(frames) if frames else 128.0
    avg_blur = sum(f.quality_score for f in frames) / len(frames) if frames else overall_quality

    return AnalysisResult(
        media_type="video",
        width=meta.width,
        height=meta.height,
        file_size=meta.file_size,
        duration_seconds=meta.duration_seconds,
        fps=meta.fps,
        codec=meta.codec,
        has_audio=meta.has_audio,
        captured_at=meta.captured_at,
        thumbnail_path=str(thumbnail_dst),
        quality_score=overall_quality,
        blur_score=round(avg_blur, 1),
        brightness_score=round(avg_brightness, 1),
        phash="",  # video dedup by content is out of scope; handled via scene/thumbnail similarity if needed
        has_people=has_people,
        face_count=face_count,
        scene_label=scene,
        tags=tags,
        selected_start=start,
        selected_end=end,
    )
