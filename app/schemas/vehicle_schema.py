from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class VehicleBase(BaseModel):
    user_id: str
    model_name: str
    brand: str
    year: Optional[int] = None
    fuel_type: str
    plate_number: str
    vin_number: Optional[str] = None
    color: Optional[str] = None
    status: str
    is_primary: bool = False


class VehicleCreate(VehicleBase):
    pass


class VehicleRead(VehicleBase):
    vehicle_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True

