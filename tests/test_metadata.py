"""Tests for image/video metadata extraction."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from PIL import Image

from app.media.metadata import extract_image_metadata, extract_video_metadata


@pytest.fixture()
def sample_image(tmp_path) -> Path:
    path = tmp_path / "sample.jpg"
    img = Image.new("RGB", (640, 480), color=(120, 130, 140))
    img.save(path, "JPEG")
    return path


@pytest.fixture()
def sample_video(tmp_path) -> Path:
    path = tmp_path / "sample.mp4"
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=320x240:duration=2:rate=10",
        str(path),
    ]
    subprocess.run(cmd, capture_output=True, timeout=30)
    return path


def test_extract_image_metadata_reads_dimensions(sample_image):
    meta = extract_image_metadata(sample_image)
    assert meta.width == 640
    assert meta.height == 480
    assert meta.format == "JPEG"
    assert meta.file_size > 0
    assert meta.captured_at is not None  # falls back to mtime when no EXIF


def test_extract_image_metadata_handles_missing_file(tmp_path):
    fake = tmp_path / "does_not_exist.jpg"
    meta = extract_image_metadata(fake)
    # Should not raise; returns a default/empty-ish result
    assert meta.width == 0


def test_extract_video_metadata_reads_duration_and_resolution(sample_video):
    meta = extract_video_metadata(sample_video)
    assert meta.width == 320
    assert meta.height == 240
    assert meta.duration_seconds == pytest.approx(2.0, abs=0.5)
    assert meta.fps > 0
