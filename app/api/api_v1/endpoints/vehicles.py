from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database.dependency import get_db
from app.schemas.vehicle_schema import (
    VehicleCreate,
    VehicleDocumentCreate,
    VehicleImageCreate,
    VehicleRead,
    VehicleDocumentRead,
    VehicleImageRead,
    VehicleStatusLogCreate,
    VehicleStatusLogRead,
)
from app.services.vehicle_service import (
    add_vehicle_document_service,
    add_vehicle_image_service,
    add_vehicle_status_log_service,
    create_vehicle_service,
    get_vehicle_service,
)

router = APIRouter()


@router.post("", response_model=VehicleRead)
def create_vehicle(payload: VehicleCreate, db: Session = Depends(get_db)) -> VehicleRead:
    try:
        return create_vehicle_service(db=db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{vehicle_id}", response_model=VehicleRead)
def read_vehicle(vehicle_id: str, db: Session = Depends(get_db)) -> VehicleRead:
    try:
        return get_vehicle_service(db=db, vehicle_id=vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{vehicle_id}/images", response_model=VehicleImageRead)
def add_vehicle_image(
    vehicle_id: str,
    payload: VehicleImageCreate,
    db: Session = Depends(get_db),
) -> VehicleImageRead:
    try:
        return add_vehicle_image_service(db=db, vehicle_id=vehicle_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{vehicle_id}/documents", response_model=VehicleDocumentRead)
def add_vehicle_document(
    vehicle_id: str,
    payload: VehicleDocumentCreate,
    db: Session = Depends(get_db),
) -> VehicleDocumentRead:
    try:
        return add_vehicle_document_service(db=db, vehicle_id=vehicle_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{vehicle_id}/status", response_model=VehicleStatusLogRead)
def add_vehicle_status_log(
    vehicle_id: str,
    payload: VehicleStatusLogCreate,
    db: Session = Depends(get_db),
) -> VehicleStatusLogRead:
    try:
        return add_vehicle_status_log_service(db=db, vehicle_id=vehicle_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

