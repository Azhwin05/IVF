from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing import service
from app.billing.schemas import (
    BillingOverrideCreate,
    DiscountApply,
    InvoiceCreate,
    InvoiceOut,
    PaymentCreate,
    PaymentOut,
    RefundCreate,
)
from app.core.database import get_db
from app.core.deps import require_permission
from app.core.idempotency import get_idempotent_response, hash_request_body, store_idempotent_response
from app.users.models import User

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/invoices", response_model=list[InvoiceOut])
async def list_invoices(
    patient_id: str | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("billing.read")),
) -> list[InvoiceOut]:
    return await service.list_invoices(session, patient_id=patient_id)


@router.post("/invoices", response_model=InvoiceOut, status_code=201)
async def create_invoice(
    body: InvoiceCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("billing.create")),
) -> InvoiceOut:
    return await service.create_invoice(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    invoice_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("billing.read")),
) -> InvoiceOut:
    return await service.get_invoice(session, invoice_id)


@router.post("/payments", response_model=PaymentOut, status_code=201)
async def record_payment(
    body: PaymentCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("billing.payment")),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> PaymentOut:
    """Requires an Idempotency-Key header — per spec §35, payments must
    never be duplicated by a double-click or a client retry. The frontend
    generates one UUID per user-initiated payment action and resends the
    same key on retry; a replayed key with the same body returns the
    original result without charging twice."""
    req_hash = hash_request_body(body.model_dump(mode="json"))
    cached = await get_idempotent_response(session, key=idempotency_key, request_hash=req_hash)
    if cached is not None:
        return PaymentOut(**cached)

    payment = await service.record_payment(
        session, invoice_id=body.invoice_id, amount_paise=body.amount_paise, method=body.method,
        reference=body.reference, actor_id=current.id, actor_role=current.role.code,
    )
    out = PaymentOut.model_validate(payment)
    await store_idempotent_response(session, key=idempotency_key, request_hash=req_hash, response=out.model_dump(mode="json"))
    return out


@router.post("/refunds", response_model=PaymentOut, status_code=201)
async def record_refund(
    body: RefundCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("billing.refund")),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> PaymentOut:
    req_hash = hash_request_body(body.model_dump(mode="json"))
    cached = await get_idempotent_response(session, key=idempotency_key, request_hash=req_hash)
    if cached is not None:
        return PaymentOut(**cached)

    refund = await service.record_refund(
        session, invoice_id=body.invoice_id, amount_paise=body.amount_paise, reason=body.reason,
        actor_id=current.id, actor_role=current.role.code,
    )
    out = PaymentOut.model_validate(refund)
    await store_idempotent_response(session, key=idempotency_key, request_hash=req_hash, response=out.model_dump(mode="json"))
    return out


@router.post("/discounts", response_model=InvoiceOut)
async def apply_discount(
    body: DiscountApply,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("billing.discount")),
) -> InvoiceOut:
    return await service.apply_discount(
        session, invoice_id=body.invoice_id, discount_paise=body.discount_paise, reason=body.reason,
        actor_id=current.id, actor_role=current.role.code,
    )


@router.post("/overrides", status_code=201)
async def authorize_override(
    body: BillingOverrideCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("billing.override")),
) -> dict:
    override = await service.authorize_billing_override(
        session, invoice_id=body.invoice_id, reason=body.reason, actor_id=current.id, actor_role=current.role.code
    )
    return {"id": str(override.id), "authorized": True}
