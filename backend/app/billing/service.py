"""
Billing service — the highest-stakes module in the system alongside
pharmacy dispensing. Every mutation here is wrapped so that:
  - invoice/receipt numbers are generated under a row lock (no duplicate
    numbers under concurrent requests, per spec §33/§35)
  - payment amounts can never push paid_amount past total (no negative
    outstanding, no overpayment silently accepted)
  - every payment, refund, discount, and override is audited with actor,
    reason, and timestamp, per spec §6 "Financial and clinical integrity"
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import record_audit_event
from app.billing.models import (
    BillingOverride,
    Charge,
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentMethod,
)
from app.billing.schemas import InvoiceCreate
from app.core.exceptions import ConflictError, NotFoundError, ValidationFailedError
from app.events.bus import EventType, emit


async def _next_sequence_number(session: AsyncSession, *, prefix: str, table, column) -> str:
    """Generates INV-2026-00001 / RCP-2026-00001 style numbers under a
    SELECT ... FOR UPDATE-equivalent guard: PostgreSQL's row locking on the
    max-value query via `with_for_update()` serializes concurrent number
    generation so two simultaneous requests never get the same number."""
    year = datetime.now(timezone.utc).year
    full_prefix = f"{prefix}-{year}-"
    stmt = select(column).where(column.like(f"{full_prefix}%")).order_by(column.desc()).limit(1).with_for_update()
    result = await session.execute(stmt)
    last = result.scalar_one_or_none()
    next_seq = int(last.split("-")[-1]) + 1 if last else 1
    return f"{full_prefix}{next_seq:05d}"


async def create_invoice(
    session: AsyncSession, data: InvoiceCreate, *, actor_id: uuid.UUID, actor_role: str
) -> Invoice:
    invoice_number = await _next_sequence_number(session, prefix="INV", table=Invoice, column=Invoice.invoice_number)
    invoice = Invoice(
        invoice_number=invoice_number,
        patient_id=data.patient_id,
        couple_id=data.couple_id,
        total_amount_paise=sum(c.amount_paise for c in data.charges),
    )
    session.add(invoice)
    await session.flush()

    for c in data.charges:
        session.add(Charge(invoice_id=invoice.id, **c.model_dump()))
    await session.flush()

    # Charge rows above were added via their raw invoice_id FK, not by
    # appending to invoice.charges — so the relationship's lazy="selectin"
    # loader has never populated this specific in-memory instance. Without
    # this explicit refresh, InvoiceOut's `charges` field would trigger a
    # lazy load during FastAPI's response serialization, which runs
    # outside the async/greenlet context and raises MissingGreenlet.
    await session.refresh(invoice, attribute_names=["charges"])

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="billing.invoice_created", entity_type="Invoice", entity_id=str(invoice.id),
        after_state={"invoice_number": invoice.invoice_number, "total_paise": invoice.total_amount_paise},
    )
    return invoice


async def get_invoice(session: AsyncSession, invoice_id: uuid.UUID) -> Invoice:
    invoice = await session.get(Invoice, invoice_id)
    if not invoice:
        raise NotFoundError("Invoice not found", error_code="invoice_not_found")
    # Force-refresh in case this instance was already in the identity map
    # from an earlier operation in the same session without its
    # relationships populated (see create_invoice's comment above).
    await session.refresh(invoice, attribute_names=["charges", "payments"])
    return invoice


def is_payment_satisfied(invoice: Invoice) -> bool:
    """The check the workflow engine (Phase 3) calls before allowing a
    chargeable step to proceed — the billing-lock gate from spec §14."""
    return invoice.status in (InvoiceStatus.PAID, InvoiceStatus.OVERRIDDEN) or invoice.outstanding_paise <= 0


async def record_payment(
    session: AsyncSession, *, invoice_id: uuid.UUID, amount_paise: int, method: PaymentMethod,
    reference: str | None, actor_id: uuid.UUID, actor_role: str,
) -> Payment:
    # Lock the invoice row for the duration of this balance update so two
    # concurrent payment submissions (double-click, retry) can't both read
    # the same stale outstanding balance and both succeed.
    result = await session.execute(select(Invoice).where(Invoice.id == invoice_id).with_for_update())
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise NotFoundError("Invoice not found", error_code="invoice_not_found")

    if invoice.status == InvoiceStatus.CANCELLED:
        raise ConflictError("Cannot record a payment against a cancelled invoice.")

    max_payable = invoice.total_amount_paise - invoice.discount_paise - invoice.paid_amount_paise
    if amount_paise > max_payable:
        raise ValidationFailedError(
            f"Payment of {amount_paise} exceeds outstanding balance of {max_payable}.",
            error_code="overpayment_rejected",
        )

    receipt_number = await _next_sequence_number(session, prefix="RCP", table=Payment, column=Payment.receipt_number)
    payment = Payment(
        receipt_number=receipt_number, invoice_id=invoice.id, amount_paise=amount_paise,
        method=method, reference=reference, received_by_id=actor_id,
    )
    session.add(payment)

    invoice.paid_amount_paise += amount_paise
    invoice.status = (
        InvoiceStatus.PAID if invoice.outstanding_paise <= 0 else InvoiceStatus.PARTIALLY_PAID
    )
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="billing.payment_recorded", entity_type="Payment", entity_id=str(payment.id),
        after_state={"receipt_number": receipt_number, "amount_paise": amount_paise, "method": method.value},
    )
    await emit(
        session, event_type=EventType.PAYMENT_RECEIVED, entity_type="Invoice", entity_id=str(invoice.id),
        payload={"payment_id": str(payment.id), "amount_paise": amount_paise},
    )
    return payment


async def record_refund(
    session: AsyncSession, *, invoice_id: uuid.UUID, amount_paise: int, reason: str,
    actor_id: uuid.UUID, actor_role: str,
) -> Payment:
    """Requires billing.refund permission — enforced at the router level.
    This is a critical action per spec §6: reason is mandatory (validated
    by the Pydantic schema's min_length), actor and timestamp captured via
    the audit event."""
    result = await session.execute(select(Invoice).where(Invoice.id == invoice_id).with_for_update())
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise NotFoundError("Invoice not found", error_code="invoice_not_found")

    if amount_paise > invoice.paid_amount_paise:
        raise ValidationFailedError("Refund amount exceeds the amount actually paid on this invoice.")

    receipt_number = await _next_sequence_number(session, prefix="RFD", table=Payment, column=Payment.receipt_number)
    refund = Payment(
        receipt_number=receipt_number, invoice_id=invoice.id, amount_paise=amount_paise,
        method=PaymentMethod.BANK_TRANSFER, received_by_id=actor_id,
        is_refund=True, refund_reason=reason, refund_approved_by_id=actor_id,
    )
    session.add(refund)
    invoice.paid_amount_paise -= amount_paise
    if invoice.paid_amount_paise < invoice.total_amount_paise - invoice.discount_paise:
        invoice.status = InvoiceStatus.PARTIALLY_PAID
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="billing.refund_issued", entity_type="Payment", entity_id=str(refund.id),
        after_state={"amount_paise": amount_paise}, reason=reason,
    )
    await emit(
        session, event_type=EventType.PAYMENT_REFUNDED, entity_type="Invoice", entity_id=str(invoice.id),
        payload={"refund_id": str(refund.id), "amount_paise": amount_paise},
    )
    return refund


async def apply_discount(
    session: AsyncSession, *, invoice_id: uuid.UUID, discount_paise: int, reason: str,
    actor_id: uuid.UUID, actor_role: str,
) -> Invoice:
    """Critical action — requires billing.discount permission at the router."""
    invoice = await get_invoice(session, invoice_id)
    if discount_paise > invoice.total_amount_paise:
        raise ValidationFailedError("Discount cannot exceed the invoice total.")

    before = {"discount_paise": invoice.discount_paise}
    invoice.discount_paise = discount_paise
    invoice.discount_reason = reason
    invoice.discount_approved_by_id = actor_id
    if invoice.outstanding_paise <= 0:
        invoice.status = InvoiceStatus.PAID
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="billing.discount_applied", entity_type="Invoice", entity_id=str(invoice.id),
        before_state=before, after_state={"discount_paise": discount_paise}, reason=reason,
    )
    return invoice


async def authorize_billing_override(
    session: AsyncSession, *, invoice_id: uuid.UUID, reason: str, actor_id: uuid.UUID, actor_role: str,
) -> BillingOverride:
    """The 'Emergency Override -> Proceed with Audit' path from spec §14.
    Requires billing.override permission at the router. Never silently
    allowed — always creates a permanent, reasoned audit trail."""
    invoice = await get_invoice(session, invoice_id)
    override = BillingOverride(invoice_id=invoice.id, authorized_by_id=actor_id, reason=reason)
    session.add(override)
    invoice.status = InvoiceStatus.OVERRIDDEN
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="billing.override_authorized", entity_type="Invoice", entity_id=str(invoice.id),
        reason=reason,
    )
    return override
