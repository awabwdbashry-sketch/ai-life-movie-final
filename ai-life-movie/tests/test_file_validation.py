"""Tests for safe file-handling utilities: sanitization, extension validation,
path-traversal protection.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.utils.files import (
    UnsupportedFileError,
    generate_storage_name,
    human_size,
    is_image_ext,
    is_video_ext,
    safe_join,
    sanitize_filename,
    validate_extension,
)


def test_sanitize_filename_strips_path_components():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("/absolute/path/photo.jpg") == "photo.jpg"


def test_sanitize_filename_replaces_unsafe_chars():
    result = sanitize_filename("my photo! (final).jpg")
    assert " " not in result
    assert "!" not in result
    assert "(" not in result


def test_sanitize_filename_handles_empty_or_dotdot():
    assert sanitize_filename("") == "file"
    assert sanitize_filename("..") == "file"


def test_validate_extension_accepts_allowed_types():
    assert validate_extension("photo.JPG") == ".jpg"
    assert validate_extension("clip.mp4") == ".mp4"


def test_validate_extension_rejects_disallowed_types():
    with pytest.raises(UnsupportedFileError):
        validate_extension("script.exe")
    with pytest.raises(UnsupportedFileError):
        validate_extension("archive.zip")


def test_is_image_and_video_ext():
    assert is_image_ext(".jpg") is True
    assert is_image_ext(".mp4") is False
    assert is_video_ext(".mov") is True
    assert is_video_ext(".png") is False


def test_generate_storage_name_is_random_and_safe():
    a = generate_storage_name(".jpg")
    b = generate_storage_name(".jpg")
    assert a != b
    assert a.endswith(".jpg")


def test_safe_join_blocks_path_traversal(tmp_path):
    base = tmp_path / "uploads"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "..", "..", "etc", "passwd")


def test_safe_join_allows_valid_subpath(tmp_path):
    base = tmp_path / "uploads"
    base.mkdir()
    result = safe_join(base, "sub", "file.jpg")
    assert str(result).startswith(str(base.resolve()))


def test_human_size_formats_reasonably():
    assert human_size(500) == "500.0B"
    assert "KB" in human_size(2048)
    assert "MB" in human_size(5 * 1024 * 1024)
