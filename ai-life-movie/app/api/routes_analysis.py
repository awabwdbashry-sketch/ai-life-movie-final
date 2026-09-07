"""REST endpoints for triggering analysis and retrieving the timeline/events."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.repositories import EventRepository, MediaRepository, ProjectRepository
from app.movie.timeline_builder import build_visual_timeline
from app.workers.jobs import analyze_project_media

router = APIRouter(prefix="/api/projects", tags=["analysis"])


@router.post("/{project_id}/analyze")
def analyze_project(project_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    project = ProjectRepository(db).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # For small personal libraries this completes quickly enough to run inline
    # and return results immediately, which keeps the UI simple (no extra
    # polling step just for analysis, as opposed to full movie rendering).
    analyze_project_media(project_id)
    items = MediaRepository(db).list_for_project(project_id)
    events = EventRepository(db).list_for_project(project_id)
    return {
        "media": [m.to_dict() for m in items],
        "events": [e.to_dict() for e in events],
    }


@router.get("/{project_id}/timeline")
def get_timeline(project_id: str, db: Session = Depends(get_db)):
    project = ProjectRepository(db).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    items = MediaRepository(db).list_for_project(project_id)
    timeline = build_visual_timeline([m.to_dict() | {"captured_at": m.captured_at} for m in items])
    events = EventRepository(db).list_for_project(project_id)
    return {
        "timeline": [
            {**t, "time": t["time"].isoformat() if t["time"] else None} for t in timeline
        ],
        "events": [e.to_dict() for e in events],
    }
