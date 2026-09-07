"""Safe file-handling utilities: filename sanitization, MIME/extension checks,
path traversal protection. Never trust an uploaded filename directly.
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import quote

from app.utils.config import ALLOWED_EXT, ALLOWED_IMAGE_EXT, ALLOWED_VIDEO_EXT, DATA_DIR
from app.utils.logging import get_logger

log = get_logger(__name__)

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9_.-]")
_WINDOWS_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]")


class UnsupportedFileError(ValueError):
    pass


def sanitize_filename(original_name: str) -> str:
    """Strip any path components and unsafe characters from a filename."""
    name = Path(original_name).name  # drop any directory / traversal components
    name = name.strip().replace(" ", "_")
    name = _SAFE_CHARS.sub("", name)
    if not name or name in {".", ".."}:
        name = "file"
    return name[-180:]  # keep it reasonably short


def validate_extension(filename: str) -> str:
    """Return the lowercase extension if allowed, else raise."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise UnsupportedFileError(
            f"File type '{ext or 'unknown'}' is not supported. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXT))}"
        )
    return ext


def is_image_ext(ext: str) -> bool:
    return ext.lower() in ALLOWED_IMAGE_EXT


def is_video_ext(ext: str) -> bool:
    return ext.lower() in ALLOWED_VIDEO_EXT


def generate_storage_name(ext: str) -> str:
    """Generate a random, collision-free, safe storage filename."""
    return f"{uuid.uuid4().hex}{ext}"


def safe_join(base_dir: Path, *parts: str) -> Path:
    """Join path parts under base_dir, refusing any path-traversal attempt."""
    base_dir = base_dir.resolve()
    candidate = base_dir.joinpath(*parts).resolve()
    if base_dir not in candidate.parents and candidate != base_dir:
        raise ValueError("Path traversal detected — refusing to build path outside base directory.")
    return candidate


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def _pure_path_for(path_str: str):
    """Pick the correct *pure* (no filesystem access) path implementation for
    a stored path string, based on what the string actually looks like —
    never based on which OS is currently running this code.

    This matters because a path recorded by the app (and read back later,
    possibly for a test, a migration, or just introspection) should parse
    the same way regardless of host OS: a Windows path like
    'C:\\Users\\me\\...' must be recognized as a Windows path even when this
    code happens to run on Linux, and vice versa. Detection: a drive letter
    followed by ':' and a slash (either style), or the presence of a
    backslash, means Windows-style; otherwise POSIX-style.
    """
    if _WINDOWS_PATH_RE.match(path_str) or "\\" in path_str:
        return PureWindowsPath(path_str)
    return PurePosixPath(path_str)


def to_data_relative_url(path: str | Path | None, data_dir: str | Path = DATA_DIR) -> str:
    """Convert an absolute filesystem path that lives under `data_dir` into
    the correct '/data/...' URL for the browser.

    This is the single place that turns an on-disk path into a URL — no
    template or frontend code should ever do its own string-splitting on a
    raw path again. Using proper path parsing (never naive substring
    matching like `path.split('data/')`) means it is correct regardless of
    OS path separators or drive letters: a Windows absolute path such as
    'C:\\Users\\me\\app\\data\\projects\\p1\\movie.mp4' with
    data_dir='C:\\Users\\me\\app\\data' becomes '/data/projects/p1/movie.mp4'
    — never a URL containing 'C:' or a backslash.

    Returns '' (never raises) if `path` is falsy or cannot be resolved
    under `data_dir` — callers already treat an empty thumbnail/file URL as
    "not available yet".
    """
    if not path:
        return ""

    path_str = str(path)
    data_dir_str = str(data_dir)

    try:
        pure_path = _pure_path_for(path_str)
        pure_data_dir = _pure_path_for(data_dir_str)
        rel = pure_path.relative_to(pure_data_dir)
    except ValueError:
        log.warning("Path '%s' is not under DATA_DIR ('%s'); cannot build a /data URL for it.", path_str, data_dir_str)
        return ""

    # Build the URL with each path segment percent-encoded individually
    # (handles spaces/unicode safely) while keeping '/' as the separator —
    # this matches how Starlette's StaticFiles decodes incoming URLs.
    url_path = "/".join(quote(part) for part in rel.parts)
    return f"/data/{url_path}"
