"""Background music selection & generation.

IMPORTANT: This app never downloads or bundles copyrighted commercial music.
Two music sources are supported:
  1. User-provided track (uploaded by the user — their own responsibility/rights).
  2. A small built-in catalog of *procedurally synthesized* ambient beds,
     generated on-the-fly with ffmpeg's audio synthesis filters (sine-wave
     pads mixed and shaped per movie style). These are clearly synthetic
     placeholder/demo tracks, not real recordings.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from app.utils.config import MUSIC_DIR
from app.utils.logging import get_logger

log = get_logger(__name__)

# style -> (base chord frequencies Hz, tempo feel, description)
TRACK_CATALOG = {
    "warm_memories": {
        "name": "Warm Memories",
        "freqs": [196.0, 246.94, 293.66],  # G major-ish triad, low & warm
        "description": "Slow, warm synthesized pad — fits cinematic/memories styles.",
    },
    "gentle_travel": {
        "name": "Gentle Travel",
        "freqs": [261.63, 329.63, 392.0],  # C major triad, brighter
        "description": "Bright, flowing synthesized pad — fits travel style.",
    },
    "uplifting_pulse": {
        "name": "Uplifting Pulse",
        "freqs": [293.66, 349.23, 440.0],
        "description": "Slightly faster, hopeful synthesized pad — fits dynamic/social styles.",
    },
    "minimal_air": {
        "name": "Minimal Air",
        "freqs": [220.0, 277.18],
        "description": "Sparse two-note synthesized ambience — fits minimal style.",
    },
    "silence": {
        "name": "No Music",
        "freqs": [],
        "description": "No background music — narration/ambient audio only.",
    },
}

STYLE_DEFAULT_TRACK = {
    "cinematic": "warm_memories",
    "travel": "gentle_travel",
    "memories": "warm_memories",
    "dynamic": "uplifting_pulse",
    "minimal": "minimal_air",
    "social": "uplifting_pulse",
}


def list_tracks() -> list[dict]:
    return [{"id": k, **{kk: vv for kk, vv in v.items() if kk != "freqs"}} for k, v in TRACK_CATALOG.items()]


def default_track_for_style(style: str) -> str:
    return STYLE_DEFAULT_TRACK.get(style, "warm_memories")


def generate_track(track_id: str, duration_seconds: float, dst_path: Path) -> bool:
    """Synthesize a looping ambient pad of the requested duration using ffmpeg."""
    track = TRACK_CATALOG.get(track_id, TRACK_CATALOG["warm_memories"])
    duration_seconds = max(1.0, duration_seconds)
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    if not track["freqs"]:
        # Silence track
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo:d={duration_seconds}",
            str(dst_path),
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0 and dst_path.exists()

    # Build a mixed sine-wave pad, gently faded in/out, low volume so it sits
    # comfortably under narration.
    inputs = []
    filter_parts = []
    for i, freq in enumerate(track["freqs"]):
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={freq}:duration={duration_seconds}:sample_rate=44100"]
        filter_parts.append(f"[{i}:a]volume=0.18[a{i}]")

    mix_inputs = "".join(f"[a{i}]" for i in range(len(track["freqs"])))
    filter_complex = (
        ";".join(filter_parts)
        + f";{mix_inputs}amix=inputs={len(track['freqs'])}:duration=longest[mixed]"
        + f";[mixed]afade=t=in:st=0:d=2,afade=t=out:st={max(0.0, duration_seconds - 2)}:d=2[out]"
    )

    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", filter_complex, "-map", "[out]", str(dst_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=90)
        if result.returncode != 0:
            log.warning("Music synthesis failed: %s", result.stderr.decode(errors="ignore")[:300])
            return False
        return dst_path.exists()
    except Exception as exc:
        log.warning("Music synthesis exception: %s", exc)
        return False


def resolve_music_path(track_id: str, duration_seconds: float, cache_dir: Path) -> Path | None:
    """Get (generating + caching if needed) the audio file path for a track id."""
    if track_id not in TRACK_CATALOG:
        track_id = "warm_memories"
    if track_id == "silence":
        return None
    dst = cache_dir / f"music_{track_id}_{int(duration_seconds)}s.wav"
    if not dst.exists():
        ok = generate_track(track_id, duration_seconds, dst)
        if not ok:
            return None
    return dst
