"""API endpoint tests. Uses a temporary SQLite file (not the real app database)
via dependency override, and a temp directory for uploads.
"""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    from app.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Redirect project storage to a temp dir so tests never touch real data/
    import app.api.routes_media as routes_media

    monkeypatch.setattr(routes_media, "PROJECTS_DIR", tmp_path)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_create_and_list_projects(client):
    res = client.post("/api/projects", json={"title": "API Test Project"})
    assert res.status_code == 201
    project = res.json()
    assert project["title"] == "API Test Project"

    res = client.get("/api/projects")
    assert res.status_code == 200
    assert any(p["id"] == project["id"] for p in res.json())


def test_get_nonexistent_project_returns_404(client):
    res = client.get("/api/projects/does-not-exist")
    assert res.status_code == 404


def test_update_project(client):
    project = client.post("/api/projects", json={"title": "Original"}).json()
    res = client.patch(f"/api/projects/{project['id']}", json={"title": "Updated", "style": "minimal"})
    assert res.status_code == 200
    assert res.json()["title"] == "Updated"
    assert res.json()["style"] == "minimal"


def test_delete_project(client):
    project = client.post("/api/projects", json={"title": "To Delete"}).json()
    res = client.delete(f"/api/projects/{project['id']}")
    assert res.status_code == 204
    assert client.get(f"/api/projects/{project['id']}").status_code == 404


def test_upload_media_rejects_unsupported_extension(client):
    project = client.post("/api/projects", json={"title": "Upload Test"}).json()
    fake_file = io.BytesIO(b"not a real file")
    res = client.post(
        f"/api/projects/{project['id']}/media",
        files={"files": ("malware.exe", fake_file, "application/octet-stream")},
    )
    assert res.status_code == 201  # request succeeds, but the file itself is rejected
    body = res.json()
    assert len(body["created"]) == 0
    assert len(body["errors"]) == 1


def test_upload_media_accepts_valid_image(client, tmp_path):
    project = client.post("/api/projects", json={"title": "Upload Test 2"}).json()
    # Build a tiny valid JPEG
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="red").save(buf, "JPEG")
    buf.seek(0)
    res = client.post(
        f"/api/projects/{project['id']}/media",
        files={"files": ("photo.jpg", buf, "image/jpeg")},
    )
    assert res.status_code == 201
    body = res.json()
    assert len(body["created"]) == 1
    assert body["errors"] == []


def test_settings_endpoint_returns_expected_shape(client):
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert "gemini_configured" in data
    assert "demo_mode" in data
    assert "music_tracks" in data


def test_job_not_found_returns_404(client):
    res = client.get("/api/jobs/nonexistent-job-id")
    assert res.status_code == 404


def test_analyze_requires_existing_project(client):
    res = client.post("/api/projects/does-not-exist/analyze")
    assert res.status_code == 404


def test_dashboard_page_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
