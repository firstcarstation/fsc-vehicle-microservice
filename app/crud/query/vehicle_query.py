import uuid
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.vehicle_image_model import VehicleImage
from app.models.vehicle_model import Vehicle


def _parse_uuid(vehicle_id: str) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(str(vehicle_id))
    except (ValueError, TypeError):
        return None


def get_vehicle_by_id(db: Session, vehicle_id: str) -> Optional[Vehicle]:
    vid = _parse_uuid(vehicle_id)
    if vid is None:
        return None
    return db.query(Vehicle).filter(Vehicle.vehicle_id == vid).first()


def get_vehicle_by_plate_number(db: Session, plate_number: str) -> Optional[Vehicle]:
    return db.query(Vehicle).filter(Vehicle.plate_number == plate_number).first()


def list_vehicles_by_user_id(db: Session, user_id: str) -> list[Vehicle]:
    uid = _parse_uuid(user_id)
    if uid is None:
        return []
    return db.query(Vehicle).filter(Vehicle.user_id == uid).order_by(Vehicle.created_at.desc()).all()


def search_vehicles_by_plate_query(db: Session, query: str, *, limit: int = 20) -> list[Vehicle]:
    q = (query or "").strip()
    if not q:
        return []
    like = f"%{q.lower()}%"
    return (
        db.query(Vehicle)
        .filter(func.lower(Vehicle.plate_number).like(like))
        .order_by(Vehicle.created_at.desc())
        .limit(min(max(int(limit), 1), 50))
        .all()
    )


def clear_primary_flags_for_vehicle_images(db: Session, vehicle_id: uuid.UUID) -> None:
    db.query(VehicleImage).filter(
        VehicleImage.vehicle_id == vehicle_id,
        VehicleImage.is_primary.is_(True),
    ).update({"is_primary": False})
    db.flush()

