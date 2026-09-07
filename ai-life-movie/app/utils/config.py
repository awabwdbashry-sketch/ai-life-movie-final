"""Central application configuration, loaded from environment variables (.env)."""
from __future__ import annotations

import os
import shutil
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
PREVIEWS_DIR = DATA_DIR / "previews"
MOVIES_DIR = DATA_DIR / "movies"
CACHE_DIR = DATA_DIR / "cache"
PROJECTS_DIR = DATA_DIR / "projects"
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"


class Settings(BaseSettings):
    """Application settings. Values come from environment / .env file."""

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    app_name: str = "AI Life Movie"
    gemini_api_key: str = ""
    demo_mode: bool = False
    default_language: str = "en"
    default_movie_style: str = "cinematic"
    default_aspect_ratio: str = "16:9"
    default_quality: str = "high"
    narration_enabled_default: bool = True
    max_upload_mb: int = 500
    log_level: str = "INFO"
    secret_key: str = "dev-secret-change-me"

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.strip())

    @property
    def effective_demo_mode(self) -> bool:
        """Demo mode is forced on if no Gemini key is configured."""
        return self.demo_mode or not self.gemini_configured


@lru_cache
def get_settings() -> Settings:
    return Settings()


def ensure_data_dirs() -> None:
    for d in (UPLOADS_DIR, PROCESSED_DIR, PREVIEWS_DIR, MOVIES_DIR, CACHE_DIR, PROJECTS_DIR, MUSIC_DIR):
        d.mkdir(parents=True, exist_ok=True)


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def ffprobe_available() -> bool:
    return shutil.which("ffprobe") is not None


ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
ALLOWED_EXT = ALLOWED_IMAGE_EXT | ALLOWED_VIDEO_EXT

ALLOWED_MIME_PREFIXES = ("image/", "video/")
