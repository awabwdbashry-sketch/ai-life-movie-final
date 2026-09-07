"""Tests for the path→URL conversion layer (app.utils.files.to_data_relative_url).

This directly targets the real-world bug: on Windows, an absolute file path
looks like 'C:\\Users\\me\\app\\data\\projects\\...\\movie.mp4', and naive
string-splitting on 'data/' (forward slash) never matches, leaking the full
absolute Windows path — including the drive letter — into a URL sent to the
browser (e.g. '/data/C%3A/Users/me/...'), which 404s because it doesn't match
anything under the '/data' static mount.

These tests simulate Windows-style paths explicitly (via PureWindowsPath
detection in `_pure_path_for`) so the fix is verified regardless of which OS
actually runs the test suite — the bug is about path *parsing*, not about
which OS happens to execute pytest.
"""
from __future__ import annotations

from app.utils.files import _pure_path_for, to_data_relative_url


def test_windows_backslash_path_produces_clean_relative_url():
    data_dir = r"C:\Users\user\Desktop\ai-life-movie-final\ai-life-movie\data"
    file_path = (
        r"C:\Users\user\Desktop\ai-life-movie-final\ai-life-movie\data"
        r"\projects\proj123\renders\job456\final\movie.mp4"
    )
    url = to_data_relative_url(file_path, data_dir=data_dir)
    assert url == "/data/projects/proj123/renders/job456/final/movie.mp4"
    assert "C:" not in url
    assert "%3A" not in url
    assert "\\" not in url


def test_windows_forward_slash_drive_path_produces_clean_relative_url():
    # Windows also accepts forward slashes with a drive letter — this is the
    # exact shape seen in the reported bug's URL after decoding (%3A -> ':').
    data_dir = "C:/Users/user/Desktop/ai-life-movie-final/ai-life-movie/data"
    file_path = (
        "C:/Users/user/Desktop/ai-life-movie-final/ai-life-movie/data"
        "/projects/abc/renders/xyz/final/movie.mp4"
    )
    url = to_data_relative_url(file_path, data_dir=data_dir)
    assert url == "/data/projects/abc/renders/xyz/final/movie.mp4"
    assert "C:" not in url


def test_windows_path_thumbnail_example():
    data_dir = r"D:\media-app\data"
    thumb_path = r"D:\media-app\data\projects\p1\thumbnails\m1.jpg"
    url = to_data_relative_url(thumb_path, data_dir=data_dir)
    assert url == "/data/projects/p1/thumbnails/m1.jpg"


def test_posix_absolute_path_produces_clean_relative_url():
    data_dir = "/home/user/ai-life-movie/data"
    file_path = "/home/user/ai-life-movie/data/projects/proj123/final/movie.mp4"
    url = to_data_relative_url(file_path, data_dir=data_dir)
    assert url == "/data/projects/proj123/final/movie.mp4"


def test_empty_or_none_path_returns_empty_string():
    assert to_data_relative_url("") == ""
    assert to_data_relative_url(None) == ""


def test_path_outside_data_dir_returns_empty_string_without_raising():
    # A path that isn't under data_dir at all can't be served through the
    # /data static mount — must fail gracefully, never raise or leak the path.
    result = to_data_relative_url(
        "/some/other/place/file.mp4", data_dir="/home/user/ai-life-movie/data"
    )
    assert result == ""

    result_win = to_data_relative_url(
        r"C:\Other\Place\file.mp4", data_dir=r"C:\Users\me\app\data"
    )
    assert result_win == ""


def test_url_encodes_special_characters_in_path_segments():
    data_dir = "/home/user/ai-life-movie/data"
    file_path = "/home/user/ai-life-movie/data/projects/my project/final/my movie.mp4"
    url = to_data_relative_url(file_path, data_dir=data_dir)
    assert url == "/data/projects/my%20project/final/my%20movie.mp4"
    assert " " not in url


def test_pure_path_for_detects_windows_style():
    from pathlib import PureWindowsPath

    win_path = _pure_path_for(r"C:\Users\me\file.txt")
    assert isinstance(win_path, PureWindowsPath)
    assert win_path.parts[0] == "C:\\"

    # Drive-letter + forward slashes also counts as Windows-style.
    win_path2 = _pure_path_for("C:/Users/me/file.txt")
    assert isinstance(win_path2, PureWindowsPath)


def test_pure_path_for_detects_posix_style():
    posix_path = _pure_path_for("/home/user/file.txt")
    assert posix_path.parts == ("/", "home", "user", "file.txt")


def test_media_item_to_dict_exposes_clean_thumbnail_url(db_session):
    from app.database.repositories import MediaRepository, ProjectRepository

    project = ProjectRepository(db_session).create(title="URL Test")
    media_repo = MediaRepository(db_session)

    # Simulate a thumbnail path stored the way the real app stores it: an
    # absolute path under DATA_DIR (built the same way PROJECTS_DIR is).
    from app.utils.config import DATA_DIR

    thumb_path = str(DATA_DIR / "projects" / project.id / "thumbnails" / "abc.jpg")
    item = media_repo.add(
        project_id=project.id,
        media_type="image",
        original_filename="a.jpg",
        storage_path="/tmp/a.jpg",
        thumbnail_path=thumb_path,
    )
    d = item.to_dict()
    assert d["thumbnail_url"] == f"/data/projects/{project.id}/thumbnails/abc.jpg"
    assert "thumbnail_path" in d  # raw path still available for internal/debug use


def test_generated_movie_to_dict_exposes_clean_file_url(db_session):
    from app.database.repositories import MovieRepository, ProjectRepository
    from app.utils.config import DATA_DIR

    project = ProjectRepository(db_session).create(title="Movie URL Test")
    movie_path = str(DATA_DIR / "projects" / project.id / "renders" / "job1" / "final" / "movie.mp4")
    movie = MovieRepository(db_session).create(project_id=project.id, file_path=movie_path)
    d = movie.to_dict()
    assert d["file_url"] == f"/data/projects/{project.id}/renders/job1/final/movie.mp4"
    assert "C:" not in d["file_url"]
