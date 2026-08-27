import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounting.models import CashBookEntry, EntryType, LedgerAccount
from app.accounting.schemas import CashBookEntryCreate
from app.audit.service import record_audit_event
from app.billing.models import Charge, Invoice, Payment


async def record_cash_book_entry(
    session: AsyncSession, data: CashBookEntryCreate, *, actor_id: uuid.UUID, actor_role: str
) -> CashBookEntry:
    """Critical action — requires accounting.write permission at router."""
    signed_amount = data.amount_paise if data.entry_type == EntryType.RECEIPT else -abs(data.amount_paise)
    entry = CashBookEntry(
        entry_date=data.entry_date, particulars=data.particulars, entry_type=data.entry_type,
        mode=data.mode, amount_paise=signed_amount, recorded_by_id=actor_id,
    )
    session.add(entry)
    await session.flush()

    await record_audit_event(
        session, actor_id=actor_id, actor_role=actor_role,
        action="accounting.entry_recorded", entity_type="CashBookEntry", entity_id=str(entry.id),
        after_state={"amount_paise": signed_amount, "particulars": data.particulars},
    )
    return entry


async def list_cash_book(session: AsyncSession, *, from_date: date, to_date: date) -> list[CashBookEntry]:
    result = await session.execute(
        select(CashBookEntry)
        .where(CashBookEntry.entry_date.between(from_date, to_date))
        .order_by(CashBookEntry.entry_date.desc())
    )
    return list(result.scalars().all())


async def list_ledger_accounts(session: AsyncSession) -> list[LedgerAccount]:
    result = await session.execute(select(LedgerAccount).order_by(LedgerAccount.name))
    return list(result.scalars().all())


async def profit_loss_report(session: AsyncSession, *, from_date: date, to_date: date) -> dict:
    """Real aggregation from the Charge/Payment tables (replacing the
    frontend's static PROFIT_LOSS fixture) — revenue grouped by
    source_module, matching the frontend's Revenue breakdown categories."""
    revenue_result = await session.execute(
        select(Charge.source_module, func.sum(Charge.amount_paise))
        .join(Invoice, Invoice.id == Charge.invoice_id)
        .where(Invoice.created_at.between(from_date, to_date))
        .group_by(Charge.source_module)
    )
    revenue = {(module or "consultation"): int(total) for module, total in revenue_result.all()}

    expense_result = await session.execute(
        select(func.sum(Payment.amount_paise)).where(
            Payment.is_refund.is_(True), Payment.created_at.between(from_date, to_date)
        )
    )
    total_expenses = int(expense_result.scalar_one() or 0)

    total_revenue = sum(revenue.values())
    return {
        "period": f"{from_date.isoformat()} to {to_date.isoformat()}",
        "revenue": revenue,
        "expenses": {"refunds": total_expenses},
        "net_profit_paise": total_revenue - total_expenses,
    }
