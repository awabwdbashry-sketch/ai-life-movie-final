"""ORM models: projects, media, events, stories, jobs, movies, settings."""
from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.utils.files import to_data_relative_url


def _uid() -> str:
    return uuid.uuid4().hex


def _now() -> dt.datetime:
    return dt.datetime.utcnow()


class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class JobState(str, enum.Enum):
    QUEUED = "QUEUED"
    ANALYZING = "ANALYZING"
    SELECTING = "SELECTING"
    STORY_GENERATION = "STORY_GENERATION"
    GENERATING_NARRATION = "GENERATING_NARRATION"
    BUILDING_TIMELINE = "BUILDING_TIMELINE"
    RENDERING = "RENDERING"
    FINALIZING = "FINALIZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uid)
    title: Mapped[str] = mapped_column(String, default="Untitled Movie")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    style: Mapped[str] = mapped_column(String, default="cinematic")
    aspect_ratio: Mapped[str] = mapped_column(String, default="16:9")
    target_duration_seconds: Mapped[int] = mapped_column(Integer, default=60)
    language: Mapped[str] = mapped_column(String, default="en")
    narration_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    subtitles_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    music_track: Mapped[str] = mapped_column(String, default="warm_memories")
    status: Mapped[str] = mapped_column(String, default="draft")  # draft, processing, ready

    media_items: Mapped[list["MediaItem"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    events: Mapped[list["Event"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    stories: Mapped[list["Story"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["MovieJob"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    movies: Mapped[list["GeneratedMovie"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "style": self.style,
            "aspect_ratio": self.aspect_ratio,
            "target_duration_seconds": self.target_duration_seconds,
            "language": self.language,
            "narration_enabled": self.narration_enabled,
            "subtitles_enabled": self.subtitles_enabled,
            "music_track": self.music_track,
            "status": self.status,
            "media_count": len(self.media_items),
            "photo_count": sum(1 for m in self.media_items if m.media_type == MediaType.IMAGE.value),
            "video_count": sum(1 for m in self.media_items if m.media_type == MediaType.VIDEO.value),
        }


class MediaItem(Base):
    __tablename__ = "media_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    project: Mapped["Project"] = relationship(back_populates="media_items")

    media_type: Mapped[str] = mapped_column(String)  # image | video
    original_filename: Mapped[str] = mapped_column(String)
    storage_path: Mapped[str] = mapped_column(String)
    thumbnail_path: Mapped[str] = mapped_column(String, default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[str] = mapped_column(String, default="")

    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    fps: Mapped[float] = mapped_column(Float, default=0.0)
    codec: Mapped[str] = mapped_column(String, default="")
    has_audio: Mapped[bool] = mapped_column(Boolean, default=False)

    captured_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    # Analysis results
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    blur_score: Mapped[float] = mapped_column(Float, default=0.0)
    brightness_score: Mapped[float] = mapped_column(Float, default=0.0)
    phash: Mapped[str] = mapped_column(String, default="")
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of: Mapped[str] = mapped_column(String, default="")
    has_people: Mapped[bool] = mapped_column(Boolean, default=False)
    face_count: Mapped[int] = mapped_column(Integer, default=0)
    scene_label: Mapped[str] = mapped_column(String, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    analysis_json: Mapped[dict] = mapped_column(JSON, default=dict)

    # Video clip selection (best sub-segment)
    selected_start: Mapped[float] = mapped_column(Float, default=0.0)
    selected_end: Mapped[float] = mapped_column(Float, default=0.0)

    event_id: Mapped[str | None] = mapped_column(ForeignKey("events.id"), nullable=True)
    event: Mapped["Event | None"] = relationship(back_populates="media_items")

    selected_for_movie: Mapped[bool] = mapped_column(Boolean, default=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "media_type": self.media_type,
            "original_filename": self.original_filename,
            "thumbnail_path": self.thumbnail_path,
            "thumbnail_url": to_data_relative_url(self.thumbnail_path),
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration_seconds,
            "fps": self.fps,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "quality_score": round(self.quality_score, 1),
            "blur_score": round(self.blur_score, 1),
            "brightness_score": round(self.brightness_score, 1),
            "is_duplicate": self.is_duplicate,
            "has_people": self.has_people,
            "face_count": self.face_count,
            "scene_label": self.scene_label,
            "tags": self.tags or [],
            "event_id": self.event_id,
            "selected_for_movie": self.selected_for_movie,
            "selected_start": self.selected_start,
            "selected_end": self.selected_end,
            "order_index": self.order_index,
        }


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    project: Mapped["Project"] = relationship(back_populates="events")

    label: Mapped[str] = mapped_column(String, default="Moment")
    start_time: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, default="")

    media_items: Mapped[list["MediaItem"]] = relationship(back_populates="event")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "order_index": self.order_index,
            "summary": self.summary,
            "media_ids": [m.id for m in self.media_items],
        }


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    project: Mapped["Project"] = relationship(back_populates="stories")

    title: Mapped[str] = mapped_column(String, default="")
    opening: Mapped[str] = mapped_column(Text, default="")
    ending: Mapped[str] = mapped_column(Text, default="")
    tone: Mapped[str] = mapped_column(String, default="cinematic")
    chapters_json: Mapped[list] = mapped_column(JSON, default=list)
    narration_script: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String, default="fallback")  # "gemini" | "fallback"
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "opening": self.opening,
            "ending": self.ending,
            "tone": self.tone,
            "chapters": self.chapters_json or [],
            "narration_script": self.narration_script,
            "source": self.source,
        }


class MovieJob(Base):
    __tablename__ = "movie_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    project: Mapped["Project"] = relationship(back_populates="jobs")

    state: Mapped[str] = mapped_column(String, default=JobState.QUEUED.value)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(String, default="Queued")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
    result_movie_id: Mapped[str] = mapped_column(String, default="")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "state": self.state,
            "progress": self.progress,
            "message": self.message,
            "error": self.error,
            "result_movie_id": self.result_movie_id,
            "updated_at": self.updated_at.isoformat(),
        }


class GeneratedMovie(Base):
    __tablename__ = "generated_movies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    project: Mapped["Project"] = relationship(back_populates="movies")

    file_path: Mapped[str] = mapped_column(String, default="")
    thumbnail_path: Mapped[str] = mapped_column(String, default="")
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    resolution: Mapped[str] = mapped_column(String, default="")
    style: Mapped[str] = mapped_column(String, default="")
    subtitle_path: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "file_path": self.file_path,
            "file_url": to_data_relative_url(self.file_path),
            "thumbnail_path": self.thumbnail_path,
            "thumbnail_url": to_data_relative_url(self.thumbnail_path),
            "duration_seconds": self.duration_seconds,
            "resolution": self.resolution,
            "style": self.style,
            "subtitle_path": self.subtitle_path,
            "subtitle_url": to_data_relative_url(self.subtitle_path),
            "created_at": self.created_at.isoformat(),
        }


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
