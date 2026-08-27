"""
Idempotency-key handling for critical mutating endpoints (payments,
refunds, pharmacy dispensing), per spec §34/§35: "Never create a
duplicate payment because the user clicked twice."

Usage pattern in a router:

    @router.post("/payments")
    async def record_payment(body: PaymentCreate, idempotency_key: str = Header(...), ...):
        cached = await get_idempotent_response(session, key=idempotency_key, request_hash=hash(body))
        if cached:
            return cached  # exact replay of the original response, no side effects re-run
        result = await service.record_payment(...)
        await store_idempotent_response(session, key=idempotency_key, request_hash=hash(body), response=result)
        return result
"""
import hashlib
import json
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.exceptions import IdempotencyConflictError


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_body: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def hash_request_body(body: dict) -> str:
    canonical = json.dumps(body, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


async def get_idempotent_response(session: AsyncSession, *, key: str, request_hash: str) -> dict | None:
    record = await session.get(IdempotencyRecord, key)
    if record is None:
        return None
    if record.request_hash != request_hash:
        raise IdempotencyConflictError(
            "This idempotency key was already used with a different request payload."
        )
    return record.response_body


async def store_idempotent_response(session: AsyncSession, *, key: str, request_hash: str, response: dict) -> None:
    session.add(IdempotencyRecord(key=key, request_hash=request_hash, response_body=response))
    await session.flush()
