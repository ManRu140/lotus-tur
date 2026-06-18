"""Media (image) upload management for the admin panel.

Security model for uploads — the riskiest kind of admin feature:
  1. Only a fixed allow-list of image extensions/MIME types is accepted.
  2. The first bytes of the file are checked against known magic numbers
     for that type, so a renamed .exe can't masquerade as a .png.
  3. Files are stored under a randomly generated name — the user's
     original filename is *never* used as a path component, which is
     what rules out path traversal ("../../app/main.py") and silent
     overwrites of another file.
  4. Size is capped (default 5 MB) before the body is even fully read,
     to bound memory/disk usage.
  5. Served back as static files by extension only (StaticFiles), so the
     browser always gets the Content-Type we intended, never one an
     attacker could use to get a payload interpreted as HTML/JS.

Operational note: on Railway (and most container hosts) the local
filesystem is ephemeral — files written here will NOT survive a
redeploy/restart unless this directory is mounted on a persistent
Railway Volume. For real production use, swap `_save_to_disk()` below
for an S3-compatible client (e.g. Cloudflare R2 / AWS S3); the rest of
this module (validation, DB bookkeeping, routes) stays the same.
"""

import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin, require_staff
from app.db.session import get_session
from app.models.media import MediaAsset
from app.models.user import User
from app.services.audit_service import log_admin_action

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

# extension -> (allowed content-types, magic-byte prefixes to verify against)
_ALLOWED_TYPES: dict[str, tuple[set[str], list[bytes]]] = {
    "jpg":  ({"image/jpeg"}, [b"\xff\xd8\xff"]),
    "jpeg": ({"image/jpeg"}, [b"\xff\xd8\xff"]),
    "png":  ({"image/png"}, [b"\x89PNG\r\n\x1a\n"]),
    "gif":  ({"image/gif"}, [b"GIF87a", b"GIF89a"]),
    "webp": ({"image/webp"}, [b"RIFF"]),  # full check also verifies the "WEBP" tag below
}


def _detect_extension(filename: str, content_type: str) -> str:
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if ext not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Разрешены только изображения: jpg, jpeg, png, gif, webp",
        )
    allowed_mimes, _ = _ALLOWED_TYPES[ext]
    if content_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content-Type «{content_type}» не соответствует расширению .{ext}",
        )
    return ext


def _verify_magic_bytes(ext: str, head: bytes) -> None:
    _, signatures = _ALLOWED_TYPES[ext]
    if not any(head.startswith(sig) for sig in signatures):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Содержимое файла не соответствует заявленному формату изображения",
        )
    if ext == "webp" and head[8:12] != b"WEBP":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Повреждённый WEBP-файл")


def _save_to_disk(stored_filename: str, data: bytes) -> None:
    """Persist the validated file bytes. Swap this one function for an
    S3-compatible client call to move storage off the local (ephemeral)
    container filesystem — nothing else in this module needs to change.
    """
    (UPLOAD_DIR / stored_filename).write_bytes(data)


@router.post("", status_code=201, summary="Загрузить изображение")
async def upload_media(
    request: Request,
    file: UploadFile,
    admin: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> dict:
    ext = _detect_extension(file.filename or "", file.content_type or "")

    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл превышает лимит {MAX_UPLOAD_BYTES // (1024 * 1024)} МБ",
        )
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пустой файл")

    _verify_magic_bytes(ext, data[:16])

    stored_filename = f"{secrets.token_hex(16)}.{ext}"
    _save_to_disk(stored_filename, data)

    asset = MediaAsset(
        stored_filename=stored_filename,
        original_filename=(file.filename or "")[:256],
        content_type=file.content_type or "",
        size_bytes=len(data),
        uploaded_by_id=admin.id,
    )
    session.add(asset)
    await session.commit()
    await session.refresh(asset)
    await log_admin_action(
        session, admin, action="media.upload", target_type="media",
        target_id=asset.id, details=asset.original_filename, request=request,
    )
    return {"id": asset.id, "url": asset.url, "original_filename": asset.original_filename}


@router.get("", summary="Список загруженных файлов")
async def list_media(
    _: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    rows = (
        await session.execute(select(MediaAsset).order_by(MediaAsset.created_at.desc()).limit(200))
    ).scalars().all()
    return [
        {
            "id": a.id,
            "url": a.url,
            "original_filename": a.original_filename,
            "size_bytes": a.size_bytes,
            "created_at": a.created_at.isoformat(),
        }
        for a in rows
    ]


@router.delete("/{media_id}", status_code=204, summary="Удалить файл")
async def delete_media(
    media_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    asset = await session.get(MediaAsset, media_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден")

    file_path = UPLOAD_DIR / asset.stored_filename
    # Best-effort disk cleanup — DB row is the source of truth either way.
    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass

    name = asset.original_filename
    await session.delete(asset)
    await session.commit()
    await log_admin_action(
        session, admin, action="media.delete", target_type="media",
        target_id=media_id, details=name, request=request,
    )
