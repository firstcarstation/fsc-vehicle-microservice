import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database.base import Base


class VehicleImage(Base):
    __tablename__ = "vehicle_images"

    image_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        nullable=False,
    )

    image_url = Column(String, nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False, server_default=text("false"))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    vehicle = relationship("Vehicle", back_populates="images")

    __table_args__ = (Index("idx_vehicle_images_vehicle_id", "vehicle_id"),)

