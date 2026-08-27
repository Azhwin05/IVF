import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class EntryType(str, enum.Enum):
    RECEIPT = "receipt"
    PAYMENT = "payment"


class CashBookEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cash_book_entries"

    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    particulars: Mapped[str] = mapped_column(String(500), nullable=False)
    entry_type: Mapped[EntryType] = mapped_column(Enum(EntryType), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)  # Cash, UPI, Bank Transfer, Cheque
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)  # signed: receipts +, payments -
    linked_payment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    recorded_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)


class LedgerAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ledger_accounts"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    debit_paise: Mapped[int] = mapped_column(Integer, default=0)
    credit_paise: Mapped[int] = mapped_column(Integer, default=0)

    @property
    def balance_paise(self) -> int:
        return self.debit_paise - self.credit_paise
