"""Report-job generators.

Each generator is an async function ``(session, parameters) -> (bytes, content_type)``.
It only reads from other modules' tables; it never writes to them. Register new
report types in ``REPORT_GENERATORS`` - the async job pipeline does not change.

``generate_patient_summary`` produces a professional PDF (built with fpdf2, a
pure-Python library) here in the Celery worker - the browser never renders it.
The gathered data is identical to the JSON the job previously emitted; only the
serialisation changed.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace
from sqlalchemy.ext.asyncio import AsyncSession

from app.appointments.models import Appointment
from app.laboratory.models import LabReport, LabReportResult
from app.patients.models import Patient
from app.reports.job_models import ReportType

Generator = Callable[[AsyncSession, dict[str, Any]], Awaitable[tuple[bytes, str]]]


class ReportGenerationError(Exception):
    """A generator could not produce the report. Message is safe to surface."""


# fpdf2's core fonts (Helvetica) are latin-1 only. Patient data is free text, so
# every string is passed through this before it reaches the PDF - unsupported
# code points become "?" rather than crashing the worker. A future switch to an
# embedded Unicode TTF would lift this.
_BRAND = (6, 95, 70)          # brand-700 green, matches the app UI
_HEADING_FILL = (232, 240, 236)
_ROW_ALT = (247, 249, 248)


def _safe(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.encode("latin-1", "replace").decode("latin-1")


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _fmt_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%d %b %Y, %H:%M UTC")


def _fmt_date(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%d %b %Y")


class _PatientSummaryPDF(FPDF):
    """A4 patient-summary report with a repeating title bar and page footer."""

    def __init__(self) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(15, 16, 15)
        self.set_auto_page_break(auto=True, margin=18)
        self.set_title("Patient Summary Report")

    # -- repeating chrome ---------------------------------------------------
    def header(self) -> None:
        self.set_fill_color(*_BRAND)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 10, "  Dr. Archana IVF & Women Centre", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, "  Patient Summary Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(
            0, 8,
            f"Confidential clinical document  -  generated {_fmt_dt(datetime.now(timezone.utc))}  -  "
            f"Page {self.page_no()}/{{nb}}",
            align="C",
        )
        self.set_text_color(0, 0, 0)

    # -- building blocks --------------------------------------------------
    def section(self, title: str) -> None:
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(*_HEADING_FILL)
        self.cell(0, 8, f"  {_safe(title)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.ln(1.5)

    def kv(self, label: str, value: Any) -> None:
        self.set_font("Helvetica", "B", 9.5)
        self.cell(45, 6, _safe(label), new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("Helvetica", "", 9.5)
        self.multi_cell(0, 6, _safe(value) or "-", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def note(self, text: str) -> None:
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(110, 110, 110)
        self.multi_cell(0, 5, _safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)


async def generate_patient_summary(
    session: AsyncSession, parameters: dict[str, Any]
) -> tuple[bytes, str]:
    """A PDF snapshot of one patient: demographics, appointment counts, and
    every uploaded lab report and its extracted results on file for them."""
    patient_id = UUID(str(parameters["patient_id"]))

    patient = (
        await session.execute(sa.select(Patient).where(Patient.id == patient_id))
    ).scalar_one_or_none()
    if patient is None:
        raise ReportGenerationError("The patient no longer exists.")

    appt_rows = (
        await session.execute(
            sa.select(Appointment.status, sa.func.count())
            .where(Appointment.patient_id == patient_id)
            .group_by(Appointment.status)
        )
    ).all()
    appointments_by_status = {
        (status.value if hasattr(status, "value") else str(status)): count
        for status, count in appt_rows
    }
    appointments_total = sum(appointments_by_status.values())

    lab_reports = (
        await session.execute(
            sa.select(LabReport)
            .where(LabReport.patient_id == patient_id)
            .order_by(LabReport.created_at.desc(), LabReport.id.desc())
        )
    ).scalars().all()

    report_ids = [r.id for r in lab_reports]
    results_by_report: dict[UUID, list[LabReportResult]] = {rid: [] for rid in report_ids}
    if report_ids:
        result_rows = (
            await session.execute(
                sa.select(LabReportResult)
                .where(LabReportResult.report_id.in_(report_ids))
                .order_by(LabReportResult.report_id, LabReportResult.id)
            )
        ).scalars().all()
        for row in result_rows:
            results_by_report.setdefault(row.report_id, []).append(row)
    result_count = sum(len(v) for v in results_by_report.values())

    # ---- render -------------------------------------------------------------
    pdf = _PatientSummaryPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(
        0, 5, f"Generated {_fmt_dt(datetime.now(timezone.utc))}",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_text_color(0, 0, 0)

    pdf.section("Patient Information")
    pdf.kv("UHID", patient.uhid)
    pdf.kv("Full name", patient.full_name)
    pdf.kv("Date of birth", _fmt_date(patient.date_of_birth))
    pdf.kv("Gender", patient.gender)
    pdf.kv("Phone", patient.phone)
    pdf.kv("Email", patient.email)

    pdf.section("Appointments")
    pdf.kv("Total on record", appointments_total)
    if appointments_by_status:
        for status_name, count in sorted(appointments_by_status.items()):
            pdf.kv(status_name.replace("_", " ").title(), count)
    else:
        pdf.note("No appointments on record for this patient.")

    pdf.section("Laboratory")
    pdf.kv("Uploaded reports", len(lab_reports))
    pdf.kv("Extracted results", result_count)

    if not lab_reports:
        pdf.note("No laboratory reports have been uploaded for this patient.")

    for i, report in enumerate(lab_reports, start=1):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(
            0, 6,
            _safe(f"{i}. {report.original_filename}"),
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(
            0, 5,
            _safe(
                f"{report.document_kind.value}  |  extraction: {report.extraction_status.value}"
                f" ({report.extraction_method.value})  |  pages: {report.page_count or '-'}"
                f"  |  uploaded {_fmt_date(report.created_at)}"
                f"  |  extracted {_fmt_date(report.extracted_at)}"
            ),
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

        rows = results_by_report.get(report.id, [])
        if not rows:
            pdf.note("   No structured results extracted from this report.")
            continue

        with pdf.table(
            width=180,
            col_widths=(52, 22, 22, 34, 20, 30),
            line_height=5.5,
            headings_style=FontFace(emphasis="BOLD", fill_color=_HEADING_FILL),
            cell_fill_color=_ROW_ALT,
            cell_fill_mode="ROWS",
            text_align=("LEFT", "LEFT", "LEFT", "LEFT", "LEFT", "LEFT"),
            first_row_as_headings=True,
        ) as table:
            table.row(["Test", "Value", "Unit", "Reference range", "Origin", "Validation"])
            for r in rows:
                table.row([
                    _safe(r.test_name),
                    _safe(r.value),
                    _safe(r.unit),
                    _safe(r.reference_range),
                    _safe(r.entry_origin.value),
                    _safe(r.validation_status.value.replace("_", " ")),
                ])

    out = pdf.output()
    return bytes(out), "application/pdf"


REPORT_GENERATORS: dict[ReportType, Generator] = {
    ReportType.patient_summary: generate_patient_summary,
}
