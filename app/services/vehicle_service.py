from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException
from app.crud.command.vehicle_command import (
    add_vehicle_document,
    add_vehicle_image,
    add_vehicle_status_log,
    create_vehicle,
    deactivate_vehicle_with_log,
    update_vehicle,
)
from app.crud.query.vehicle_position_query import get_latest_position_for_vehicle
from app.crud.query.vehicle_query import (
    clear_primary_flags_for_vehicle_images,
    get_vehicle_by_id,
    get_vehicle_by_plate_number,
    list_vehicles_by_user_id,
    search_vehicles_by_plate_query,
)
from app.integrations.outbound import (
    analytics_vehicle_summary,
    fetch_vehicle_tracking,
    proxy_media_upload,
    ticket_approve,
    ticket_create,
    validate_user_exists,
)
from app.models.enums import FuelTypeEnum, VehicleDocEnum, VehicleStatusEnum
from app.models.vehicle_document_model import VehicleDocument
from app.models.vehicle_position_model import VehiclePosition
from app.models.vehicle_image_model import VehicleImage
from app.models.vehicle_model import Vehicle
from app.models.vehicle_status_log_model import VehicleStatusLog
from app.schemas.vehicle_schema import (
    MessageResponse,
    TicketApproveRequest,
    TicketCreateResponse,
    TrackingPositionResponse,
    TrackingRecordRequest,
    VehicleCreateRequest,
    VehicleCreateResponse,
    VehicleDeactivateRequest,
    VehicleDetailsRequest,
    VehicleDetailsResponse,
    VehicleDocumentCreate,
    VehicleDocumentRead,
    VehicleImageCreate,
    VehicleImageRead,
    VehicleListItem,
    VehicleListRequest,
    VehicleStatusLogCreate,
    VehicleStatusLogRead,
    VehicleUpdateRequest,
    VehicleUploadDocumentJsonRequest,
    VehicleUploadDocumentResponse,
    VehicleUploadImageResponse,
)
def _to_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError) as e:
        raise AppException("Invalid data", status_code=400) from e


def _enum_str(v: object) -> str:
    if isinstance(v, (FuelTypeEnum, VehicleStatusEnum, VehicleDocEnum)):
        return v.value
    return str(v)


def _vehicle_to_details(vehicle: Vehicle) -> VehicleDetailsResponse:
    return VehicleDetailsResponse(
        vehicle_id=str(vehicle.vehicle_id),
        user_id=str(vehicle.user_id),
        model_name=vehicle.model_name,
        brand=vehicle.brand,
        year=vehicle.year,
        fuel_type=_enum_str(vehicle.fuel_type),
        plate_number=vehicle.plate_number,
        vin_number=vehicle.vin_number,
        color=vehicle.color,
        status=_enum_str(vehicle.status),
        is_primary=bool(vehicle.is_primary),
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )


def create_vehicle_api(db: Session, payload: VehicleCreateRequest) -> VehicleCreateResponse:
    _to_uuid(payload.user_id)
    validate_user_exists(payload.user_id)
    existing = get_vehicle_by_plate_number(db=db, plate_number=payload.plate_number)
    if existing is not None:
        raise AppException("Invalid data", status_code=400)

    fuel = FuelTypeEnum.PETROL
    if payload.fuel_type is not None:
        try:
            fuel = FuelTypeEnum(payload.fuel_type)
        except ValueError as e:
            raise AppException("Invalid data", status_code=400) from e

    vehicle = Vehicle(
        user_id=_to_uuid(payload.user_id),
        model_name=payload.model_name,
        brand=(payload.brand or "Unknown"),
        year=payload.year,
        fuel_type=fuel,
        plate_number=payload.plate_number,
        vin_number=payload.vin_number,
        color=payload.color,
        status=VehicleStatusEnum.ACTIVE,
        is_primary=False,
    )
    created = create_vehicle(db=db, vehicle=vehicle)
    return VehicleCreateResponse(vehicle_id=str(created.vehicle_id), message="Vehicle created")


