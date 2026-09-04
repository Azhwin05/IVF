from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.deps import require_permission
from app.core.exceptions import NotFoundError, ValidationFailedError
from app.laboratory import report_service, service
from app.laboratory.models import LabOrderStatus
from app.laboratory.report_schemas import (
    LabReportDetail,
    LabReportPage,
    LabReportResultCorrectionRead,
    LabReportResultCorrectionRequest,
    LabReportResultManualCreate,
    LabReportResultRead,
    LabReportSummary,
)
from app.laboratory.schemas import LabOrderCreate, LabOrderOut, LabOrderStatusUpdate, LabResultCreate, LabResultOut
from app.laboratory.storage import ObjectStorage, get_object_storage
from app.users.models import User

router = APIRouter(prefix="/laboratory", tags=["laboratory"])

_MAX_FILENAME = 255


@router.get("/orders", response_model=list[LabOrderOut])
async def list_orders(
    status: LabOrderStatus | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("laboratory.read")),
) -> list[LabOrderOut]:
    return await service.list_orders(session, status=status)


@router.post("/orders", response_model=LabOrderOut, status_code=201)
async def create_order(
    body: LabOrderCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("laboratory.order")),
) -> LabOrderOut:
    return await service.create_order(session, body, actor_id=current.id, actor_role=current.role.code)


@router.post("/orders/{order_id}/status", response_model=LabOrderOut)
async def update_status(
    order_id: str,
    body: LabOrderStatusUpdate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("laboratory.result")),
) -> LabOrderOut:
    return await service.update_order_status(session, order_id, body.status, actor_id=current.id, actor_role=current.role.code)


@router.post("/orders/{order_id}/results", response_model=LabResultOut, status_code=201)
async def add_result(
    order_id: str,
    body: LabResultCreate,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("laboratory.result")),
) -> LabResultOut:
    return await service.add_result(session, order_id, body, actor_id=current.id, actor_role=current.role.code)


@router.get("/orders/{order_id}/results", response_model=list[LabResultOut])
async def get_results(
    order_id: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("laboratory.read")),
) -> list[LabResultOut]:
    return await service.list_results(session, order_id)


# ===========================================================================
# Outside-lab report ingestion: upload a document, run OCR / PDF-text
# extraction, review the structured results, and correct them with a full
# append-only history. Separate from the /orders workflow above.
#
#   laboratory.read    - view reports, results and correction history
#   laboratory.upload  - upload a report and run extraction
#   laboratory.correct - edit an extracted value or add a result by hand
# ===========================================================================


@router.post("/reports", response_model=LabReportDetail, status_code=201)
async def upload_lab_report(
    patient_id: UUID = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    storage: ObjectStorage = Depends(get_object_storage),
    _: User = Depends(require_permission("laboratory.upload")),
) -> LabReportDetail:
    data = await file.read()
    if len(data) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ValidationFailedError(
            f"The file is larger than the {settings.MAX_UPLOAD_SIZE_MB} MB limit."
        )
    report = await report_service.create_report(
        session,
        storage,
        patient_id=patient_id,
        filename=(file.filename or "report")[:_MAX_FILENAME],
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    return LabReportDetail.model_validate(report)


@router.get("/reports", response_model=LabReportPage)
async def list_lab_reports(
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=25, ge=1, le=100),
    cursor: str | None = Query(default=None),
    patient_id: UUID | None = Query(default=None),
    _: User = Depends(require_permission("laboratory.read")),
) -> LabReportPage:
    reports, next_cursor, has_more = await report_service.list_reports(
        session, limit=limit, cursor=cursor, patient_id=patient_id
    )
    return LabReportPage(
        items=[LabReportSummary.model_validate(r) for r in reports],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/reports/{report_id}", response_model=LabReportDetail)
async def get_lab_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("laboratory.read")),
) -> LabReportDetail:
    report = await report_service.get_report(session, report_id)
    if report is None:
        raise NotFoundError("Lab report not found.")
    return LabReportDetail.model_validate(report)


@router.get("/reports/{report_id}/document")
async def download_lab_report_document(
    report_id: UUID,
    session: AsyncSession = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage),
    _: User = Depends(require_permission("laboratory.read")),
) -> StreamingResponse:
    found = await report_service.get_report_document(session, storage, report_id)
    if found is None:
        raise NotFoundError("Lab report not found.")
    report, data = found

    def _iter():
        yield data

    return StreamingResponse(
        _iter(),
        media_type=report.content_type,
        headers={"Content-Disposition": f'inline; filename="{report.original_filename}"'},
    )


@router.post("/reports/{report_id}/extraction", response_model=LabReportDetail)
async def run_lab_report_extraction(
    report_id: UUID,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    storage: ObjectStorage = Depends(get_object_storage),
    _: User = Depends(require_permission("laboratory.upload")),
) -> LabReportDetail:
    report = await report_service.run_extraction(session, storage, settings, report_id)
    return LabReportDetail.model_validate(report)


@router.post(
    "/reports/{report_id}/results", response_model=LabReportResultRead, status_code=201
)
async def add_lab_report_result(
    report_id: UUID,
    payload: LabReportResultManualCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("laboratory.correct")),
) -> LabReportResultRead:
    result = await report_service.add_manual_result(session, report_id, payload)
    return LabReportResultRead.model_validate(result)


@router.patch("/reports/results/{result_id}", response_model=LabReportResultRead)
async def correct_lab_report_result(
    result_id: UUID,
    payload: LabReportResultCorrectionRequest,
    session: AsyncSession = Depends(get_db),
    current: User = Depends(require_permission("laboratory.correct")),
) -> LabReportResultRead:
    result = await report_service.correct_result(
        session, result_id, payload, corrected_by_id=current.id
    )
    return LabReportResultRead.model_validate(result)


@router.get(
    "/reports/results/{result_id}/corrections",
    response_model=list[LabReportResultCorrectionRead],
)
async def list_lab_report_result_corrections(
    result_id: UUID,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("laboratory.read")),
) -> list[LabReportResultCorrectionRead]:
    corrections = await report_service.list_corrections(session, result_id)
    return [LabReportResultCorrectionRead.model_validate(c) for c in corrections]
