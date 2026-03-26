from sqlalchemy.orm import Session

from app.models.vehicle_document_model import VehicleDocument
from app.models.vehicle_image_model import VehicleImage
from app.models.vehicle_model import Vehicle
from app.models.vehicle_status_log_model import VehicleStatusLog


def create_vehicle(db: Session, vehicle: Vehicle) -> Vehicle:
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def add_vehicle_image(db: Session, image: VehicleImage) -> VehicleImage:
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def add_vehicle_document(db: Session, document: VehicleDocument) -> VehicleDocument:
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def add_vehicle_status_log(db: Session, log: VehicleStatusLog) -> VehicleStatusLog:
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

