from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounting import service
from app.accounting.schemas import CashBookEntryCreate, CashBookEntryOut, LedgerAccountOut
from app.core.database import get_db
from app.core.deps import require_permission
from app.users.models import User

router = APIRouter(prefix="/accounting", tags=["accounting"])


@router.get("/cash-book", response_model=list[CashBookEntryOut])
async def list_cash_book(
    from_date: date = Query(...),
    to_date: date = Query(...),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("accounting.read")),
) -> list[CashBookEntryOut]:
    return await service.list_cash_book(session, from_date=from_date, to_date=to_date)


@router.post("/cash-book", response_model=CashBookEntryOut, status_code=201)
async def record_entry(
    body: CashBookEntryCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("accounting.write")),
) -> CashBookEntryOut:
    return await service.record_cash_book_entry(session, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/ledger", response_model=list[LedgerAccountOut])
async def list_ledger(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("accounting.read")),
) -> list[LedgerAccountOut]:
    return await service.list_ledger_accounts(session)


@router.get("/profit-loss")
async def profit_loss(
    from_date: date = Query(...),
    to_date: date = Query(...),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("accounting.read")),
) -> dict:
    return await service.profit_loss_report(session, from_date=from_date, to_date=to_date)
