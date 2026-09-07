"""Background job execution for movie generation.

Runs in a simple in-process thread pool (no external broker needed — this is
a personal, single-user desktop-style app, not a multi-tenant SaaS). Job
progress/state is persisted to the database so the UI can poll it.
"""
from __future__ import annotations

import datetime as dt
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.ai.media_analyzer import analyze_image, analyze_video
from app.ai.story_generator import generate_story, story_to_narration_script
from app.database.database import session_scope
from app.database.models import JobState, MediaType
from app.database.repositories import (
    EventRepository,
    JobRepository,
    MediaRepository,
    MovieRepository,
    ProjectRepository,
    StoryRepository,
)
from app.media.duplicate_detector import mark_duplicates
from app.movie.movie_builder import build_movie
from app.movie.timeline_builder import MediaForGrouping, group_into_events
from app.utils.config import PROJECTS_DIR
from app.utils.logging import get_logger

log = get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


def submit_job(job_id: str, project_id: str) -> None:
    _executor.submit(_run_job, job_id, project_id)


def _update(job_id: str, state: str, progress: int, message: str) -> None:
    with session_scope() as db:
        repo = JobRepository(db)
        job = repo.get(job_id)
        if job:
            repo.update(job, state=state, progress=progress, message=message)
    log.info("[job %s] %s (%d%%) - %s", job_id, state, progress, message)


def _fail(job_id: str, human_message: str, technical_error: str) -> None:
    log.error("[job %s] FAILED: %s", job_id, technical_error)
    with session_scope() as db:
        repo = JobRepository(db)
        job = repo.get(job_id)
        if job:
            repo.update(job, state=JobState.FAILED.value, progress=100, message=human_message, error=technical_error)


def analyze_project_media(project_id: str) -> None:
    """Run (or re-run) analysis for every media item in a project. Can be
    called directly by the /analyze endpoint (synchronously for small
    batches) or as part of the full movie-generation job.
    """
    project_dir = PROJECTS_DIR / project_id
    thumbs_dir = project_dir / "thumbnails"
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    with session_scope() as db:
        media_repo = MediaRepository(db)
        items = media_repo.list_for_project(project_id)
        analyzed = []
        for item in items:
            src = Path(item.storage_path)
            if not src.exists():
                continue
            thumb_dst = thumbs_dir / f"{item.id}.jpg"
            try:
                if item.media_type == MediaType.IMAGE.value:
                    result = analyze_image(src, thumb_dst)
                else:
                    result = analyze_video(src, thumb_dst)
            except Exception as exc:
                log.warning("Analysis failed for media %s: %s", item.id, exc)
                continue

            media_repo.update(
                item,
                width=result.width,
                height=result.height,
                duration_seconds=result.duration_seconds,
                fps=result.fps,
                codec=result.codec,
                has_audio=result.has_audio,
                captured_at=result.captured_at,
                thumbnail_path=result.thumbnail_path,
                quality_score=result.quality_score,
                blur_score=result.blur_score,
                brightness_score=result.brightness_score,
                phash=result.phash,
                has_people=result.has_people,
                face_count=result.face_count,
                scene_label=result.scene_label,
                tags=result.tags,
                selected_start=result.selected_start,
                selected_end=result.selected_end,
                analysis_json=result.raw,
            )
            analyzed.append(item)

        # Duplicate detection across the whole project (images only — phash is image-specific)
        dupe_input = [
            {
                "id": m.id,
                "phash": m.phash,
                "quality_score": m.quality_score,
                "captured_at_ts": m.captured_at.timestamp() if m.captured_at else None,
            }
            for m in analyzed
            if m.media_type == MediaType.IMAGE.value
        ]
        duplicate_map = mark_duplicates(dupe_input)
        for m in analyzed:
            if m.id in duplicate_map:
                media_repo.update(m, is_duplicate=True, duplicate_of=duplicate_map[m.id])

        # Build events from freshly analyzed media
        grouping_input = [
            MediaForGrouping(
                id=m.id, captured_at=m.captured_at, scene_label=m.scene_label or "unknown",
                phash=m.phash, media_type=m.media_type, has_people=m.has_people, tags=m.tags or [],
            )
            for m in media_repo.list_for_project(project_id)
        ]
        events_data = group_into_events(grouping_input)
        EventRepository(db).replace_for_project(project_id, events_data)


