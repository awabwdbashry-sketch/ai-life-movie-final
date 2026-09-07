"""Cinematic transition definitions, mapped to ffmpeg's `xfade` filter.

Kept intentionally small and tasteful — the spec explicitly warns against
overusing transitions, so we pick one sensible transition per style and vary
it only occasionally for texture.
"""
from __future__ import annotations

import random

# Subset of ffmpeg xfade transition names that read as "elegant" rather than gimmicky.
ELEGANT_TRANSITIONS = ["fade", "fadeblack", "dissolve", "smoothleft", "smoothright"]

STYLE_TRANSITION_DEFAULT = {
    "cinematic": "fade",
    "travel": "smoothleft",
    "memories": "dissolve",
    "dynamic": "smoothright",
    "minimal": "fade",
    "social": "fadeblack",
}

TRANSITION_DURATION = {
    "cinematic": 1.0,
    "travel": 0.6,
    "memories": 0.9,
    "dynamic": 0.35,
    "minimal": 0.7,
    "social": 0.3,
}


def pick_transition(style: str, index: int, vary: bool = True) -> str:
    base = STYLE_TRANSITION_DEFAULT.get(style, "fade")
    if vary and index % 5 == 4:  # occasional variation for texture, not chaos
        alt = [t for t in ELEGANT_TRANSITIONS if t != base]
        return random.choice(alt)
    return base


def transition_duration(style: str) -> float:
    return TRANSITION_DURATION.get(style, 0.7)