def list_vehicles_api(db: Session, payload: VehicleListRequest) -> list[VehicleListItem]:
    _to_uuid(payload.user_id)
    validate_user_exists(payload.user_id)
    rows = list_vehicles_by_user_id(db=db, user_id=payload.user_id)
    out: list[VehicleListItem] = []
    for v in rows:
        img = None
        try:
            # Pick primary image when available (may be None in older data).
            if getattr(v, "images", None):
                prim = next((i for i in v.images if getattr(i, "is_primary", False)), None)
                if prim is None and len(v.images) > 0:
                    prim = v.images[0]
                img = getattr(prim, "image_url", None) if prim else None
        except Exception:
            img = None
        out.append(
            VehicleListItem(
                vehicle_id=str(v.vehicle_id),
                model_name=v.model_name,
                plate_number=getattr(v, "plate_number", None),
                vin_number=getattr(v, "vin_number", None),
                brand=getattr(v, "brand", None),
                year=getattr(v, "year", None),
                color=getattr(v, "color", None),
                image_url=img,
            )
        )
    return out


def search_vehicles_api(db: Session, query: str) -> dict[str, list[dict[str, Any]]]:
    q = (query or "").strip()
    if len(q) < 2:
        return {"vehicles": []}
    rows = search_vehicles_by_plate_query(db=db, query=q, limit=20)
    return {
        "vehicles": [
            {
                "vehicle_id": str(v.vehicle_id),
                "user_id": str(v.user_id),
                "model_name": v.model_name,
                "plate_number": v.plate_number,
                "vin_number": v.vin_number,
                "color": v.color,
                "status": _enum_str(v.status),
            }
            for v in rows
        ]
    }


def vehicle_details_api(db: Session, payload: VehicleDetailsRequest) -> VehicleDetailsResponse:
    vehicle = get_vehicle_by_id(db=db, vehicle_id=payload.vehicle_id)
    if vehicle is None:
        raise AppException("Vehicle not found", status_code=404)
    return _vehicle_to_details(vehicle)


def update_vehicle_api(db: Session, payload: VehicleUpdateRequest) -> MessageResponse:
    vehicle = get_vehicle_by_id(db=db, vehicle_id=payload.vehicle_id)
    if vehicle is None:
        raise AppException("Invalid", status_code=400)

    if payload.plate_number is not None and payload.plate_number != vehicle.plate_number:
        taken = get_vehicle_by_plate_number(db=db, plate_number=payload.plate_number)
        if taken is not None:
            raise AppException("Invalid", status_code=400)
        vehicle.plate_number = payload.plate_number

    prev_status = vehicle.status
    if payload.model_name is not None:
        vehicle.model_name = payload.model_name
    if payload.brand is not None:
        vehicle.brand = payload.brand
    if payload.year is not None:
        vehicle.year = payload.year
    if payload.fuel_type is not None:
        try:
            vehicle.fuel_type = FuelTypeEnum(payload.fuel_type)
        except ValueError as e:
            raise AppException("Invalid", status_code=400) from e
    if payload.vin_number is not None:
        vehicle.vin_number = payload.vin_number
    if payload.color is not None:
        vehicle.color = payload.color
    if payload.status is not None:
        try:
            vehicle.status = VehicleStatusEnum(payload.status)
        except ValueError as e:
            raise AppException("Invalid", status_code=400) from e
    if payload.is_primary is not None:
        vehicle.is_primary = payload.is_primary

    update_vehicle(db=db, vehicle=vehicle)

    if payload.status is not None and vehicle.status != prev_status:
        log = VehicleStatusLog(
            vehicle_id=vehicle.vehicle_id,
            status=vehicle.status,
            changed_by=vehicle.user_id,
        )
        add_vehicle_status_log(db=db, log=log)

    return MessageResponse(message="Updated")