def _select_media_for_movie(items, target_duration_seconds: int) -> list:
    """Pick the best non-duplicate items, capped to a sensible count for the
    target movie length, ordered chronologically.
    """
    candidates = [m for m in items if not m.is_duplicate]
    candidates.sort(key=lambda m: (m.captured_at or dt.datetime.min))

    # Rough budget: ~1 item per 3.5 seconds of target runtime, minimum 4.
    max_items = max(4, int(target_duration_seconds / 3.5))
    if len(candidates) > max_items:
        # Keep chronological spread but prefer higher quality: sort by quality
        # within a chronological-bucket sampling to preserve story order.
        bucket_size = len(candidates) / max_items
        selected = []
        for i in range(max_items):
            lo = int(i * bucket_size)
            hi = int((i + 1) * bucket_size) or (lo + 1)
            bucket = candidates[lo:hi] or candidates[lo : lo + 1]
            best = max(bucket, key=lambda m: m.quality_score)
            selected.append(best)
        candidates = selected
    return candidates


def _run_job(job_id: str, project_id: str) -> None:
    try:
        _update(job_id, JobState.ANALYZING.value, 5, "Analyzing media")
        analyze_project_media(project_id)

        with session_scope() as db:
            project = ProjectRepository(db).get(project_id)
            if not project:
                _fail(job_id, "Project not found.", "project missing at job start")
                return
            style = project.style
            aspect_ratio = project.aspect_ratio
            target_duration = project.target_duration_seconds
            narration_enabled = project.narration_enabled
            subtitles_enabled = project.subtitles_enabled
            music_track = project.music_track
            language = project.language

            _update(job_id, JobState.SELECTING.value, 25, "Selecting best moments")
            all_media = MediaRepository(db).list_for_project(project_id)
            selected = _select_media_for_movie(all_media, target_duration)
            if not selected:
                _fail(job_id, "No usable photos or videos were found to build a movie.", "empty selection")
                return

            for m in all_media:
                MediaRepository(db).update(m, selected_for_movie=(m in selected))
            for idx, m in enumerate(selected):
                MediaRepository(db).update(m, order_index=idx)

            events = EventRepository(db).list_for_project(project_id)
            events_data = [e.to_dict() | {"id": e.id} for e in events]

            _update(job_id, JobState.STORY_GENERATION.value, 40, "Writing the story")
            story_dict = generate_story(events_data, style, language, target_duration)
            story_repo = StoryRepository(db)
            story = story_repo.create(
                project_id=project_id,
                title=story_dict.get("title", ""),
                opening=story_dict.get("opening", ""),
                ending=story_dict.get("ending", ""),
                tone=story_dict.get("tone", style),
                chapters_json=story_dict.get("chapters", []),
                narration_script=story_to_narration_script(story_dict),
                source=story_dict.get("source", "fallback"),
            )

            items_data = [
                {
                    "id": m.id,
                    "media_type": m.media_type,
                    "storage_path": m.storage_path,
                    "selected_start": m.selected_start,
                    "selected_end": m.selected_end,
                    "event_id": m.event_id,
                }
                for m in selected
            ]

        _update(job_id, JobState.BUILDING_TIMELINE.value, 50, "Building timeline")
        # (Timeline itself is a UI concern built on-demand from stored media; nothing to persist here.)

        _update(job_id, JobState.RENDERING.value, 55, "Rendering movie")
        work_dir = PROJECTS_DIR / project_id / "renders" / job_id

        def progress_cb(msg: str, pct: int) -> None:
            # Map the builder's internal 0-100 progress onto the RENDERING phase's 55-95 band.
            mapped = 55 + int((pct / 100) * 40)
            _update(job_id, JobState.RENDERING.value, min(95, mapped), msg)

        result = build_movie(
            project_id=project_id,
            items=items_data,
            story=story_dict,
            style=style,
            aspect_ratio=aspect_ratio,
            target_duration_seconds=target_duration,
            narration_enabled=narration_enabled,
            subtitles_enabled=subtitles_enabled,
            music_track=music_track,
            language=language,
            work_dir=work_dir,
            events=events_data,
            progress_cb=progress_cb,
        )

        _update(job_id, JobState.FINALIZING.value, 97, "Finalizing")
        with session_scope() as db:
            movie_repo = MovieRepository(db)
            movie = movie_repo.create(
                project_id=project_id,
                file_path=str(result.output_path),
                thumbnail_path=str(result.thumbnail_path),
                duration_seconds=result.duration_seconds,
                resolution=result.resolution,
                style=style,
                subtitle_path=str(result.subtitle_path) if result.subtitle_path else "",
            )
            project = ProjectRepository(db).get(project_id)
            if project:
                ProjectRepository(db).update(project, status="ready")
            job_repo = JobRepository(db)
            job = job_repo.get(job_id)
            if job:
                job_repo.update(
                    job, state=JobState.COMPLETED.value, progress=100,
                    message="Your movie is ready!", result_movie_id=movie.id,
                )
    except Exception as exc:
        _fail(job_id, "Movie generation failed. Please check the logs and try again.", f"{exc}\n{traceback.format_exc()}")
