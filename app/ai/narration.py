"""Text-to-speech narration generation.

Uses `pyttsx3` (backed by the offline `espeak-ng` engine on Linux). This is
fully offline/local — no external API key or network call required — which
also means it works identically in demo mode and production mode. English
and Arabic are both supported via espeak-ng's built-in voices.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from app.utils.logging import get_logger

log = get_logger(__name__)

_VOICE_MAP = {
    "en": "en-us",
    "ar": "ar",
}


def narration_available() -> bool:
    import shutil

    return shutil.which("espeak-ng") is not None


def synthesize_narration(text: str, dst_path: Path, language: str = "en", rate_wpm: int = 155) -> bool:
    """Render `text` to a WAV file at `dst_path`. Returns True on success."""
    if not text.strip():
        return False
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    voice = _VOICE_MAP.get(language, "en-us")

    # Use espeak-ng directly via subprocess for reliability/headless environments
    # (pyttsx3 wraps this but can be flaky without a display / audio device).
    cmd = [
        "espeak-ng", "-v", voice, "-s", str(rate_wpm), "-w", str(dst_path), text,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode != 0:
            log.warning("espeak-ng failed: %s", result.stderr.decode(errors="ignore")[:300])
            return False
        return dst_path.exists() and dst_path.stat().st_size > 0
    except Exception as exc:
        log.warning("Narration synthesis failed: %s", exc)
        return False


def estimate_duration_seconds(text: str, rate_wpm: int = 155) -> float:
    """Rough duration estimate before synthesis (for pacing decisions)."""
    words = max(1, len(text.split()))
    return round(words / (rate_wpm / 60.0), 1)
