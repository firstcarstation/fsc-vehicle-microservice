import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.vehicle_position_model import VehiclePosition


def _parse_uuid(vehicle_id: str) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(str(vehicle_id))
    except (ValueError, TypeError):
        return None


def get_latest_position_for_vehicle(db: Session, vehicle_id: str) -> Optional[VehiclePosition]:
    vid = _parse_uuid(vehicle_id)
    if vid is None:
        return None
    return (
        db.query(VehiclePosition)
        .filter(VehiclePosition.vehicle_id == vid)
        .order_by(VehiclePosition.recorded_at.desc())
        .first()
    )
