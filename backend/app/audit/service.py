"""
The single function every other module calls to record an audit event.
Deliberately synchronous with the caller's transaction (same session,
same commit) so an audited action and its audit record either both
succeed or both roll back together — never a mutation without a trail.
"""
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditEvent
from app.core.logging import request_id_ctx


async def record_audit_event(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID | None,
    actor_role: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    reason: str | None = None,
    source_ip: str | None = None,
    session_id: uuid.UUID | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=before_state,
        after_state=after_state,
        reason=reason,
        request_id=request_id_ctx.get(),
        source_ip=source_ip,
        session_id=session_id,
    )
    session.add(event)
    await session.flush()
    return event
