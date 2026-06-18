from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.db.session import get_session
from app.models.audit_log import AdminAuditLog
from app.models.user import User

router = APIRouter()


class AuditLogOut(BaseModel):
    id: int
    admin_username: str
    action: str
    target_type: str
    target_id: str
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/logs", response_model=list[AuditLogOut], summary="Журнал действий администраторов")
async def list_audit_logs(
    admin_username: Optional[str] = Query(None),
    action: Optional[str] = Query(None, description="Точное совпадение либо префикс, напр. 'tour.'"),
    target_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    # Full admin only — moderators can act, but only admins audit them.
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[AuditLogOut]:
    q = select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc())
    if admin_username:
        q = q.where(AdminAuditLog.admin_username.ilike(f"%{admin_username}%"))
    if action:
        q = q.where(AdminAuditLog.action.like(f"{action}%"))
    if target_type:
        q = q.where(AdminAuditLog.target_type == target_type)
    q = q.limit(limit).offset(offset)

    rows = (await session.execute(q)).scalars().all()
    return list(rows)
