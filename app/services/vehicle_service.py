import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.crud.command.vehicle_command import (
    add_vehicle_document,
    add_vehicle_image,
    add_vehicle_status_log,
    create_vehicle,
)
from app.crud.query.vehicle_query import get_vehicle_by_id, get_vehicle_by_plate_number
from app.models.enums import FuelTypeEnum, VehicleDocEnum, VehicleStatusEnum
from app.models.vehicle_document_model import VehicleDocument
from app.models.vehicle_image_model import VehicleImage
from app.models.vehicle_model import Vehicle
from app.models.vehicle_status_log_model import VehicleStatusLog
from app.schemas.vehicle_schema import (
    VehicleCreate,
    VehicleDocumentCreate,
    VehicleImageCreate,
    VehicleRead,
    VehicleStatusLogCreate,
    VehicleImageRead,
    VehicleDocumentRead,
    VehicleStatusLogRead,
)


def _to_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(str(value))


def _vehicle_to_read(vehicle: Vehicle) -> VehicleRead:
    return VehicleRead.model_validate(vehicle, from_attributes=True)


def _image_to_read(image: VehicleImage) -> VehicleImageRead:
    return VehicleImageRead.model_validate(image, from_attributes=True)


def _document_to_read(document: VehicleDocument) -> VehicleDocumentRead:
    return VehicleDocumentRead.model_validate(document, from_attributes=True)


def _status_log_to_read(log: VehicleStatusLog) -> VehicleStatusLogRead:
    return VehicleStatusLogRead.model_validate(log, from_attributes=True)


def create_vehicle_service(db: Session, payload: VehicleCreate) -> VehicleRead:
    existing = get_vehicle_by_plate_number(db=db, plate_number=payload.plate_number)
    if existing is not None:
        raise ValueError("plate_number already exists")

    vehicle = Vehicle(
        user_id=_to_uuid(payload.user_id),
        model_name=payload.model_name,
        brand=payload.brand,
        year=payload.year,
        fuel_type=FuelTypeEnum(payload.fuel_type),
        plate_number=payload.plate_number,
        vin_number=payload.vin_number,
        color=payload.color,
        status=VehicleStatusEnum(payload.status),
        is_primary=payload.is_primary,
    )
    created = create_vehicle(db=db, vehicle=vehicle)
    return _vehicle_to_read(created)


def get_vehicle_service(db: Session, vehicle_id: str) -> VehicleRead:
    vehicle = get_vehicle_by_id(db=db, vehicle_id=vehicle_id)
    if vehicle is None:
        raise ValueError("vehicle not found")
    return _vehicle_to_read(vehicle)


def add_vehicle_image_service(
    db: Session,
    vehicle_id: str,
    payload: VehicleImageCreate,
) -> VehicleImageRead:
    vehicle = get_vehicle_by_id(db=db, vehicle_id=vehicle_id)
    if vehicle is None:
        raise ValueError("vehicle not found")

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
        raise ValueError("vehicle not found")

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
        raise ValueError("vehicle not found")

    status = VehicleStatusEnum(payload.status)
    changed_by = _to_uuid(payload.changed_by)

    # Update current status.
    vehicle.status = status
    db.commit()
    db.refresh(vehicle)

    # Append status log.
    log = VehicleStatusLog(vehicle_id=_to_uuid(vehicle_id), status=status, changed_by=changed_by)
    created_log = add_vehicle_status_log(db=db, log=log)
    return _status_log_to_read(created_log)

