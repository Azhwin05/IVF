"""
Print-ready document generation, spec §25. Phase-1 architecture: the
backend generates a print-ready PDF/label payload and hands it to the
browser to print (HMIS -> Generate print-ready document -> Browser
print / selected printer). The later local-print-agent architecture
described in the spec is a Phase 6+ addition and intentionally not
built here — this module is structured so that swap-in doesn't touch
callers (they only ever call `generate_*` and get bytes back).
"""
import io
import uuid

import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from pypdf import PdfWriter
from sqlalchemy.ext.asyncio import AsyncSession

from app.printing.models import PrintLog


def generate_qr_png(data: str) -> bytes:
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_barcode_png(data: str) -> bytes:
    buf = io.BytesIO()
    Code128(data, writer=ImageWriter()).write(buf)
    return buf.getvalue()


def generate_patient_id_card(*, uhid: str, full_name: str, blood_group: str | None) -> bytes:
    """Placeholder text-based PDF generator — swap for a proper templated
    renderer (e.g. WeasyPrint/ReportLab with the hospital's branded
    template) once the actual card layout is approved by the client."""
    writer = PdfWriter()
    writer.add_blank_page(width=242, height=153)  # ID-1 card size in points
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


PRINT_TEMPLATES = [
    "patient_id_card", "wristband", "prescription", "invoice", "receipt",
    "lab_report", "consent_form", "ot_document",
]


async def record_print_event(
    session: AsyncSession,
    *,
    document_type: str,
    printed_by_id: uuid.UUID,
    patient_id: uuid.UUID | None = None,
    context_entity_type: str | None = None,
    context_entity_id: str | None = None,
) -> PrintLog:
    """Single call every print/export endpoint in the system should make —
    new requirement (source doc §5/§2): 'who printed what, for whom, when'
    must be queryable on its own, not buried inside the generic audit
    stream. Call this from every future printable feature (prescriptions,
    consent forms, sample stickers, discharge summaries) rather than each
    one inventing its own logging."""
    log = PrintLog(
        document_type=document_type,
        printed_by_id=printed_by_id,
        patient_id=patient_id,
        context_entity_type=context_entity_type,
        context_entity_id=context_entity_id,
    )
    session.add(log)
    await session.flush()
    return log


async def list_print_history(session: AsyncSession, *, patient_id: uuid.UUID | None = None, limit: int = 200) -> list[PrintLog]:
    from sqlalchemy import select

    stmt = select(PrintLog).order_by(PrintLog.printed_at.desc()).limit(limit)
    if patient_id:
        stmt = stmt.where(PrintLog.patient_id == patient_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())
