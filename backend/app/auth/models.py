"""
Session + refresh-token model.

Design: one `Session` row per login (per device). Each session has a
chain of RefreshTokens — every refresh rotates to a new token and marks
the old one `used_at`. If a *used* token is presented again, that's
theft/replay: the entire session is revoked immediately (reuse
detection, per spec §6).
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class Session(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    device_label: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g. "iPad — OT Room"
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # absolute lifetime
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # idle-timeout tracking
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="session", lazy="selectin")

    @property
    def is_valid(self) -> bool:
        return self.revoked_at is None


class RefreshToken(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "refresh_tokens"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    session: Mapped["Session"] = relationship(back_populates="refresh_tokens")

    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
