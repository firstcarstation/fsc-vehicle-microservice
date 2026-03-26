import uuid

from sqlalchemy import Boolean, Column, Enum as SAEnum, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database.base import Base
from app.models.enums import FuelTypeEnum, VehicleStatusEnum


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # External reference to the User MS.
    user_id = Column(UUID(as_uuid=True), nullable=False)

    model_name = Column(String(100), nullable=False)
    brand = Column(String(100), nullable=False)
    year = Column(Integer, nullable=True)

    fuel_type = Column(SAEnum(FuelTypeEnum, name="fuel_type_enum"), nullable=False)

    plate_number = Column(String(20), unique=True, nullable=False)
    vin_number = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)

    status = Column(SAEnum(VehicleStatusEnum, name="vehicle_status_enum"), nullable=False)

    is_primary = Column(Boolean, nullable=False, default=False, server_default=text("false"))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    images = relationship(
        "VehicleImage",
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )
    documents = relationship(
        "VehicleDocument",
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )
    status_logs = relationship(
        "VehicleStatusLog",
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_vehicles_user_id", "user_id"),
        Index("idx_vehicles_plate_number", "plate_number"),
        Index("idx_vehicles_status", "status"),
    )

