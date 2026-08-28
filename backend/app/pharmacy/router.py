from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.idempotency import get_idempotent_response, hash_request_body, store_idempotent_response
from app.pharmacy import service
from app.pharmacy.schemas import DispenseRequest, MedicineOut, SaleOut
from app.users.models import User

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])


@router.get("/medicines", response_model=list[MedicineOut])
async def list_medicines(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("pharmacy.read")),
) -> list[MedicineOut]:
    return await service.list_medicines_with_stock(session)


@router.post("/dispense", response_model=SaleOut, status_code=201)
async def dispense(
    body: DispenseRequest,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("pharmacy.dispense")),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> SaleOut:
    """Requires Idempotency-Key — a retried dispense request must never
    deduct stock twice, per spec §33/§34."""
    req_hash = hash_request_body(body.model_dump(mode="json"))
    cached = await get_idempotent_response(session, key=idempotency_key, request_hash=req_hash)
    if cached is not None:
        return SaleOut(**cached)

    sale = await service.dispense(session, body, actor_id=current.id, actor_role=current.role.code)
    out = SaleOut.model_validate(sale)
    await store_idempotent_response(session, key=idempotency_key, request_hash=req_hash, response=out.model_dump(mode="json"))
    return out


@router.get("/sales", response_model=list[SaleOut])
async def list_sales(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("pharmacy.read")),
) -> list[SaleOut]:
    return await service.list_sales(session)


@router.get("/sales/{sale_id}", response_model=SaleOut)
async def get_sale(
    sale_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("pharmacy.read")),
) -> SaleOut:
    return await service.get_sale(session, sale_id)
