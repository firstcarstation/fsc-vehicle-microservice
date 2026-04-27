import uuid

from sqlalchemy import Column, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database.base import Base


class VehiclePosition(Base):
    """GPS (or telemetry) samples for a vehicle; supports history and latest lookup."""

    __tablename__ = "vehicle_positions"

    position_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        nullable=False,
    )

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    speed_kmh = Column(Float, nullable=True)
    heading_degrees = Column(Float, nullable=True)
    source = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    vehicle = relationship("Vehicle", back_populates="positions")

    __table_args__ = (
        Index("idx_vehicle_positions_vehicle_recorded", "vehicle_id", "recorded_at"),
    )
