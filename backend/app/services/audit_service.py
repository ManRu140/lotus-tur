from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AdminAuditLog
from app.models.user import User


async def log_admin_action(
    session: AsyncSession,
    admin: User,
    *,
    action: str,
    target_type: str,
    target_id: str,
    details: Optional[str] = None,
    request: Optional[Request] = None,
) -> AdminAuditLog:
    """Append one audit log entry and flush it in the *same* transaction
    as the action it describes.

    Important: this does NOT call `session.commit()` itself. It is always
    called right after the caller's own `await session.commit()`, using
    a fresh `session.add()` + `session.commit()` of its own — logging
    failures must never roll back the action being logged, and the
    action being logged must never be lost if logging fails. Keeping the
    two commits separate (action first, log second) gives us that
    ordering without coupling the two.
    """
    ip_address = None
    if request is not None:
        # Respect a reverse proxy's forwarded header (Railway sits behind
        # one), falling back to the direct client address.
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        elif request.client:
            ip_address = request.client.host

    entry = AdminAuditLog(
        admin_id=admin.id,
        admin_username=admin.username,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        details=details,
        ip_address=ip_address,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry
