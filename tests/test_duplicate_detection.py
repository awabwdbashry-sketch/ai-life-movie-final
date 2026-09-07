"""Tests for perceptual-hash based duplicate detection."""
from __future__ import annotations

from app.media.duplicate_detector import find_duplicate_clusters, hamming_distance, mark_duplicates


def test_hamming_distance_identical_hashes():
    h = "ffff0000ffff0000"
    assert hamming_distance(h, h) == 0


def test_hamming_distance_different_hashes():
    assert hamming_distance("ffffffffffffffff", "0000000000000000") == 64


def test_find_duplicate_clusters_groups_near_identical():
    items = [
        {"id": "a", "phash": "0f0f0f0f0f0f0f0f"},
        {"id": "b", "phash": "0f0f0f0f0f0f0f0e"},  # 1 bit different -> near-duplicate
        {"id": "c", "phash": "ffffffffffffffff"},  # very different
    ]
    clusters = find_duplicate_clusters(items)
    assert len(clusters) == 1
    assert set(clusters[0]) == {"a", "b"}


def test_mark_duplicates_prefers_higher_quality():
    items = [
        {"id": "a", "phash": "0f0f0f0f0f0f0f0f", "quality_score": 40.0, "captured_at_ts": 100},
        {"id": "b", "phash": "0f0f0f0f0f0f0f0e", "quality_score": 90.0, "captured_at_ts": 101},
    ]
    result = mark_duplicates(items)
    # 'a' (lower quality) should be marked as a duplicate of 'b' (higher quality)
    assert result.get("a") == "b"
    assert "b" not in result


def test_mark_duplicates_no_duplicates_when_all_distinct():
    items = [
        {"id": "a", "phash": "0000000000000000", "quality_score": 50.0},
        {"id": "b", "phash": "ffffffffffffffff", "quality_score": 50.0},
    ]
    result = mark_duplicates(items)
    assert result == {}


def test_mark_duplicates_ignores_items_without_phash():
    items = [{"id": "a", "phash": "", "quality_score": 50.0}, {"id": "b", "phash": "", "quality_score": 50.0}]
    result = mark_duplicates(items)
    assert result == {}
