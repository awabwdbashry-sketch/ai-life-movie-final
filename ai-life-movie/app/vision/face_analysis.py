"""Lightweight face/people-presence detection.

Uses OpenCV's bundled Haar cascade classifiers, which ship with opencv-python
(no extra model download required) and run comfortably on CPU. This is
intentionally lightweight rather than a full deep face-recognition pipeline —
we only need "are there people in this shot" for narrative/selection purposes.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2

from app.utils.logging import get_logger

log = get_logger(__name__)

_face_cascade = None


def _get_cascade():
    global _face_cascade
    if _face_cascade is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _face_cascade = cv2.CascadeClassifier(cascade_path)
    return _face_cascade


@dataclass
class FaceResult:
    face_count: int
    has_people: bool


def detect_faces(path: Path) -> FaceResult:
    img = cv2.imread(str(path))
    if img is None:
        return FaceResult(0, False)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Downscale for speed on large images
    h, w = gray.shape[:2]
    scale = min(1.0, 800 / max(h, w))
    if scale < 1.0:
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)))

    cascade = _get_cascade()
    try:
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    except Exception as exc:
        log.warning("Face detection failed for %s: %s", path.name, exc)
        return FaceResult(0, False)

    count = len(faces)
    return FaceResult(face_count=count, has_people=count > 0)
