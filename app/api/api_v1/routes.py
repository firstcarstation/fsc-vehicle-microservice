from fastapi import APIRouter
from app.api.api_v1.endpoints import vehicles

api_router = APIRouter()
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])
