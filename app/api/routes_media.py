"""REST endpoints for media upload and management, with strict validation:
extension + MIME allow-list, size limits, sanitized/random storage filenames,
and path-traversal protection.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.repositories import MediaRepository, ProjectRepository
from app.utils.config import PROJECTS_DIR, get_settings
from app.utils.files import (
    UnsupportedFileError,
    generate_storage_name,
    human_size,
    is_image_ext,
    sanitize_filename,
    validate_extension,
)
from app.utils.logging import get_logger

router = APIRouter(tags=["media"])
log = get_logger(__name__)


@router.post("/api/projects/{project_id}/media", status_code=201)
async def upload_media(project_id: str, files: list[UploadFile], db: Session = Depends(get_db)):
    project = ProjectRepository(db).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    media_repo = MediaRepository(db)

    originals_dir = PROJECTS_DIR / project_id / "originals"
    originals_dir.mkdir(parents=True, exist_ok=True)

    created = []
    errors = []

    for upload in files:
        safe_name = sanitize_filename(upload.filename or "file")
        try:
            ext = validate_extension(safe_name)
        except UnsupportedFileError as exc:
            errors.append({"filename": upload.filename, "error": str(exc)})
            continue

        if upload.content_type and not (
            upload.content_type.startswith("image/") or upload.content_type.startswith("video/")
        ):
            errors.append({"filename": upload.filename, "error": "Unsupported content type."})
            continue

        storage_name = generate_storage_name(ext)
        dst_path = originals_dir / storage_name

        size = 0
        try:
            with open(dst_path, "wb") as f:
                while chunk := await upload.read(1024 * 1024):
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError(f"File exceeds max upload size of {settings.max_upload_mb}MB")
                    f.write(chunk)
        except Exception as exc:
            if dst_path.exists():
                dst_path.unlink(missing_ok=True)
            errors.append({"filename": upload.filename, "error": str(exc)})
            continue

        media_type = "image" if is_image_ext(ext) else "video"
        item = media_repo.add(
            project_id=project_id,
            media_type=media_type,
            original_filename=safe_name,
            storage_path=str(dst_path),
            file_size=size,
            mime_type=upload.content_type or "",
        )
        created.append(item.to_dict() | {"file_size_human": human_size(size)})

    return {"created": created, "errors": errors}


@router.get("/api/projects/{project_id}/media")
def list_media(project_id: str, db: Session = Depends(get_db)):
    items = MediaRepository(db).list_for_project(project_id)
    return [m.to_dict() for m in items]


@router.delete("/api/media/{media_id}", status_code=204)
def delete_media(media_id: str, db: Session = Depends(get_db)):
    repo = MediaRepository(db)
    item = repo.get(media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media not found")
    # Remove the original file too (uploads are otherwise treated as immutable,
    # but explicit user-requested deletion is respected).
    try:
        Path(item.storage_path).unlink(missing_ok=True)
        if item.thumbnail_path:
            Path(item.thumbnail_path).unlink(missing_ok=True)
    except Exception as exc:
        log.warning("Could not remove files for media %s: %s", media_id, exc)
    repo.delete(media_id)
    return None
