"""Image processing: thumbnail generation, blur/brightness/quality scoring.

Uses OpenCV for numeric analysis (fast, CPU-only) and Pillow for I/O/thumbnails.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from app.utils.logging import get_logger

log = get_logger(__name__)

THUMBNAIL_SIZE = (480, 480)
ANALYSIS_MAX_DIM = 720  # downscale before heavy analysis to save CPU


@dataclass
class ImageQuality:
    blur_score: float  # higher = sharper
    brightness_score: float  # 0-255 average luma
    contrast_score: float
    quality_score: float  # combined 0-100


def make_thumbnail(src: Path, dst: Path, size: tuple[int, int] = THUMBNAIL_SIZE) -> None:
    """Create an orientation-corrected thumbnail preserving aspect ratio."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img)  # respect EXIF orientation
        img = img.convert("RGB")
        img.thumbnail(size, Image.LANCZOS)
        img.save(dst, "JPEG", quality=85)


def _load_cv_downscaled(path: Path, max_dim: int = ANALYSIS_MAX_DIM) -> np.ndarray | None:
    img = cv2.imread(str(path))
    if img is None:
        return None
    h, w = img.shape[:2]
    scale = min(1.0, max_dim / max(h, w))
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def analyze_quality(path: Path) -> ImageQuality:
    """Compute blur (Laplacian variance), brightness, contrast, and a combined score."""
    img = _load_cv_downscaled(path)
    if img is None:
        return ImageQuality(0.0, 0.0, 0.0, 0.0)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Sharpness: variance of Laplacian. Typical sharp photos score in the hundreds+.
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    blur_score = float(min(laplacian_var, 1000.0)) / 10.0  # normalize to ~0-100

    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))

    # Brightness scoring: penalize extremes (too dark / blown out), ideal ~110-190
    if 90 <= brightness <= 200:
        brightness_score = 100.0
    else:
        distance = min(abs(brightness - 90), abs(brightness - 200)) if brightness < 90 or brightness > 200 else 0
        brightness_score = max(0.0, 100.0 - distance * 1.2)

    contrast_score = float(min(contrast / 64.0, 1.0) * 100.0)

    quality_score = round(
        0.45 * min(blur_score, 100.0) + 0.35 * brightness_score + 0.20 * contrast_score, 1
    )
    return ImageQuality(
        blur_score=round(blur_score, 1),
        brightness_score=round(brightness, 1),
        contrast_score=round(contrast_score, 1),
        quality_score=quality_score,
    )


def compute_phash(path: Path) -> str:
    """Perceptual hash for duplicate/near-duplicate detection."""
    import imagehash

    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            return str(imagehash.phash(img))
    except Exception as exc:
        log.warning("phash failed for %s: %s", path.name, exc)
        return ""
