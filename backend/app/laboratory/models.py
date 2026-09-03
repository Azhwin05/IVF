import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class LabOrderSource(str, enum.Enum):
    INTERNAL = "internal_lab"
    EXTERNAL = "external_lab"


class LabOrderStatus(str, enum.Enum):
    ORDERED = "ordered"
    SAMPLE_COLLECTED = "sample_collected"
    IN_PROGRESS = "in_progress"
    REPORT_READY = "report_ready"
    DELIVERED = "delivered"


class LabOrderPriority(str, enum.Enum):
    ROUTINE = "routine"
    URGENT = "urgent"


class LabTestCatalogueItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lab_test_catalogue"

    test_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    turnaround_time: Mapped[str] = mapped_column(String(64), nullable=False)  # "24 hrs"
    sample_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class LabOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lab_orders"

    order_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    test_catalogue_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lab_test_catalogue.id"), nullable=True)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)

    ordered_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sample_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[LabOrderSource] = mapped_column(Enum(LabOrderSource), default=LabOrderSource.INTERNAL)
    external_lab_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[LabOrderPriority] = mapped_column(Enum(LabOrderPriority), default=LabOrderPriority.ROUTINE)
    status: Mapped[LabOrderStatus] = mapped_column(Enum(LabOrderStatus), default=LabOrderStatus.ORDERED, index=True)

    result_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patient_documents.id"), nullable=True)
    result_verified_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    result_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LabResultFlag(str, enum.Enum):
    NORMAL = "normal"
    LOW = "low"
    HIGH = "high"
    CRITICAL = "critical"


class LabResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Structured, chartable result values — new requirement (source doc §6):
    previously a lab order's result existed only as an attached file
    (`LabOrder.result_document_id`), so nothing in the system could show a
    single numeric value like 'AMH: 2.4 ng/mL'. One order can have many
    parameters (e.g. a hormonal panel), hence a separate table rather than
    columns on LabOrder."""
    __tablename__ = "lab_results"

    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lab_orders.id"), nullable=False, index=True)
    parameter_name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "AMH", "FSH", "Lead Follicle"
    value: Mapped[str] = mapped_column(String(64), nullable=False)  # kept as string — some params are qualitative ("Normal cavity")
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(64), nullable=True)  # e.g. "1.0 – 4.0"
    flag: Mapped[LabResultFlag] = mapped_column(Enum(LabResultFlag), default=LabResultFlag.NORMAL)
    entered_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
