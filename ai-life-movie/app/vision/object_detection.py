"""Pluggable object detection.

Ultralytics YOLO gives the best results but pulls in a heavy (torch-based)
dependency chain that is impractical to require on a CPU-only, low-resource
machine for every install. We treat it as optional: if `ultralytics` is
importable and a model can be loaded, we use it; otherwise we fall back to a
fast heuristic tagger (color/edge-density based) so the pipeline keeps working
everywhere. This keeps object tagging useful without unnecessarily running
heavy AI models on every frame.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.utils.logging import get_logger

log = get_logger(__name__)

_YOLO_AVAILABLE = False
try:
    from ultralytics import YOLO  # type: ignore  # noqa: F401

    _YOLO_AVAILABLE = True
except Exception:
    _YOLO_AVAILABLE = False


@lru_cache
def _get_model():
    if not _YOLO_AVAILABLE:
        return None
    try:
        from ultralytics import YOLO

        return YOLO("yolov8n.pt")
    except Exception as exc:
        log.info("YOLO model unavailable, using heuristic tagging instead: %s", exc)
        return None


def detect_objects(path: Path, max_tags: int = 6) -> list[str]:
    """Return a small list of coarse tags for a media file's representative image."""
    model = _get_model()
    if model is not None:
        try:
            results = model.predict(source=str(path), verbose=False, conf=0.4)
            names = model.names
            tags: list[str] = []
            for r in results:
                for box in r.boxes:
                    label = names.get(int(box.cls), None) if hasattr(names, "get") else names[int(box.cls)]
                    if label and label not in tags:
                        tags.append(label)
            return tags[:max_tags]
        except Exception as exc:
            log.warning("YOLO inference failed for %s, falling back: %s", path.name, exc)

    return _heuristic_tags(path)


def _heuristic_tags(path: Path) -> list[str]:
    """A dependency-free fallback: edge density + color signature -> coarse tags."""
    import cv2
    import numpy as np

    img = cv2.imread(str(path))
    if img is None:
        return []
    small = cv2.resize(img, (160, 90))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    edge_density = float(np.mean(edges > 0))

    tags = []
    if edge_density > 0.12:
        tags.append("structure")
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    if float(np.mean((hsv[:, :, 0] > 90) & (hsv[:, :, 0] < 130))) > 0.2:
        tags.append("sky_or_water")
    if float(np.mean((hsv[:, :, 0] > 35) & (hsv[:, :, 0] < 85))) > 0.25:
        tags.append("greenery")
    return tags
