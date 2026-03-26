from typing import Optional

from sqlalchemy.orm import Session

from app.models.vehicle_model import Vehicle


def get_vehicle_by_id(db: Session, vehicle_id: str) -> Optional[Vehicle]:
    return db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()


def get_vehicle_by_plate_number(db: Session, plate_number: str) -> Optional[Vehicle]:
    return db.query(Vehicle).filter(Vehicle.plate_number == plate_number).first()

