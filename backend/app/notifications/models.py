"""Central notification + task engine, spec §19 — not random browser
popups. Tasks (e.g. 'Call patient before tomorrow's retrieval') escalate
if left unresolved past their due time; see app/workers/tasks.py."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class NotificationTone(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    ATTENTION = "attention"
    CRITICAL = "critical"


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[NotificationTone] = mapped_column(Enum(NotificationTone), default=NotificationTone.INFO)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    link_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    link_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class TaskStatus(str, enum.Enum):
    OPEN = "open"
    DONE = "done"
    ESCALATED = "escalated"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AlertType(str, enum.Enum):
    """New requirement (source doc §8) — typed so a UI can filter/badge
    consistently instead of pattern-matching free-text titles."""
    FOLLOW_UP = "follow_up"
    PROCEDURE_REMINDER = "procedure_reminder"
    EGG_EVENT = "egg_event"
    MEDICATION_REMINDER = "medication_reminder"
    FRONT_DESK = "front_desk"
    OTHER = "other"


class NotificationTask(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """E.g. 'Call Patient — Priya Raman — Tomorrow: Oocyte Retrieval 10:30 AM'
    with [Mark Called] / [Not Reachable] / [Reschedule] actions, from
    spec §19's example. DB-backed with a real due_at/status — critical
    reminders must never be implemented as frontend-only timers (source
    doc §8)."""
    __tablename__ = "notification_tasks"

    patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True, index=True)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType), default=AlertType.OTHER, index=True)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.NORMAL, index=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    assigned_to_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.OPEN, index=True)
    resolution: Mapped[str | None] = mapped_column(String(128), nullable=True)  # "called", "not_reachable", "rescheduled"
    escalated_to_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    related_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
