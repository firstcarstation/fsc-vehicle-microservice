from sqlalchemy.orm import Session

from app.models.vehicle_position_model import VehiclePosition


def create_vehicle_position(db: Session, position: VehiclePosition) -> VehiclePosition:
    db.add(position)
    db.commit()
    db.refresh(position)
    return position