def deactivate_vehicle_api(db: Session, payload: VehicleDeactivateRequest) -> MessageResponse:
    vehicle = get_vehicle_by_id(db=db, vehicle_id=payload.vehicle_id)
    if vehicle is None:
        raise AppException("Not found", status_code=404)
    deactivate_vehicle_with_log(db=db, vehicle=vehicle, changed_by=vehicle.user_id)
    return MessageResponse(message="Deactivated")


def _assert_upload_size(num_bytes: int) -> None:
    max_b = settings.UPLOAD_MAX_MB * 1024 * 1024
    if num_bytes > max_b:
        raise AppException("Invalid file", status_code=400)


def upload_vehicle_image_api(
    db: Session,
    vehicle_id: str,
    file_bytes: bytes,
    filename: str,
    content_type: str | None,
    is_primary: bool,
) -> VehicleUploadImageResponse:
    _assert_upload_size(len(file_bytes))
    vehicle = get_vehicle_by_id(db=db, vehicle_id=vehicle_id)
    if vehicle is None:
        raise AppException("Invalid file", status_code=400)

    image_url = proxy_media_upload(file_bytes, filename, content_type)
    vid = vehicle.vehicle_id
    if is_primary:
        clear_primary_flags_for_vehicle_images(db=db, vehicle_id=vid)
    image = VehicleImage(vehicle_id=vid, image_url=image_url, is_primary=is_primary)
    add_vehicle_image(db=db, image=image)
    return VehicleUploadImageResponse(image_url=image_url)


def upload_vehicle_document_api(
    db: Session,
    vehicle_id: str,
    doc_type: str,
    doc_url: str,
    expiry_date: object = None,
) -> VehicleUploadDocumentResponse:
    vehicle = get_vehicle_by_id(db=db, vehicle_id=vehicle_id)
    if vehicle is None:
        raise AppException("Invalid", status_code=400)
    try:
        dt = VehicleDocEnum(doc_type)
    except ValueError as e:
        raise AppException("Invalid", status_code=400) from e
    doc = VehicleDocument(vehicle_id=vehicle.vehicle_id, doc_type=dt, doc_url=doc_url, expiry_date=expiry_date)
    created = add_vehicle_document(db=db, document=doc)
    return VehicleUploadDocumentResponse(doc_id=str(created.doc_id))


def upload_vehicle_document_from_json(db: Session, payload: VehicleUploadDocumentJsonRequest) -> VehicleUploadDocumentResponse:
    return upload_vehicle_document_api(
        db=db,
        vehicle_id=payload.vehicle_id,
        doc_type=payload.doc_type,
        doc_url=payload.doc_url,
        expiry_date=payload.expiry_date,
    )


def _validate_coordinates(lat: float, lng: float) -> None:
    if lat < -90 or lat > 90 or lng < -180 or lng > 180:
        raise AppException("Invalid coordinates", status_code=400)


def record_tracking_api(db: Session, vehicle_id: str, payload: TrackingRecordRequest) -> MessageResponse:
    vehicle = get_vehicle_by_id(db=db, vehicle_id=vehicle_id)
    if vehicle is None:
        raise AppException("Vehicle not found", status_code=404)
    _validate_coordinates(payload.lat, payload.lng)
    pos_kwargs: dict = {
        "vehicle_id": vehicle.vehicle_id,
        "latitude": payload.lat,
        "longitude": payload.lng,
        "speed_kmh": payload.speed_kmh,
        "heading_degrees": payload.heading_degrees,
        "source": payload.source,
    }
    if payload.recorded_at is not None:
        pos_kwargs["recorded_at"] = payload.recorded_at
    pos = VehiclePosition(**pos_kwargs)
    create_vehicle_position(db=db, position=pos)
    return MessageResponse(message="Recorded")


