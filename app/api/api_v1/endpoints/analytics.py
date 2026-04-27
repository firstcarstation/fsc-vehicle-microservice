from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database.dependency import get_db
from app.services import vehicle_service

router = APIRouter()


@router.get("/vehicle-summary")
def vehicle_summary(
    vehicle_id: str = Query(..., description="Vehicle UUID"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return vehicle_service.vehicle_analytics_summary(db=db, vehicle_id=vehicle_id)
