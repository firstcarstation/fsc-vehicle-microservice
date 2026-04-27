from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# --- API payloads (contract-aligned) ---


class VehicleCreateRequest(BaseModel):
    user_id: str
    model_name: str = Field(..., max_length=100)
    plate_number: str = Field(..., max_length=20)
    brand: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = None
    fuel_type: Optional[str] = None
    vin_number: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=50)


class VehicleCreateResponse(BaseModel):
    vehicle_id: str
    message: str = "Vehicle created"


class VehicleListRequest(BaseModel):
    user_id: str


class VehicleListItem(BaseModel):
    vehicle_id: str
    model_name: str
    plate_number: str | None = None
    vin_number: str | None = None
    brand: str | None = None
    year: Optional[int] = None
    color: Optional[str] = None
    image_url: Optional[str] = None


class VehicleDetailsRequest(BaseModel):
    vehicle_id: str


class VehicleDetailsResponse(BaseModel):
    vehicle_id: str
    user_id: str
    model_name: str
    brand: str
    year: Optional[int] = None
    fuel_type: str
    plate_number: str
    vin_number: Optional[str] = None
    color: Optional[str] = None
    status: str
    is_primary: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VehicleUpdateRequest(BaseModel):
    vehicle_id: str
    model_name: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = None
    fuel_type: Optional[str] = None
    plate_number: Optional[str] = Field(None, max_length=20)
    vin_number: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    is_primary: Optional[bool] = None


class MessageResponse(BaseModel):
    message: str


class VehicleDeactivateRequest(BaseModel):
    vehicle_id: str


class VehicleUploadImageResponse(BaseModel):
    image_url: str


class VehicleUploadDocumentJsonRequest(BaseModel):
    """When the client already has a URL (e.g. from /api/v1/media/upload)."""

    vehicle_id: str
    doc_type: str
    doc_url: str
    expiry_date: Optional[date] = None


class VehicleUploadDocumentResponse(BaseModel):
    doc_id: str


# --- Legacy / internal (status changes with explicit actor) ---


class VehicleImageCreate(BaseModel):
    image_url: str
    is_primary: bool = False


class VehicleImageRead(BaseModel):
    image_id: str
    vehicle_id: str
    image_url: str
    is_primary: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VehicleDocumentCreate(BaseModel):
    doc_type: str
    doc_url: str
    expiry_date: Optional[date] = None


class VehicleDocumentRead(BaseModel):
    doc_id: str
    vehicle_id: str
    doc_type: str
    doc_url: str
    expiry_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VehicleStatusLogCreate(BaseModel):
    status: str
    changed_by: str


class VehicleStatusLogRead(BaseModel):
    log_id: str
    vehicle_id: str
    status: str
    changed_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- Integration proxies ---


class TicketCreateRequest(BaseModel):
    vehicle_id: str


class TicketCreateResponse(BaseModel):
    ticket_id: str


class TicketApproveRequest(BaseModel):
    ticket_id: str
    status: str


class TrackingPositionResponse(BaseModel):
    lat: float
    lng: float
    recorded_at: Optional[datetime] = None


class TrackingRecordRequest(BaseModel):
    """Ingest a GPS/telemetry point for a vehicle (this service stores tracking)."""

    lat: float
    lng: float
    recorded_at: Optional[datetime] = None
    speed_kmh: Optional[float] = None
    heading_degrees: Optional[float] = None
    source: Optional[str] = Field(None, max_length=50)


class MediaUploadResponse(BaseModel):
    url: str
