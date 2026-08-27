"""QA/QC scheduled recurring tasks, spec §22."""
import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class QAFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class QATaskTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """The recurring definition — Celery Beat generates a new QATaskInstance
    from this on schedule; the template itself is never marked 'complete'."""
    __tablename__ = "qa_task_templates"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(64), nullable=False)
    frequency: Mapped[QAFrequency] = mapped_column(Enum(QAFrequency), nullable=False)
    checklist_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)


class QATaskInstance(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "qa_task_instances"

    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("qa_task_templates.id"), nullable=False, index=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    completed: Mapped[bool] = mapped_column(default=False)
    completed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    evidence_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patient_documents.id"), nullable=True)
