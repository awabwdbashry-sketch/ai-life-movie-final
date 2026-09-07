"""Combined 0-100 quality score used for media selection.

Factors: sharpness (blur), brightness, contrast, face visibility bonus,
duplicate penalty, corruption penalty.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QualityFactors:
    blur_score: float = 0.0
    brightness_score: float = 0.0
    contrast_score: float = 0.0
    has_people: bool = False
    face_count: int = 0
    is_duplicate: bool = False
    is_corrupted: bool = False


def compute_final_score(factors: QualityFactors) -> float:
    if factors.is_corrupted:
        return 0.0

    base = 0.45 * min(factors.blur_score, 100.0) + 0.35 * min(factors.brightness_score, 100.0) + 0.20 * min(
        factors.contrast_score, 100.0
    )

    face_bonus = 0.0
    if factors.has_people:
        face_bonus = 5.0 if factors.face_count <= 4 else 2.0  # small groups favored slightly over huge crowds

    duplicate_penalty = 15.0 if factors.is_duplicate else 0.0

    score = base + face_bonus - duplicate_penalty
    return round(max(0.0, min(100.0, score)), 1)
