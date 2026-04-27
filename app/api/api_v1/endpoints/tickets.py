from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database.dependency import get_db
from app.schemas.vehicle_schema import MessageResponse, TicketApproveRequest, TicketCreateRequest, TicketCreateResponse
from app.services import vehicle_service

router = APIRouter()


@router.post(
    "/create",
    response_model=TicketCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(payload: TicketCreateRequest, db: Session = Depends(get_db)) -> TicketCreateResponse:
    return vehicle_service.create_ticket_api(db=db, vehicle_id=payload.vehicle_id)


@router.post("/approve", response_model=MessageResponse)
def approve_ticket(payload: TicketApproveRequest) -> MessageResponse:
    return vehicle_service.approve_ticket_api(payload=payload)
