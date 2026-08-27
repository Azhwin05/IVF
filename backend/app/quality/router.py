from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.quality import service
from app.quality.schemas import QATaskInstanceOut, QATemplateCreate
from app.users.models import User

router = APIRouter(prefix="/quality", tags=["quality"])


@router.post("/templates", status_code=201)
async def create_template(
    body: QATemplateCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("quality.read")),
) -> dict:
    template = await service.create_template(session, body)
    return {"id": str(template.id)}


@router.get("/instances", response_model=list[QATaskInstanceOut])
async def list_open(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("quality.read")),
) -> list[QATaskInstanceOut]:
    return await service.list_open_instances(session)


@router.post("/instances/{instance_id}/complete", response_model=QATaskInstanceOut)
async def complete(
    instance_id: str,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("quality.complete")),
) -> QATaskInstanceOut:
    return await service.complete_instance(session, instance_id, actor_id=current.id, actor_role=current.role.code)