def get_tracking_api(db: Session, vehicle_id: str) -> TrackingPositionResponse:
    if get_vehicle_by_id(db=db, vehicle_id=vehicle_id) is None:
        raise AppException("Vehicle not found", status_code=404)
    latest = get_latest_position_for_vehicle(db=db, vehicle_id=vehicle_id)
    if latest is not None:
        return TrackingPositionResponse(
            lat=float(latest.latitude),
            lng=float(latest.longitude),
            recorded_at=latest.recorded_at,
        )
    if settings.TRACKING_MS_BASE_URL.strip():
        data = fetch_vehicle_tracking(vehicle_id)
        return TrackingPositionResponse(
            lat=float(data.get("lat", 0)),
            lng=float(data.get("lng", 0)),
            recorded_at=None,
        )
    raise AppException("No tracking data", status_code=404)


def create_ticket_api(db: Session, vehicle_id: str) -> TicketCreateResponse:
    if get_vehicle_by_id(db=db, vehicle_id=vehicle_id) is None:
        raise AppException("Failed", status_code=400)
    data = ticket_create(vehicle_id)
    tid = data.get("ticket_id")
    if not tid:
        raise AppException("Failed", status_code=400)
    return TicketCreateResponse(ticket_id=str(tid))


def approve_ticket_api(payload: TicketApproveRequest) -> MessageResponse:
    ticket_approve(payload.ticket_id, payload.status)
    return MessageResponse(message="Updated")


def vehicle_analytics_summary(db: Session, vehicle_id: str) -> dict[str, Any]:
    if get_vehicle_by_id(db=db, vehicle_id=vehicle_id) is None:
        raise AppException("Failed", status_code=404)
    return analytics_vehicle_summary(vehicle_id)


# --- Legacy helpers (internal / backward use) ---


def _image_to_read(image: VehicleImage) -> VehicleImageRead:
    return VehicleImageRead.model_validate(image, from_attributes=True)


def _document_to_read(document: VehicleDocument) -> VehicleDocumentRead:
    return VehicleDocumentRead.model_validate(document, from_attributes=True)


def _status_log_to_read(log: VehicleStatusLog) -> VehicleStatusLogRead:
    return VehicleStatusLogRead.model_validate(log, from_attributes=True)


def add_vehicle_image_service(
    db: Session,
    vehicle_id: str,
    payload: VehicleImageCreate,
) -> VehicleImageRead:
    vehicle = get_vehicle_by_id(db=db, vehicle_id=vehicle_id)
    if vehicle is None:
        raise AppException("vehicle not found", status_code=404)

    image = VehicleImage(
        vehicle_id=_to_uuid(vehicle_id),
        image_url=payload.image_url,
        is_primary=payload.is_primary,
    )
    created = add_vehicle_image(db=db, image=image)
    return _image_to_read(created)


def add_vehicle_document_service(
    db: Session,
    vehicle_id: str,
    payload: VehicleDocumentCreate,
) -> VehicleDocumentRead:
    vehicle = get_vehicle_by_id(db=db, vehicle_id=vehicle_id)
    if vehicle is None:
        raise AppException("vehicle not found", status_code=404)

    document = VehicleDocument(
        vehicle_id=_to_uuid(vehicle_id),
        doc_type=VehicleDocEnum(payload.doc_type),
        doc_url=payload.doc_url,
        expiry_date=payload.expiry_date,
    )
    created = add_vehicle_document(db=db, document=document)
    return _document_to_read(created)


def add_vehicle_status_log_service(
    db: Session,
    vehicle_id: str,
    payload: VehicleStatusLogCreate,
) -> VehicleStatusLogRead:
    vehicle = get_vehicle_by_id(db=db, vehicle_id=vehicle_id)
    if vehicle is None:
        raise AppException("vehicle not found", status_code=404)

    status = VehicleStatusEnum(payload.status)
    changed_by = _to_uuid(payload.changed_by)

    vehicle.status = status
    update_vehicle(db=db, vehicle=vehicle)

    log = VehicleStatusLog(vehicle_id=_to_uuid(vehicle_id), status=status, changed_by=changed_by)
    created_log = add_vehicle_status_log(db=db, log=log)
    return _status_log_to_read(created_log)
