"""
Cursor-based pagination — per the spec's API design rules (§32), list
endpoints never return unbounded result sets. Cursor is a base64-encoded
(created_at, id) tuple so pagination stays stable even as new rows are
inserted between page fetches (unlike OFFSET/LIMIT).
"""
import base64
import json
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None
    has_more: bool


def encode_cursor(created_at: datetime, id_: UUID) -> str:
    raw = json.dumps({"t": created_at.isoformat(), "id": str(id_)})
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    raw = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    return datetime.fromisoformat(raw["t"]), UUID(raw["id"])


async def paginate(
    session: AsyncSession,
    stmt: Select,
    *,
    model,
    cursor: str | None,
    limit: int,
) -> tuple[list, str | None, bool]:
    """Applies a stable (created_at DESC, id DESC) cursor page to `stmt`.
    `model` must expose .created_at and .id columns."""
    limit = max(1, min(limit, MAX_PAGE_SIZE))

    if cursor:
        after_time, after_id = decode_cursor(cursor)
        stmt = stmt.where(
            or_(
                model.created_at < after_time,
                and_(model.created_at == after_time, model.id < after_id),
            )
        )

    stmt = stmt.order_by(model.created_at.desc(), model.id.desc()).limit(limit + 1)
    result = await session.execute(stmt)
    rows = result.scalars().all()

    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = encode_cursor(rows[-1].created_at, rows[-1].id) if has_more and rows else None
    return list(rows), next_cursor, has_more
