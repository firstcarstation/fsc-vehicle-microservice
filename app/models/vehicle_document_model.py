import uuid

from sqlalchemy import Column, Date, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database.base import Base
from app.models.enums import VehicleDocEnum


class VehicleDocument(Base):
    __tablename__ = "vehicle_documents"

    doc_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        nullable=False,
    )

    doc_type = Column(
        SAEnum(
            VehicleDocEnum,
            name="vehicle_doc_enum",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    doc_url = Column(String, nullable=False)
    expiry_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    vehicle = relationship("Vehicle", back_populates="documents")

