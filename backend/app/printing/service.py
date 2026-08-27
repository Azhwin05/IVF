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
