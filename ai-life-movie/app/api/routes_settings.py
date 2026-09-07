"""REST endpoints for application settings. The raw Gemini API key is never
returned to the client — only a boolean "configured" status.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.repositories import SettingsRepository
from app.movie.music import list_tracks
from app.utils.config import get_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

_EDITABLE_KEYS = {
    "default_language", "default_movie_style", "default_aspect_ratio",
    "default_quality", "narration_enabled_default", "dark_mode",
}


class SettingsUpdate(BaseModel):
    default_language: str | None = None
    default_movie_style: str | None = None
    default_aspect_ratio: str | None = None
    default_quality: str | None = None
    narration_enabled_default: bool | None = None
    dark_mode: bool | None = None


@router.get("")
def get_settings_route(db: Session = Depends(get_db)):
    settings = get_settings()
    repo = SettingsRepository(db)
    stored = repo.all()
    return {
        "gemini_configured": settings.gemini_configured,
        "demo_mode": settings.effective_demo_mode,
        "default_language": stored.get("default_language", settings.default_language),
        "default_movie_style": stored.get("default_movie_style", settings.default_movie_style),
        "default_aspect_ratio": stored.get("default_aspect_ratio", settings.default_aspect_ratio),
        "default_quality": stored.get("default_quality", settings.default_quality),
        "narration_enabled_default": stored.get("narration_enabled_default", str(settings.narration_enabled_default)),
        "dark_mode": stored.get("dark_mode", "true"),
        "music_tracks": list_tracks(),
    }


@router.put("")
def update_settings_route(payload: SettingsUpdate, db: Session = Depends(get_db)):
    repo = SettingsRepository(db)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    for k, v in updates.items():
        repo.set(k, str(v))
    return get_settings_route(db)
