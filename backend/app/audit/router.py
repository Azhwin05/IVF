from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditEvent
from app.audit.schemas import AuditEventOut
from app.core.database import get_db
from app.core.deps import require_permission
from app.users.models import User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditEventOut])
async def list_audit_events(
    q: str | None = Query(default=None, description="Free-text match against action or entity_type"),
    limit: int = Query(default=200, le=1000),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("audit.read")),
) -> list[AuditEventOut]:
    stmt = select(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(limit)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(AuditEvent.action.ilike(pattern), AuditEvent.entity_type.ilike(pattern)))
    result = await session.execute(stmt)
    return list(result.scalars().all())
