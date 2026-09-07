"""Scene-cut detection using ffmpeg's native `select=gt(scene,T)` filter.

This is far cheaper than decoding every frame in Python — ffmpeg does the
histogram-difference scoring internally in C and we just parse timestamps.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from app.utils.logging import get_logger

log = get_logger(__name__)

_TIME_RE = re.compile(r"pts_time:([\d.]+)")


def detect_scene_cuts(video_path: Path, threshold: float = 0.35, max_cuts: int = 40) -> list[float]:
    """Return a list of timestamps (seconds) where ffmpeg detects a scene change."""
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-filter:v", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception as exc:
        log.warning("scene detection failed for %s: %s", video_path.name, exc)
        return []

    # ffmpeg writes showinfo to stderr
    timestamps = [float(m.group(1)) for m in _TIME_RE.finditer(result.stderr)]
    return timestamps[:max_cuts]
