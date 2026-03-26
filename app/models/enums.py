from enum import Enum as PyEnum


class FuelTypeEnum(str, PyEnum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"


class VehicleStatusEnum(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    IN_SERVICE = "in_service"
    DELIVERED = "delivered"


class VehicleDocEnum(str, PyEnum):
    RC = "rc"
    INSURANCE = "insurance"
    POLLUTION = "pollution"
    OTHER = "other"
