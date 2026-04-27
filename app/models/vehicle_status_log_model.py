import uuid

from sqlalchemy import Column, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database.base import Base
from app.models.enums import VehicleStatusEnum


class VehicleStatusLog(Base):
    __tablename__ = "vehicle_status_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        nullable=False,
    )

    status = Column(
        SAEnum(
            VehicleStatusEnum,
            name="vehicle_status_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )

    # External reference to the User MS.
    changed_by = Column(UUID(as_uuid=True), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    vehicle = relationship("Vehicle", back_populates="status_logs")

