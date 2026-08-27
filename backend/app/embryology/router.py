from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.embryology import service
from app.embryology.schemas import (
    EmbryoCreate,
    EmbryoOut,
    EmbryoStatusUpdate,
    OocyteAssessmentCreate,
    OocyteAssessmentOut,
)
from app.users.models import User

router = APIRouter(prefix="/embryology", tags=["embryology"])


@router.post("/oocyte-assessments", response_model=OocyteAssessmentOut, status_code=201)
async def create_oocyte_assessment(
    body: OocyteAssessmentCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("embryology.write")),
) -> OocyteAssessmentOut:
    return await service.create_oocyte_assessment(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/embryos", response_model=EmbryoOut, status_code=201)
async def grade_embryo(
    body: EmbryoCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("embryology.write")),
) -> EmbryoOut:
    return await service.grade_embryo(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/embryos/by-cycle/{cycle_id}", response_model=list[EmbryoOut])
async def list_embryos(
    cycle_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("embryology.read")),
) -> list[EmbryoOut]:
    return await service.list_embryos_for_cycle(session, cycle_id)


@router.post("/embryos/{embryo_id}/status", response_model=EmbryoOut)
async def update_status(
    embryo_id: str,
    body: EmbryoStatusUpdate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("embryology.write")),
) -> EmbryoOut:
    return await service.update_embryo_status(
        session, embryo_id, body.status, body.notes, actor_id=current.id, actor_role=current.role.code
    )
