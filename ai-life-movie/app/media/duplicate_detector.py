"""Duplicate / near-duplicate detection using perceptual hashing (pHash).

Items are never deleted — only flagged, so the selection algorithm can pick
the best-quality representative of each duplicate cluster.
"""
from __future__ import annotations

import imagehash

HAMMING_DUPLICATE_THRESHOLD = 8  # <=8 bits difference ~ near-duplicate for 64-bit phash


def hamming_distance(hash_a: str, hash_b: str) -> int:
    try:
        return imagehash.hex_to_hash(hash_a) - imagehash.hex_to_hash(hash_b)
    except Exception:
        return 999


def find_duplicate_clusters(items: list[dict]) -> list[list[str]]:
    """Given items as [{'id':..., 'phash':...}], return clusters of ids that are
    near-duplicates of one another (union-find on Hamming distance).
    """
    valid = [it for it in items if it.get("phash")]
    parent = {it["id"]: it["id"] for it in valid}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    n = len(valid)
    for i in range(n):
        for j in range(i + 1, n):
            dist = hamming_distance(valid[i]["phash"], valid[j]["phash"])
            if dist <= HAMMING_DUPLICATE_THRESHOLD:
                union(valid[i]["id"], valid[j]["id"])

    clusters: dict[str, list[str]] = {}
    for it in valid:
        root = find(it["id"])
        clusters.setdefault(root, []).append(it["id"])

    return [members for members in clusters.values() if len(members) > 1]


def mark_duplicates(items: list[dict]) -> dict[str, str]:
    """Return a mapping {duplicate_id: best_id} for every item that should be
    flagged as a duplicate of a better (or first-seen) item in its cluster.
    Best = highest quality_score, tie-broken by earliest capture time.
    """
    clusters = find_duplicate_clusters(items)
    by_id = {it["id"]: it for it in items}
    result: dict[str, str] = {}

    for cluster in clusters:
        members = [by_id[i] for i in cluster]
        best = max(members, key=lambda m: (m.get("quality_score", 0.0), -_sort_key(m)))
        for m in members:
            if m["id"] != best["id"]:
                result[m["id"]] = best["id"]
    return result


def _sort_key(item: dict) -> float:
    ts = item.get("captured_at_ts")
    return float(ts) if ts is not None else 0.0
