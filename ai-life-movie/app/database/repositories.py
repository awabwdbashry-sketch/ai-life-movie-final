"""Repository layer: clean data-access functions around SQLAlchemy models."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    AppSetting,
    Event,
    GeneratedMovie,
    MediaItem,
    MovieJob,
    Project,
    Story,
)


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Project:
        project = Project(**kwargs)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get(self, project_id: str) -> Project | None:
        return self.db.get(Project, project_id)

    def list_all(self) -> list[Project]:
        return list(self.db.execute(select(Project).order_by(Project.updated_at.desc())).scalars())

    def delete(self, project_id: str) -> bool:
        project = self.get(project_id)
        if not project:
            return False
        self.db.delete(project)
        self.db.commit()
        return True

    def update(self, project: Project, **kwargs) -> Project:
        for k, v in kwargs.items():
            setattr(project, k, v)
        self.db.commit()
        self.db.refresh(project)
        return project


class MediaRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, **kwargs) -> MediaItem:
        item = MediaItem(**kwargs)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get(self, media_id: str) -> MediaItem | None:
        return self.db.get(MediaItem, media_id)

    def list_for_project(self, project_id: str) -> list[MediaItem]:
        stmt = select(MediaItem).where(MediaItem.project_id == project_id).order_by(MediaItem.captured_at)
        return list(self.db.execute(stmt).scalars())

    def delete(self, media_id: str) -> bool:
        item = self.get(media_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    def update(self, item: MediaItem, **kwargs) -> MediaItem:
        for k, v in kwargs.items():
            setattr(item, k, v)
        self.db.commit()
        self.db.refresh(item)
        return item

    def bulk_commit(self) -> None:
        self.db.commit()


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def replace_for_project(self, project_id: str, events_data: list[dict]) -> list[Event]:
        """Delete existing events for a project and create new ones."""
        existing = list(self.db.execute(select(Event).where(Event.project_id == project_id)).scalars())
        for e in existing:
            for m in list(e.media_items):
                m.event_id = None
            self.db.delete(e)
        self.db.commit()

        allowed_fields = {"label", "start_time", "end_time", "order_index", "summary"}

        created = []
        for data in events_data:
            media_ids = data.get("media_ids", [])
            event_fields = {k: v for k, v in data.items() if k in allowed_fields}
            event = Event(project_id=project_id, **event_fields)
            self.db.add(event)
            self.db.flush()
            for mid in media_ids:
                media = self.db.get(MediaItem, mid)
                if media:
                    media.event_id = event.id
            created.append(event)
        self.db.commit()
        for e in created:
            self.db.refresh(e)
        return created

    def list_for_project(self, project_id: str) -> list[Event]:
        stmt = select(Event).where(Event.project_id == project_id).order_by(Event.order_index)
        return list(self.db.execute(stmt).scalars())


class StoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Story:
        story = Story(**kwargs)
        self.db.add(story)
        self.db.commit()
        self.db.refresh(story)
        return story

    def latest_for_project(self, project_id: str) -> Story | None:
        stmt = (
            select(Story)
            .where(Story.project_id == project_id)
            .order_by(Story.created_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, project_id: str) -> MovieJob:
        job = MovieJob(project_id=project_id)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get(self, job_id: str) -> MovieJob | None:
        return self.db.get(MovieJob, job_id)

    def update(self, job: MovieJob, **kwargs) -> MovieJob:
        for k, v in kwargs.items():
            setattr(job, k, v)
        self.db.commit()
        self.db.refresh(job)
        return job


class MovieRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> GeneratedMovie:
        movie = GeneratedMovie(**kwargs)
        self.db.add(movie)
        self.db.commit()
        self.db.refresh(movie)
        return movie

    def get(self, movie_id: str) -> GeneratedMovie | None:
        return self.db.get(GeneratedMovie, movie_id)

    def list_recent(self, limit: int = 10) -> list[GeneratedMovie]:
        stmt = select(GeneratedMovie).order_by(GeneratedMovie.created_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars())


class SettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str, default: str = "") -> str:
        row = self.db.get(AppSetting, key)
        return row.value if row else default

    def set(self, key: str, value: str) -> None:
        row = self.db.get(AppSetting, key)
        if row:
            row.value = value
        else:
            row = AppSetting(key=key, value=value)
            self.db.add(row)
        self.db.commit()

    def all(self) -> dict:
        return {row.key: row.value for row in self.db.execute(select(AppSetting)).scalars()}
