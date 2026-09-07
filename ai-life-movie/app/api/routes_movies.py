"""REST endpoints for story generation, movie job kickoff/progress, and
retrieving generated movies.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.story_generator import generate_story, story_to_narration_script
from app.database.database import get_db
from app.database.repositories import (
    EventRepository,
    JobRepository,
    MovieRepository,
    ProjectRepository,
    StoryRepository,
)
from app.database.models import JobState
from app.workers.jobs import submit_job

router = APIRouter(tags=["movies"])


@router.post("/api/projects/{project_id}/story")
def create_story(project_id: str, db: Session = Depends(get_db)):
    project = ProjectRepository(db).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    events = EventRepository(db).list_for_project(project_id)
    if not events:
        raise HTTPException(status_code=400, detail="No events found — run analysis first.")
    events_data = [e.to_dict() for e in events]
    story_dict = generate_story(events_data, project.style, project.language, project.target_duration_seconds)
    story = StoryRepository(db).create(
        project_id=project_id,
        title=story_dict.get("title", ""),
        opening=story_dict.get("opening", ""),
        ending=story_dict.get("ending", ""),
        tone=story_dict.get("tone", project.style),
        chapters_json=story_dict.get("chapters", []),
        narration_script=story_to_narration_script(story_dict),
        source=story_dict.get("source", "fallback"),
    )
    return story.to_dict()


@router.get("/api/projects/{project_id}/story")
def get_latest_story(project_id: str, db: Session = Depends(get_db)):
    story = StoryRepository(db).latest_for_project(project_id)
    if not story:
        raise HTTPException(status_code=404, detail="No story generated yet")
    return story.to_dict()


@router.post("/api/projects/{project_id}/movie", status_code=202)
def start_movie_generation(project_id: str, db: Session = Depends(get_db)):
    project = ProjectRepository(db).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    job = JobRepository(db).create(project_id=project_id)
    ProjectRepository(db).update(project, status="processing")
    submit_job(job.id, project_id)
    return {"job_id": job.id, "state": JobState.QUEUED.value}


@router.get("/api/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = JobRepository(db).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.get("/api/movies/{movie_id}")
def get_movie(movie_id: str, db: Session = Depends(get_db)):
    movie = MovieRepository(db).get(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie.to_dict()


@router.get("/api/movies")
def list_recent_movies(db: Session = Depends(get_db)):
    movies = MovieRepository(db).list_recent(20)
    return [m.to_dict() for m in movies]
