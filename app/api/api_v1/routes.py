from fastapi import APIRouter

from app.api.api_v1.endpoints import analytics, media, tickets, vehicles

api_router = APIRouter()
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
