"""Metadata extraction for images (EXIF via Pillow) and videos (ffprobe)."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from PIL import ExifTags, Image

from app.utils.logging import get_logger

log = get_logger(__name__)

_EXIF_DATE_TAGS = ("DateTimeOriginal", "DateTime", "DateTimeDigitized")


@dataclass
class ImageMetadata:
    width: int = 0
    height: int = 0
    format: str = ""
    file_size: int = 0
    captured_at: dt.datetime | None = None
    orientation: int = 1
    exif: dict = field(default_factory=dict)


@dataclass
class VideoMetadata:
    width: int = 0
    height: int = 0
    duration_seconds: float = 0.0
    fps: float = 0.0
    codec: str = ""
    file_size: int = 0
    captured_at: dt.datetime | None = None
    has_audio: bool = False


def _parse_exif_date(value: str) -> dt.datetime | None:
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(value.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def extract_image_metadata(path: Path) -> ImageMetadata:
    """Extract width/height/format/EXIF/creation-date from an image file."""
    file_size = path.stat().st_size if path.exists() else 0
    try:
        with Image.open(path) as img:
            width, height = img.size
            fmt = (img.format or path.suffix.lstrip(".")).upper()
            orientation = 1
            captured_at = None
            exif_data = {}
            try:
                exif_raw = img.getexif()
                if exif_raw:
                    for tag_id, value in exif_raw.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        if tag_name == "Orientation":
                            orientation = int(value) if isinstance(value, (int, float)) else 1
                        if tag_name in _EXIF_DATE_TAGS and captured_at is None:
                            captured_at = _parse_exif_date(str(value))
                        if isinstance(value, (str, int, float)):
                            exif_data[tag_name] = value
            except Exception as exc:  # EXIF parsing can fail on odd files
                log.debug("EXIF parse issue for %s: %s", path.name, exc)

            if captured_at is None:
                # Fallback to file modification time
                captured_at = dt.datetime.fromtimestamp(path.stat().st_mtime)

            return ImageMetadata(
                width=width,
                height=height,
                format=fmt,
                file_size=file_size,
                captured_at=captured_at,
                orientation=orientation,
                exif=exif_data,
            )
    except Exception as exc:
        log.warning("Failed to read image metadata for %s: %s", path.name, exc)
        fallback_time = None
        try:
            fallback_time = dt.datetime.fromtimestamp(path.stat().st_mtime)
        except OSError:
            pass
        return ImageMetadata(file_size=file_size, captured_at=fallback_time)


def extract_video_metadata(path: Path) -> VideoMetadata:
    """Extract duration/resolution/fps/codec via ffprobe. Falls back gracefully."""
    file_size = path.stat().st_size if path.exists() else 0
    default_time = dt.datetime.fromtimestamp(path.stat().st_mtime) if path.exists() else None

    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(result.stderr[:300])
        data = json.loads(result.stdout)
    except Exception as exc:
        log.warning("ffprobe failed for %s: %s", path.name, exc)
        return VideoMetadata(file_size=file_size, captured_at=default_time)

    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = data.get("format", {})

    width = int(video_stream.get("width", 0)) if video_stream else 0
    height = int(video_stream.get("height", 0)) if video_stream else 0
    codec = video_stream.get("codec_name", "") if video_stream else ""

    fps = 0.0
    if video_stream and video_stream.get("avg_frame_rate"):
        try:
            num, denom = video_stream["avg_frame_rate"].split("/")
            denom_f = float(denom) or 1.0
            fps = round(float(num) / denom_f, 2)
        except Exception:
            fps = 0.0

    duration = 0.0
    try:
        duration = float(fmt.get("duration") or (video_stream or {}).get("duration") or 0.0)
    except Exception:
        duration = 0.0

    captured_at = default_time
    tags = fmt.get("tags", {}) or {}
    for key in ("creation_time", "com.apple.quicktime.creationdate"):
        if key in tags:
            try:
                captured_at = dt.datetime.fromisoformat(tags[key].replace("Z", "+00:00")).replace(tzinfo=None)
                break
            except Exception:
                continue

    return VideoMetadata(
        width=width,
        height=height,
        duration_seconds=round(duration, 2),
        fps=fps,
        codec=codec,
        file_size=file_size,
        captured_at=captured_at,
        has_audio=audio_stream is not None,
    )
