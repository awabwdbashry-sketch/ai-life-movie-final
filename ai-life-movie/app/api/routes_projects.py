"""REST endpoints for project (movie) management."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.repositories import ProjectRepository

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    title: str = "Untitled Movie"
    style: str = "cinematic"
    aspect_ratio: str = "16:9"
    target_duration_seconds: int = 60
    language: str = "en"
    narration_enabled: bool = True
    subtitles_enabled: bool = False
    music_track: str = "warm_memories"


class ProjectUpdate(BaseModel):
    title: str | None = None
    style: str | None = None
    aspect_ratio: str | None = None
    target_duration_seconds: int | None = None
    language: str | None = None
    narration_enabled: bool | None = None
    subtitles_enabled: bool | None = None
    music_track: str | None = None


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = ProjectRepository(db).list_all()
    return [p.to_dict() for p in projects]


@router.post("", status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = ProjectRepository(db).create(**payload.model_dump())
    return project.to_dict()


@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = ProjectRepository(db).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@router.patch("/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    project = repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    project = repo.update(project, **updates)
    return project.to_dict()


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    if not ProjectRepository(db).delete(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return None
