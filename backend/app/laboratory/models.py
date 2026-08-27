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
