"""Shared field types for response schemas."""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator


def _as_utc(value: datetime) -> datetime:
    """Guarantee the value carries an offset before it is serialised.

    Timestamps are written as UTC instants, but not every driver hands them back
    with tzinfo attached. Without this, the same row could serialise as
    "...T04:00:00" on one database and "...T04:00:00+00:00" on another, and a
    client would render the first as local time. Reading a naive value back as
    UTC is what it already is, not a guess.
    """
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


UtcDatetime = Annotated[datetime, AfterValidator(_as_utc)]
