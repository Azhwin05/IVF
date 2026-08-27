"""
Billing domain: Package -> Invoice -> Charge -> Payment, plus the
billing-lock gate from spec §14:

    Clinical Service -> Charge Created -> Invoice/Pending Charge
        -> Payment Required
            -> Paid -> Proceed
            -> Package Included -> Proceed
            -> Authorized Credit -> Proceed
            -> Emergency Override -> Proceed with Audit

Money is stored in integer paise (INR minor unit) throughout, never
float, to avoid floating-point rounding drift in financial totals.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERRIDDEN = "overridden"  # proceeded via emergency override, payment still outstanding
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    UPI = "upi"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    CREDIT = "credit"


class Package(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "packages"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    validity_description: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PatientPackage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A package sold to a specific couple/patient — inclusions are checked
    against this row when deciding whether a charge is 'package included'."""
    __tablename__ = "patient_packages"

    couple_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("couples.id"), nullable=False, index=True)
    package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("packages.id"), nullable=False)
    included_service_codes: Mapped[list] = mapped_column(String, nullable=False, default="")  # comma-separated for simplicity; see docs/database for a proper join table if this grows


class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    couple_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("couples.id"), nullable=True)

    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING, index=True)
    total_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    paid_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discount_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discount_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    discount_approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    charges: Mapped[list["Charge"]] = relationship(back_populates="invoice", lazy="selectin")
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice", lazy="selectin")

    @property
    def outstanding_paise(self) -> int:
        return self.total_amount_paise - self.discount_paise - self.paid_amount_paise


class Charge(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "charges"

    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    invoice: Mapped["Invoice"] = relationship(back_populates="charges")

    service_code: Mapped[str] = mapped_column(String(64), nullable=False)  # matches ProcedureCharge.code
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    covered_by_package: Mapped[bool] = mapped_column(Boolean, default=False)
    source_module: Mapped[str | None] = mapped_column(String(64), nullable=True)  # "ivf", "pharmacy", "laboratory", ...
    source_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Payment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "payments"

    receipt_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    invoice: Mapped["Invoice"] = relationship(back_populates="payments")

    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(128), nullable=True)  # UTR / txn id
    received_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    is_refund: Mapped[bool] = mapped_column(Boolean, default=False)
    refund_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    refund_approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class BillingOverride(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Emergency-override audit trail — every time a chargeable workflow
    step proceeded WITHOUT payment, per spec §14."""
    __tablename__ = "billing_overrides"

    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    authorized_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class ProcedureCharge(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Master pricing data — 'Initial IVF Consultation', 'Oocyte Retrieval
    (TVOR)', etc. Managed via the System Administration screen (spec §4:
    'administration panel to manage... procedure charges, packages...')."""
    __tablename__ = "procedure_charges"

    service_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    procedure_name: Mapped[str] = mapped_column(String(255), nullable=False)
    charge_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
