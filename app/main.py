"""FastAPI application entrypoint for AI Life Movie."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api import (
    routes_analysis,
    routes_media,
    routes_movies,
    routes_projects,
    routes_settings,
)
from app.database.database import get_db, init_db
from app.database.repositories import MovieRepository, ProjectRepository
from app.i18n.translations import all_strings, dir_for
from app.utils.config import (
    BASE_DIR,
    DATA_DIR,
    ensure_data_dirs,
    ffmpeg_available,
    ffprobe_available,
    get_settings,
)
from app.utils.logging import get_logger, setup_logging
from fastapi import Depends

settings = get_settings()
setup_logging(settings.log_level)
log = get_logger(__name__)

app = FastAPI(title=settings.app_name)

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


@app.on_event("startup")
def on_startup() -> None:
    ensure_data_dirs()
    init_db()
    if not ffmpeg_available() or not ffprobe_available():
        log.error(
            "FFmpeg/ffprobe not found on PATH. Video processing and rendering will fail. "
            "Install it: https://ffmpeg.org/download.html (e.g. `apt install ffmpeg` on Debian/Ubuntu)."
        )
    if settings.effective_demo_mode:
        log.info("Running in DEMO MODE (no Gemini API key configured) — using intelligent local fallbacks.")


# Static assets (CSS/JS) for the app itself
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
# Read-only access to generated data (thumbnails, rendered movies, previews)
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

app.include_router(routes_projects.router)
app.include_router(routes_media.router)
app.include_router(routes_analysis.router)
app.include_router(routes_movies.router)
app.include_router(routes_settings.router)


def _ctx(request: Request, lang: str = "en", **extra) -> dict:
    return {
        "request": request,
        "strings": all_strings(lang),
        "lang": lang,
        "dir": dir_for(lang),
        "demo_mode": settings.effective_demo_mode,
        **extra,
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, lang: str = "en", db: Session = Depends(get_db)):
    projects = ProjectRepository(db).list_all()
    movies = MovieRepository(db).list_recent(6)
    total_media = sum(p.to_dict()["media_count"] for p in projects)
    return templates.TemplateResponse(
        "dashboard.html",
        _ctx(
            request, lang,
            projects=[p.to_dict() for p in projects],
            movies=[m.to_dict() for m in movies],
            total_media=total_media,
        ),
    )


@app.get("/project/{project_id}", response_class=HTMLResponse)
def project_page(request: Request, project_id: str, lang: str = "en", db: Session = Depends(get_db)):
    project = ProjectRepository(db).get(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    return templates.TemplateResponse("project.html", _ctx(request, lang, project=project.to_dict()))


@app.get("/project/{project_id}/analysis", response_class=HTMLResponse)
def analysis_page(request: Request, project_id: str, lang: str = "en", db: Session = Depends(get_db)):
    project = ProjectRepository(db).get(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    return templates.TemplateResponse("analysis.html", _ctx(request, lang, project=project.to_dict()))


@app.get("/movie/{project_id}", response_class=HTMLResponse)
def movie_page(request: Request, project_id: str, lang: str = "en", db: Session = Depends(get_db)):
    project = ProjectRepository(db).get(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    movies = [m for m in MovieRepository(db).list_recent(50) if m.project_id == project_id]
    latest = movies[0].to_dict() if movies else None
    return templates.TemplateResponse("movie.html", _ctx(request, lang, project=project.to_dict(), movie=latest))


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, lang: str = "en"):
    return templates.TemplateResponse("settings.html", _ctx(request, lang))


@app.exception_handler(Exception)
async def human_readable_error_handler(request: Request, exc: Exception):
    log.error("Unhandled error on %s: %s", request.url.path, exc, exc_info=True)
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})
    return HTMLResponse("<h1>Something went wrong</h1><p>Please try again.</p>", status_code=500)
