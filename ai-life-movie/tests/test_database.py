"""Tests for the repository / data-access layer."""
from __future__ import annotations

from app.database.repositories import (
    EventRepository,
    JobRepository,
    MediaRepository,
    MovieRepository,
    ProjectRepository,
    SettingsRepository,
)


def test_create_and_get_project(db_session):
    repo = ProjectRepository(db_session)
    project = repo.create(title="My Trip", style="travel")
    assert project.id
    fetched = repo.get(project.id)
    assert fetched.title == "My Trip"
    assert fetched.style == "travel"


def test_project_to_dict_counts_media(db_session):
    project_repo = ProjectRepository(db_session)
    media_repo = MediaRepository(db_session)
    project = project_repo.create(title="Counts Test")
    media_repo.add(project_id=project.id, media_type="image", original_filename="a.jpg", storage_path="/tmp/a.jpg")
    media_repo.add(project_id=project.id, media_type="video", original_filename="b.mp4", storage_path="/tmp/b.mp4")
    db_session.refresh(project)
    d = project.to_dict()
    assert d["media_count"] == 2
    assert d["photo_count"] == 1
    assert d["video_count"] == 1


def test_delete_project_cascades_media(db_session):
    project_repo = ProjectRepository(db_session)
    media_repo = MediaRepository(db_session)
    project = project_repo.create(title="To Delete")
    media_repo.add(project_id=project.id, media_type="image", original_filename="a.jpg", storage_path="/tmp/a.jpg")
    assert project_repo.delete(project.id) is True
    assert project_repo.get(project.id) is None


def test_event_replace_for_project(db_session):
    project_repo = ProjectRepository(db_session)
    media_repo = MediaRepository(db_session)
    project = project_repo.create(title="Events Test")
    m1 = media_repo.add(project_id=project.id, media_type="image", original_filename="a.jpg", storage_path="/tmp/a.jpg")
    m2 = media_repo.add(project_id=project.id, media_type="image", original_filename="b.jpg", storage_path="/tmp/b.jpg")

    event_repo = EventRepository(db_session)
    events = event_repo.replace_for_project(
        project.id,
        [
            {"label": "Beach", "order_index": 0, "media_ids": [m1.id, m2.id], "media_count": 2},
        ],
    )
    assert len(events) == 1
    assert events[0].label == "Beach"

    db_session.refresh(m1)
    assert m1.event_id == events[0].id


def test_job_lifecycle(db_session):
    project_repo = ProjectRepository(db_session)
    job_repo = JobRepository(db_session)
    project = project_repo.create(title="Job Test")
    job = job_repo.create(project_id=project.id)
    assert job.state == "QUEUED"
    job_repo.update(job, state="RENDERING", progress=50, message="Rendering movie")
    fetched = job_repo.get(job.id)
    assert fetched.state == "RENDERING"
    assert fetched.progress == 50


def test_settings_repository_roundtrip(db_session):
    repo = SettingsRepository(db_session)
    assert repo.get("default_language", "en") == "en"
    repo.set("default_language", "ar")
    assert repo.get("default_language") == "ar"


def test_movie_repository(db_session):
    project_repo = ProjectRepository(db_session)
    movie_repo = MovieRepository(db_session)
    project = project_repo.create(title="Movie Test")
    movie = movie_repo.create(project_id=project.id, file_path="/tmp/out.mp4", duration_seconds=42.0)
    fetched = movie_repo.get(movie.id)
    assert fetched.duration_seconds == 42.0
    recent = movie_repo.list_recent(10)
    assert any(m.id == movie.id for m in recent)
