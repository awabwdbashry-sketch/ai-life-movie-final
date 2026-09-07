"""Tests for the combined 0-100 quality scoring system."""
from __future__ import annotations

from app.vision.quality_analysis import QualityFactors, compute_final_score


def test_corrupted_media_scores_zero():
    factors = QualityFactors(blur_score=90, brightness_score=90, contrast_score=90, is_corrupted=True)
    assert compute_final_score(factors) == 0.0


def test_high_quality_sharp_bright_scores_high():
    factors = QualityFactors(blur_score=100, brightness_score=100, contrast_score=100)
    score = compute_final_score(factors)
    assert score > 90


def test_duplicate_penalty_reduces_score():
    base = QualityFactors(blur_score=100, brightness_score=100, contrast_score=100)
    dup = QualityFactors(blur_score=100, brightness_score=100, contrast_score=100, is_duplicate=True)
    assert compute_final_score(dup) < compute_final_score(base)


def test_small_group_face_bonus_applied():
    no_faces = QualityFactors(blur_score=50, brightness_score=50, contrast_score=50)
    small_group = QualityFactors(blur_score=50, brightness_score=50, contrast_score=50, has_people=True, face_count=2)
    assert compute_final_score(small_group) > compute_final_score(no_faces)


def test_score_is_clamped_between_0_and_100():
    factors = QualityFactors(blur_score=1000, brightness_score=1000, contrast_score=1000)
    assert 0.0 <= compute_final_score(factors) <= 100.0
