import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.accounting.models import EntryType


class CashBookEntryCreate(BaseModel):
    entry_date: date
    particulars: str
    entry_type: EntryType
    mode: str
    amount_paise: int


class CashBookEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    entry_date: date
    particulars: str
    entry_type: EntryType
    mode: str
    amount_paise: int


class LedgerAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    debit_paise: int
    credit_paise: int
    balance_paise: int


class ProfitLossReport(BaseModel):
    period: str
    revenue: dict[str, int]
    expenses: dict[str, int]
    net_profit_paise: int
