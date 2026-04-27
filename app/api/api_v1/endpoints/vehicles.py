from datetime import date

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.internal_deps import require_internal_api_key
from app.core.database.dependency import get_db
from app.core.exceptions import AppException
from app.integrations.outbound import proxy_media_upload
from app.schemas.vehicle_schema import (
    MessageResponse,
    TrackingPositionResponse,
    TrackingRecordRequest,
    VehicleCreateRequest,
    VehicleCreateResponse,
    VehicleDeactivateRequest,
    VehicleDetailsRequest,
    VehicleDetailsResponse,
    VehicleListItem,
    VehicleListRequest,
    VehicleUpdateRequest,
    VehicleUploadDocumentResponse,
    VehicleUploadImageResponse,
)
from app.services import vehicle_service

router = APIRouter()


@router.post("/internal/details", response_model=VehicleDetailsResponse)
def internal_vehicle_details(
    payload: VehicleDetailsRequest,
    db: Session = Depends(get_db),
    _ok: bool = Depends(require_internal_api_key),
) -> VehicleDetailsResponse:
    del _ok
    return vehicle_service.vehicle_details_api(db=db, payload=payload)


@router.post(
    "/create",
    response_model=VehicleCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vehicle(payload: VehicleCreateRequest, db: Session = Depends(get_db)) -> VehicleCreateResponse:
    return vehicle_service.create_vehicle_api(db=db, payload=payload)


@router.post("/list", response_model=list[VehicleListItem])
def list_vehicles(payload: VehicleListRequest, db: Session = Depends(get_db)) -> list[VehicleListItem]:
    return vehicle_service.list_vehicles_api(db=db, payload=payload)


@router.post("/search")
def search_vehicles(payload: dict, db: Session = Depends(get_db)) -> dict:
    """Admin/customer lookup helper.

    Input:
      - query: matches plate number (contains, case-insensitive)

    Output:
      - vehicles: list of minimal vehicle rows (includes user_id for ticket creation).
    """
    return vehicle_service.search_vehicles_api(db=db, query=str(payload.get("query") or ""))


@router.post("/details", response_model=VehicleDetailsResponse)
def vehicle_details(payload: VehicleDetailsRequest, db: Session = Depends(get_db)) -> VehicleDetailsResponse:
    return vehicle_service.vehicle_details_api(db=db, payload=payload)


@router.put("/update", response_model=MessageResponse)
def update_vehicle(payload: VehicleUpdateRequest, db: Session = Depends(get_db)) -> MessageResponse:
    return vehicle_service.update_vehicle_api(db=db, payload=payload)


@router.post("/deactivate", response_model=MessageResponse)
def deactivate_vehicle(payload: VehicleDeactivateRequest, db: Session = Depends(get_db)) -> MessageResponse:
    return vehicle_service.deactivate_vehicle_api(db=db, payload=payload)


@router.post("/upload-image", response_model=VehicleUploadImageResponse)
def upload_vehicle_image(
    db: Session = Depends(get_db),
    vehicle_id: str = Form(...),
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
) -> VehicleUploadImageResponse:
    raw = file.file.read()
    return vehicle_service.upload_vehicle_image_api(
        db=db,
        vehicle_id=vehicle_id,
        file_bytes=raw,
        filename=file.filename or "upload",
        content_type=file.content_type,
        is_primary=is_primary,
    )


@router.post("/upload-document", response_model=VehicleUploadDocumentResponse)
def upload_vehicle_document(
    db: Session = Depends(get_db),
    vehicle_id: str = Form(...),
    doc_type: str = Form(...),
    doc_url: str | None = Form(None),
    expiry_date: date | None = Form(None),
    file: UploadFile | None = File(None),
) -> VehicleUploadDocumentResponse:
    if file is not None:
        raw = file.file.read()
        resolved = proxy_media_upload(raw, file.filename or "document", file.content_type)
        return vehicle_service.upload_vehicle_document_api(
            db=db,
            vehicle_id=vehicle_id,
            doc_type=doc_type,
            doc_url=resolved,
            expiry_date=expiry_date,
        )
    if doc_url:
        return vehicle_service.upload_vehicle_document_api(
            db=db,
            vehicle_id=vehicle_id,
            doc_type=doc_type,
            doc_url=doc_url,
            expiry_date=expiry_date,
        )
    raise AppException("Invalid", status_code=400)


@router.get("/{vehicle_id}/tracking", response_model=TrackingPositionResponse)
def vehicle_tracking(vehicle_id: str, db: Session = Depends(get_db)) -> TrackingPositionResponse:
    return vehicle_service.get_tracking_api(db=db, vehicle_id=vehicle_id)


@router.post("/{vehicle_id}/tracking", response_model=MessageResponse)
def record_vehicle_tracking(
    vehicle_id: str,
    payload: TrackingRecordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Store a position sample; GET `/{vehicle_id}/tracking` returns the latest local row."""
    return vehicle_service.record_tracking_api(db=db, vehicle_id=vehicle_id, payload=payload)
