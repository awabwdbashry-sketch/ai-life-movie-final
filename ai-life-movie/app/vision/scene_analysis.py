"""Lightweight scene/category classification.

Full deep scene-classification models are heavy to download/run on a CPU-only
box, so this module uses fast, deterministic CV heuristics (color, brightness,
time-of-day, saturation) to guess a scene label from a fixed taxonomy. When a
Gemini API key is configured, `app.ai.media_analyzer` additionally asks Gemini
for a richer semantic label on a *sampled subset* of media (not every file),
and that result takes precedence when available.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import cv2
import numpy as np

SCENE_TAXONOMY = [
    "beach", "sunset", "nature", "city", "indoor", "night", "food",
    "portrait", "group", "vehicle", "event", "unknown",
]


def heuristic_scene_label(path: Path, captured_at: dt.datetime | None, has_people: bool, face_count: int) -> str:
    img = cv2.imread(str(path))
    if img is None:
        return "unknown"

    small = cv2.resize(img, (160, 90))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

    mean_val = float(np.mean(val))
    mean_sat = float(np.mean(sat))

    blue_ratio = float(np.mean((hue > 90) & (hue < 130) & (sat > 40)))
    green_ratio = float(np.mean((hue > 35) & (hue < 85) & (sat > 40)))
    warm_ratio = float(np.mean(((hue < 20) | (hue > 165)) & (sat > 60) & (val > 120)))

    hour = captured_at.hour if captured_at else 12

    if mean_val < 60:
        return "night"
    if face_count >= 3:
        return "group"
    if face_count >= 1 and mean_sat < 90:
        return "portrait"
    if warm_ratio > 0.18 and hour >= 17:
        return "sunset"
    if blue_ratio > 0.25 and green_ratio < 0.05:
        return "beach"
    if green_ratio > 0.3:
        return "nature"
    if has_people and mean_sat > 70:
        return "event"
    if mean_sat < 40 and mean_val > 150:
        return "indoor"
    return "city"
