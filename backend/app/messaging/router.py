from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.messaging import service
from app.messaging.schemas import (
    CommsPreferenceOut,
    CommsPreferenceUpdate,
    MessageLogOut,
    MessageTemplateCreate,
    MessageTemplateOut,
    SendMessageRequest,
)
from app.users.models import User

router = APIRouter(prefix="/messaging", tags=["messaging"])


@router.post("/templates", response_model=MessageTemplateOut, status_code=201)
async def create_template(
    body: MessageTemplateCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("admin.manage_settings")),
) -> MessageTemplateOut:
    return await service.create_template(session, body)


@router.get("/templates", response_model=list[MessageTemplateOut])
async def list_templates(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("messaging.send")),
) -> list[MessageTemplateOut]:
    return await service.list_templates(session)


@router.get("/preferences/{patient_id}", response_model=CommsPreferenceOut)
async def get_comms_preference(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients.read")),
) -> CommsPreferenceOut:
    return await service.get_comms_preference(session, patient_id)


@router.put("/preferences/{patient_id}", response_model=CommsPreferenceOut)
async def update_comms_preference(
    patient_id: str,
    body: CommsPreferenceUpdate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("patients.update")),
) -> CommsPreferenceOut:
    return await service.update_comms_preference(session, patient_id, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/send", response_model=MessageLogOut, status_code=201)
async def send_message(
    body: SendMessageRequest,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("messaging.send")),
) -> MessageLogOut:
    """Promotional messages (category=promotional) are blocked with a
    422 promotional_opt_out unless the patient has opted in — source
    doc §27."""
    return await service.send_message(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/history/{patient_id}", response_model=list[MessageLogOut])
async def list_message_history(
    patient_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("messaging.send")),
) -> list[MessageLogOut]:
    return await service.list_message_history(session, patient_id)
